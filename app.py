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

    # ส่วนเลือกข้อมูลด้านบน
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_class = st.selectbox("📌 เลือกชั้นเรียน", class_list)
    with col2:
        teacher_name = st.text_input("👨‍🏫 ชื่อครูที่ปรึกษา (ผู้บันทึก)")
    with col3:
        check_date = st.date_input("📅 วันที่บันทึก", datetime.today())

    st.markdown("---")
    st.subheader(f"รายชื่อนักเรียนชั้น {selected_class}")

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()
    
    # สร้างพื้นที่เก็บสถานะของเด็กแต่ละคน
    attendance_status = {}

    # 2. วนลูปสร้างแถวแนวนอน (ชื่อเด็กซ้าย - สถานะขวา)
    for index, row in df_room.iterrows():
        # แบ่งความกว้างหน้าจอเป็น 2 ส่วน (ชื่อ 40% : ปุ่มสถานะ 60%)
        col_name, col_status = st.columns([4, 6]) 
        
        with col_name:
            # แสดง เลขที่ รหัสนักเรียน และชื่อ
            st.markdown(f"**เลขที่ {row.get('เลขที่', '-')}** | {row.get('รหัสนักเรียน', '')} | {row.get('ชื่อ', '')}")
        
        with col_status:
            # สร้างปุ่มเลือกสถานะแนวนอน
            attendance_status[row['รหัสนักเรียน']] = st.radio(
                f"สถานะของ {row['รหัสนักเรียน']}", 
                ["มาเรียนปกติ", "สาย", "ลาป่วย/ลากิจ", "ขาดเรียน"], 
                horizontal=True,
                label_visibility="collapsed", # ซ่อนหัวข้อปุ่มเพื่อความสะอาดตา
                key=f"status_{row['รหัสนักเรียน']}" # ต้องใส่ key ให้ไม่ซ้ำกัน
            )
            
        st.markdown("<hr style='margin: 0px; padding: 0px;'>", unsafe_allow_html=True) # เส้นคั่นบางๆ ระหว่างคน
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. ปุ่มบันทึกข้อมูล
    if st.button("💾 บันทึกข้อมูลทั้งห้อง", type="primary"):
        if teacher_name.strip() == "":
            st.error("กรุณากรอกชื่อครูผู้บันทึกก่อนครับ ❌")
        else:
            try:
                date_str = check_date.strftime("%d/%m/%Y")
                records_to_insert = []
                
                # วนลูปดึงสถานะที่ครูเลือก เตรียมส่งเข้าชีต
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
    st.info("ยังไม่มีข้อมูลนักเรียนในระบบครับ")
