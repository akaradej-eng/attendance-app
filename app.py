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

st.set_page_config(page_title="ระบบบันทึกเวลาเรียน", layout="wide", page_icon="🏫")
st.title("🏫 ระบบเช็คชื่อรายห้อง โรงเรียนบ้านเชียงวิทยา")

# ฟังก์ชันสำหรับเลือกสีปุ่ม
def get_button_style(current_status, target_status, color_code):
    if current_status == target_status:
        return "primary" # สีเด่นเมื่อถูกเลือก
    return "secondary" # สีจางเมื่อไม่ได้เลือก

data = ws_students.get_all_records()

if len(data) > 0:
    df_students = pd.DataFrame(data)
    class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_class = st.selectbox("📌 เลือกชั้นเรียน", class_list)
    with col2:
        teacher_name = st.text_input("👨‍🏫 ชื่อครูที่ปรึกษา (ผู้บันทึก)")
    with col3:
        check_date = st.date_input("📅 วันที่บันทึก", datetime.today())

    st.markdown("---")
    
    # ส่วนหัว
    col_h_name, col_h_status = st.columns([3, 7])
    with col_h_name: st.markdown("### 👤 รายชื่อนักเรียน")
    with col_h_status: st.markdown("### 📝 เลือกสถานะ (คลิกเพื่อเปลี่ยน)")
    st.markdown("<hr style='border: 2px solid #ccc; margin-top: 0px;'>", unsafe_allow_html=True)

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()

    # 🌟 ระบบจำสถานะด้วย Session State
    if 'att_data' not in st.session_state:
        st.session_state.att_data = {}

    for index, row in df_room.iterrows():
        sid = str(row['รหัสนักเรียน'])
        # ถ้ายังไม่มีข้อมูลในระบบจำ ให้ตั้งค่าเริ่มต้นเป็น "มาเรียน"
        if sid not in st.session_state.att_data:
            st.session_state.att_data[sid] = "มาเรียน"

        col_name, col_ma, col_puay, col_la, col_khad = st.columns([3, 1.75, 1.75, 1.75, 1.75])
        
        with col_name:
            st.markdown(f"<div style='padding-top: 5px;'><b>{row.get('เลขที่','-')}.</b> {row.get('ชื่อ','')}</div>", unsafe_allow_html=True)
        
        # ปุ่ม มาเรียน (เขียว)
        with col_ma:
            if st.button(f"🟢 มาเรียน", key=f"ma_{sid}", use_container_width=True, 
                         type="primary" if st.session_state.att_data[sid] == "มาเรียน" else "secondary"):
                st.session_state.att_data[sid] = "มาเรียน"
                st.rerun()

        # ปุ่ม ป่วย (แดง)
        with col_puay:
            if st.button(f"🔴 ป่วย", key=f"puay_{sid}", use_container_width=True,
                         type="primary" if st.session_state.att_data[sid] == "ป่วย" else "secondary"):
                st.session_state.att_data[sid] = "ป่วย"
                st.rerun()

        # ปุ่ม ลา (เหลือง)
        with col_la:
            if st.button(f"🟡 ลา", key=f"la_{sid}", use_container_width=True,
                         type="primary" if st.session_state.att_data[sid] == "ลา" else "secondary"):
                st.session_state.att_data[sid] = "ลา"
                st.rerun()

        # ปุ่ม ขาด (ส้ม)
        with col_khad:
            if st.button(f"🟠 ขาด", key=f"khad_{sid}", use_container_width=True,
                         type="primary" if st.session_state.att_data[sid] == "ขาด" else "secondary"):
                st.session_state.att_data[sid] = "ขาด"
                st.rerun()

        st.markdown("<hr style='margin: 5px; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("✅ ยืนยันบันทึกข้อมูลทั้งหมดเข้า Google Sheets", type="primary", use_container_width=True):
        if not teacher_name.strip():
            st.error("กรุณากรอกชื่อครูผู้บันทึกก่อนครับ ❌")
        else:
            try:
                date_str = check_date.strftime("%d/%m/%Y")
                final_records = []
                for index, row in df_room.iterrows():
                    sid = str(row['รหัสนักเรียน'])
                    final_records.append([
                        date_str, sid, row.get('ชื่อ',''), 
                        row.get('ชั้นเรียน',''), st.session_state.att_data[sid], teacher_name
                    ])
                
                ws_attendance.append_rows(final_records)
                st.success(f"บันทึกข้อมูลเรียบร้อยแล้ว! ข้อมูลวิ่งเข้า Google Sheets แล้วครับ 🎉")
                # เคลียร์ค่าหลังจากบันทึกเสร็จ
                del st.session_state.att_data
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
