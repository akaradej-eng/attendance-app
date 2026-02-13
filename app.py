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

data = ws_students.get_all_records()

if len(data) > 0:
    df_students = pd.DataFrame(data)
    class_list = df_students['ชั้นเรียน'].unique().tolist()
    class_list.sort()

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_class = st.selectbox("📌 เลือกชั้นเรียน", class_list)
    with col2:
        teacher_name = st.text_input("👨‍🏫 ชื่อครูที่ปรึกษา (ผู้บันทึก)")
    with col3:
        check_date = st.date_input("📅 วันที่บันทึก", datetime.today())

    st.markdown("---")
    
    # ส่วนหัว (Header)
    col_head_name, col_head_status = st.columns([3, 7])
    with col_head_name:
        st.markdown("### 👤 รายชื่อนักเรียน")
    with col_head_status:
        st.markdown("### 📝 สถานะการมาเรียน")
    st.markdown("<hr style='border: 2px solid #ccc; margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True) 

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()
    attendance_status = {}

    # วนลูปแสดงรายชื่อและปุ่มสถานะพร้อมสี
    for index, row in df_room.iterrows():
        # ปรับสัดส่วนให้ฝั่งปุ่มกว้างขึ้น (3:7) จะได้เรียงแนวนอนสวยๆ
        col_name, col_status = st.columns([3, 7]) 
        
        with col_name:
            st.markdown(f"<div style='padding-top: 10px;'><b>เลขที่ {row.get('เลขที่', '-')}</b> | {row.get('ชื่อ', '')}</div>", unsafe_allow_html=True)
        
        with col_status:
            attendance_status[row['รหัสนักเรียน']] = st.radio(
                f"status_{row['รหัสนักเรียน']}", 
                # 🌟 เปลี่ยนตัวเลือกเป็นสีตามที่คุณต้องการ
                ["🟢 มาเรียน", "🔴 ป่วย", "🟡 ลา", "🟠 ขาด"], 
                horizontal=True,
                label_visibility="collapsed",
                key=f"status_{row['รหัสนักเรียน']}"
            )
            
        st.markdown("<hr style='margin: 0px; padding: 0px; border-top: 1px dashed #eee;'>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("💾 บันทึกข้อมูลทั้งห้อง", type="primary", use_container_width=True):
        if teacher_name.strip() == "":
            st.error("กรุณากรอกชื่อครูผู้บันทึกก่อนครับ ❌")
        else:
            try:
                date_str = check_date.strftime("%d/%m/%Y")
                records_to_insert = []
                
                for index, row in df_room.iterrows():
                    student_id = row['รหัสนักเรียน']
                    status = attendance_status[student_id]
                    
                    records_to_insert.append([
                        date_str, 
                        str(student_id), 
                        str(row.get('ชื่อ', '')), 
                        str(row.get('ชั้นเรียน', '')), 
                        str(status), 
                        teacher_name
                    ])
                
                ws_attendance.append_rows(records_to_insert)
                st.success(f"บันทึกข้อมูลของห้อง {selected_class} จำนวน {len(records_to_insert)} รายการ เรียบร้อยแล้ว! ✅")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
else:
    st.info("ยังไม่มีข้อมูลนักเรียนในระบบครับ โปรดเพิ่มข้อมูลลงในชีต 'Students'")
