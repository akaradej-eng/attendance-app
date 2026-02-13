import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime

# 1. เชื่อมต่อ Google Sheets
creds_dict = json.loads(st.secrets["google_sheet"]["credentials"])
gc = gspread.service_account_from_dict(creds_dict)
sh = gc.open("ระบบเช็คชื่อนักเรียน")
ws_students = sh.worksheet("Students")
ws_attendance = sh.worksheet("Attendance")

st.set_page_config(page_title="ระบบเช็คชื่อบ้านเชียง", layout="wide", page_icon="📱")

# CSS สำหรับปรับแต่งปุ่มและระยะห่างให้ดูทันสมัยและจิ้มง่าย
st.markdown("""
    <style>
    /* ปรับแต่งปุ่มให้สูงขึ้นและตัวหนา */
    div.stButton > button {
        height: 3.5em;
        font-weight: bold;
        border-radius: 8px;
    }
    /* สร้างการ์ดล้อมรอบรายชื่อนักเรียนแต่ละคน */
    .st-emotion-cache-12w0qpk { 
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏫 ระบบเช็คชื่อรายห้อง (Responsive)")

data = ws_students.get_all_records()

if len(data) > 0:
    df_students = pd.DataFrame(data)
    class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

    # ส่วนการตั้งค่า (จะยุบตัวอัตโนมัติเมื่อจอเล็ก)
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: selected_class = st.selectbox("📌 เลือกชั้นเรียน", class_list)
        with c2: teacher_name = st.text_input("👨‍🏫 ชื่อครูผู้บันทึก")
        with c3: check_date = st.date_input("📅 วันที่", datetime.today())

    st.write("")
    st.subheader(f"📋 รายชื่อนักเรียนห้อง {selected_class}")

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()

    if 'att_data' not in st.session_state:
        st.session_state.att_data = {}

    # วนลูปสร้างหน้าจอเช็คชื่อ
    for index, row in df_room.iterrows():
        sid = str(row['รหัสนักเรียน'])
        if sid not in st.session_state.att_data:
            st.session_state.att_data[sid] = "มาเรียน"

        # ใช้ container สร้างกรอบให้นักเรียนแต่ละคน
        with st.container(border=True):
            # แบ่งเป็น 2 ส่วนหลัก: (ชื่อ) และ (กลุ่มปุ่ม)
            # ในคอมพิวเตอร์จะเรียงซ้ายขวา ในมือถือจะตัดลงมาเป็นแถวใหม่ให้อัตโนมัติ
            name_col, btn_group = st.columns([1, 2])
            
            with name_col:
                st.markdown(f"**เลขที่ {row.get('เลขที่','-')}**<br> {row.get('ชื่อ','')}", unsafe_allow_html=True)
            
            with btn_group:
                # แบ่งพื้นที่ปุ่ม 4 ปุ่ม
                b1, b2, b3, b4 = st.columns(4)
                
                with b1:
                    if st.button(f"🟢 มา", key=f"ma_{sid}", use_container_width=True, 
                                 type="primary" if st.session_state.att_data[sid] == "มาเรียน" else "secondary"):
                        st.session_state.att_data[sid] = "มาเรียน"
                        st.rerun()
                with b2:
                    if st.button(f"🔴 ป่วย", key=f"puay_{sid}", use_container_width=True,
                                 type="primary" if st.session_state.att_data[sid] == "ป่วย" else "secondary"):
                        st.session_state.att_data[sid] = "ป่วย"
                        st.rerun()
                with b3:
                    if st.button(f"🟡 ลา", key=f"la_{sid}", use_container_width=True,
                                 type="primary" if st.session_state.att_data[sid] == "ลา" else "secondary"):
                        st.session_state.att_data[sid] = "ลา"
                        st.rerun()
                with b4:
                    if st.button(f"🟠 ขาด", key=f"khad_{sid}", use_container_width=True,
                                 type="primary" if st.session_state.att_data[sid] == "ขาด" else "secondary"):
                        st.session_state.att_data[sid] = "ขาด"
                        st.rerun()

    st.write("")
    if st.button("🚀 ยืนยันบันทึกข้อมูลทั้งหมดลง Google Sheets", type="primary", use_container_width=True):
        if not teacher_name.strip():
            st.error("⚠️ กรุณากรอกชื่อครูผู้บันทึกก่อนครับ")
        else:
            try:
                date_str = check_date.strftime("%d/%m/%Y")
                final_records = [[date_str, str(row['รหัสนักเรียน']), row.get('ชื่อ',''), 
                                 row.get('ชั้นเรียน',''), st.session_state.att_data[str(row['รหัสนักเรียน'])], 
                                 teacher_name] for _, row in df_room.iterrows()]
                
                ws_attendance.append_rows(final_records)
                st.success(f"✅ บันทึกข้อมูลเรียบร้อยแล้ว!")
                del st.session_state.att_data
                st.rerun()
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {e}")
else:
    st.info("กรุณาเพิ่มข้อมูลนักเรียนใน Tab 'Students'")
