import streamlit as st
import gspread
import json
from datetime import datetime

# 1. ดึงกุญแจจากตู้เซฟของ Streamlit แทนการอ่านไฟล์
creds_dict = json.loads(st.secrets["google_sheet"]["credentials"])
gc = gspread.service_account_from_dict(creds_dict)

# 2. เปิดไฟล์ Google Sheets
sh = gc.open("ระบบเช็คชื่อนักเรียน")
worksheet = sh.sheet1

st.set_page_config(page_title="ระบบบันทึกเวลาเรียน", page_icon="🏫")
st.title("🏫 ระบบบันทึกเวลามาเรียน โรงเรียนบ้านเชียงวิทยา")
st.write("แอปพลิเคชันสำหรับเช็คชื่อและบันทึกลงฐานข้อมูลอัตโนมัติ")

with st.form("attendance_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        student_id = st.text_input("รหัสนักเรียน / ชื่อ-นามสกุล")
    with col2:
        date = st.date_input("วันที่", datetime.today())
        
    status = st.radio("สถานะ", ["มาเรียนปกติ", "สาย", "ลาป่วย/ลากิจ", "ขาดเรียน"], horizontal=True)
    
    submitted = st.form_submit_button("💾 บันทึกข้อมูล")

    if submitted:
        if student_id.strip() == "":
            st.error("กรุณากรอกข้อมูลให้ครบถ้วนครับ ❌")
        else:
            try:
                date_str = date.strftime("%d/%m/%Y")
                worksheet.append_row([date_str, student_id, status])
                st.success(f"บันทึกข้อมูลของ **{student_id}** ลงตารางเรียบร้อยแล้ว! ✅")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
