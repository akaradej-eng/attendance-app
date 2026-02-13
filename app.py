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

# CSS ตกแต่งให้เหมาะกับมือถือ (ขยายปุ่มให้สูงขึ้นและตัวหนา)
st.markdown("""
    <style>
    div.stButton > button {
        height: 3em;
        font-size: 16px !important;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .student-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 ระบบเช็คชื่อ (ฉบับมือถือ)")

data = ws_students.get_all_records()

if len(data) > 0:
    df_students = pd.DataFrame(data)
    class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

    # ส่วนเลือกข้อมูล (บีบให้เหลือคอลัมน์เดียวในมือถืออัตโนมัติ)
    with st.expander("⚙️ ตั้งค่าการบันทึก", expanded=True):
        selected_class = st.selectbox("📌 เลือกชั้นเรียน", class_list)
        teacher_name = st.text_input("👨‍🏫 ชื่อครูผู้บันทึก")
        check_date = st.date_input("📅 วันที่", datetime.today())

    st.markdown(f"### 📋 รายชื่อชั้น {selected_class}")

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()

    if 'att_data' not in st.session_state:
        st.session_state.att_data = {}

    # วนลูปสร้างการ์ดรายชื่อนักเรียน
    for index, row in df_room.iterrows():
        sid = str(row['รหัสนักเรียน'])
        if sid not in st.session_state.att_data:
            st.session_state.att_data[sid] = "มาเรียน"

        # การ์ดนักเรียนแต่ละคน
        with st.container():
            st.markdown(f"""
                <div class='student-card'>
                    <b>เลขที่ {row.get('เลขที่','-')}</b> | {row.get('ชื่อ','')}
                </div>
            """, unsafe_allow_html=True)
            
            # แบ่งปุ่มเป็น 2 แถว แถวละ 2 ปุ่ม เพื่อให้ปุ่มใหญ่จิ้มง่ายในมือถือ
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button(f"🟢 มาเรียน", key=f"ma_{sid}", use_container_width=True, 
                             type="primary" if st.session_state.att_data[sid] == "มาเรียน" else "secondary"):
                    st.session_state.att_data[sid] = "มาเรียน"
                    st.rerun()
                
                if st.button(f"🟡 ลา", key=f"la_{sid}", use_container_width=True,
                             type="primary" if st.session_state.att_data[sid] == "ลา" else "secondary"):
                    st.session_state.att_data[sid] = "ลา"
                    st.rerun()

            with btn_col2:
                if st.button(f"🔴 ป่วย", key=f"puay_{sid}", use_container_width=True,
                             type="primary" if st.session_state.att_data[sid] == "ป่วย" else "secondary"):
                    st.session_state.att_data[sid] = "ป่วย"
                    st.rerun()
                
                if st.button(f"🟠 ขาด", key=f"khad_{sid}", use_container_width=True,
                             type="primary" if st.session_state.att_data[sid] == "ขาด" else "secondary"):
                    st.session_state.att_data[sid] = "ขาด"
                    st.rerun()
            
            st.write("") # เว้นระยะห่างระหว่างคน

    st.markdown("---")
    
    if st.button("🚀 ยืนยันบันทึกข้อมูลทั้งหมด", type="primary", use_container_width=True):
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
    st.info("ไม่พบข้อมูลนักเรียน")
