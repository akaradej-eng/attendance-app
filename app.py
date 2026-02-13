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

st.set_page_config(page_title="Dschool Style - เลือกผู้บันทึก", layout="wide", page_icon="🏫")

# ส่วนหัวแอป
st.markdown("<h1 style='text-align: center; color: #1e56a0;'>บันทึกลงเวลาโรงเรียน</h1>", unsafe_allow_html=True)

data = ws_students.get_all_records()

if len(data) > 0:
    df_students = pd.DataFrame(data)
    class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

    # ส่วนการตั้งค่าชั้นเรียนและวันที่
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1: 
            selected_class = st.selectbox("📅 เลือกชั้นเรียน", class_list)
        with c2: 
            check_date = st.date_input("เลือกวันที่", datetime.today())
        
        # 🌟 ดึงรายชื่อครูที่ปรึกษาทั้ง 3 ท่านมาสร้างเป็นตัวเลือก
        room_info = df_students[df_students['ชั้นเรียน'] == selected_class].iloc[0]
        t1 = room_info.get('ครูที่ปรึกษา 1', '')
        t2 = room_info.get('ครูที่ปรึกษา 2', '')
        t3 = room_info.get('ครูที่ปรึกษา 3', '')
        
        # กรองเอาเฉพาะชื่อที่ไม่ว่างเปล่า
        teachers = [t for t in [t1, t2, t3] if t]
        
        # 🌟 ส่วนเลือกผู้บันทึก (เลือกได้ 1 ท่านจาก 3 ท่าน)
        st.markdown("---")
        recorded_by = st.radio("👤 ใครเป็นผู้บันทึกข้อมูลในวันนี้?", teachers, horizontal=True)

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()
    date_str = check_date.strftime("%d/%m/%Y")
    
    # ระบบตรวจสอบการบันทึกซ้ำ
    all_attendance = ws_attendance.get_all_records()
    df_att_check = pd.DataFrame(all_attendance)
    
    is_already_checked = False
    if not df_att_check.empty:
        duplicate = df_att_check[(df_att_check['วันที่'] == date_str) & (df_att_check['ชั้นเรียน'] == selected_class)]
        if not duplicate.empty:
            is_already_checked = True

    if is_already_checked:
        st.error(f"⚠️ ห้อง {selected_class} บันทึกข้อมูลของวันที่ {date_str} ไปแล้ว")
        st.info(f"ผู้ที่เคยบันทึกไว้คือ: {duplicate.iloc[0]['ผู้บันทึก']}")
    else:
        # ส่วนสรุปยอด (Dashboard)
        if 'att_data' not in st.session_state:
            st.session_state.att_data = {str(r['รหัสนักเรียน']): "มาเรียน" for _, r in df_room.iterrows()}

        st.markdown(f"### 📋 รายชื่อนักเรียนห้อง {selected_class}")
        status_options = ["มาเรียน", "สาย", "ลา", "ป่วย", "ขาด"]
        
        for index, row in df_room.iterrows():
            sid = str(row['รหัสนักเรียน'])
            with st.container(border=True):
                col_info, col_btn = st.columns([3, 2])
                with col_info:
                    st.write(f"**{row.get('เลขที่','-')}. {row.get('ชื่อ','')}**")
                    st.caption(f"รหัส: {sid}")
                with col_btn:
                    current_val = st.session_state.att_data.get(sid, "มาเรียน")
                    new_status = st.selectbox("สถานะ", status_options, key=f"sel_{sid}", 
                                             label_visibility="collapsed",
                                             index=status_options.index(current_val))
                    if new_status != current_val:
                        st.session_state.att_data[sid] = new_status
                        st.rerun()

        # ปุ่มบันทึกข้อมูล
        if st.button("🚀 ยืนยันบันทึกข้อมูลทั้งหมด", type="primary", use_container_width=True):
            try:
                # ตรวจสอบซ้ำกันเครื่องอื่นบันทึกก่อนหน้า
                re_check = ws_attendance.get_all_values()
                exists = any(r[0] == date_str and r[3] == selected_class for r in re_check)
                
                if exists:
                    st.error("❌ บันทึกไม่สำเร็จ: มีคนอื่นบันทึกห้องนี้ไปก่อนคุณเสี้ยววินาที!")
                else:
                    final_records = []
                    for _, r in df_room.iterrows():
                        sid = str(r['รหัสนักเรียน'])
                        final_records.append([
                            date_str, sid, r.get('ชื่อ',''), r.get('ชั้นเรียน',''), 
                            st.session_state.att_data[sid], recorded_by
                        ])
                    
                    ws_attendance.append_rows(final_records)
                    st.success(f"✅ บันทึกเรียบร้อย! โดย {recorded_by}")
                    st.balloons()
                    st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.info("กรุณาตรวจสอบข้อมูลในชีต Students")
