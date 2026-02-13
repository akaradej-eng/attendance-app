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

st.set_page_config(page_title="Dschool AI - One Line", layout="wide", page_icon="🏫")

# 🎨 CSS ขั้นสูงเพื่อให้แสดงผลบรรทัดเดียวและสวยงามแบบแอปมือถือ
st.markdown("""
    <style>
    /* ปรับแต่ง Container ของนักเรียนแต่ละคน */
    .student-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: white;
        padding: 8px 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 5px;
    }
    /* ปรับแต่งชื่อนักเรียน */
    .student-info {
        flex: 1;
        font-size: 16px;
        color: #333;
    }
    /* ปรับแต่งส่วนของ Selectbox ให้เล็กลงและพอดี */
    div[data-baseweb="select"] {
        width: 130px !important;
    }
    .stSelectbox label { display: none; } /* ซ่อน Label ของ Selectbox */
    
    /* สรุปยอด Dashboard */
    .summary-box {
        background-color: #1e56a0;
        color: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 20px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #1e56a0;'>บันทึกลงเวลาโรงเรียน</h2>", unsafe_allow_html=True)

data = ws_students.get_all_records()

if len(data) > 0:
    df_students = pd.DataFrame(data)
    class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

    # ส่วนการเลือกห้องและครู
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1: selected_class = st.selectbox("📅 ชั้นเรียน", class_list)
        with c2: check_date = st.date_input("วันที่", datetime.today())
        
        room_info = df_students[df_students['ชั้นเรียน'] == selected_class].iloc[0]
        teachers = [t for t in [room_info.get('ครูที่ปรึกษา 1'), room_info.get('ครูที่ปรึกษา 2'), room_info.get('ครูที่ปรึกษา 3')] if t]
        recorded_by = st.radio("👤 ผู้บันทึก:", teachers, horizontal=True)

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()
    date_str = check_date.strftime("%d/%m/%Y")

    # ตรวจสอบการบันทึกซ้ำ
    all_attendance = ws_attendance.get_all_records()
    df_att_check = pd.DataFrame(all_attendance)
    is_already_checked = False
    if not df_att_check.empty:
        if not df_att_check[(df_att_check['วันที่'] == date_str) & (df_att_check['ชั้นเรียน'] == selected_class)].empty:
            is_already_checked = True

    if is_already_checked:
        st.error(f"⚠️ ห้อง {selected_class} บันทึกข้อมูลวันที่ {date_str} เรียบร้อยแล้ว")
    else:
        # สรุปยอด Dashboard
        if 'att_data' not in st.session_state:
            st.session_state.att_data = {str(r['รหัสนักเรียน']): "มาเรียน" for _, r in df_room.iterrows()}
        
        stats = pd.Series(st.session_state.att_data.values()).value_counts()
        st.markdown(f"""
            <div class='summary-box'>
                <b>มา: {stats.get('มาเรียน', 0)} | สาย: {stats.get('สาย', 0)} | ลา: {stats.get('ลา', 0) + stats.get('ป่วย', 0)} | ขาด: {stats.get('ขาด', 0)}</b>
            </div>
        """, unsafe_allow_html=True)

        # 📋 รายชื่อนักเรียนแบบบรรทัดเดียว (One-Line)
        status_options = ["มาเรียน", "สาย", "ลา", "ป่วย", "ขาด"]
        
        for index, row in df_room.iterrows():
            sid = str(row['รหัสนักเรียน'])
            
            # ใช้ st.columns เพื่อบังคับให้อยู่บรรทัดเดียวกันเป๊ะๆ
            col_name, col_status = st.columns([7, 3])
            
            with col_name:
                # แสดงเลขที่และชื่อในบรรทัดเดียว
                st.markdown(f"<div style='padding-top:10px;'>{index+1}. {row.get('ชื่อ','')}</div>", unsafe_allow_html=True)
            
            with col_status:
                current_val = st.session_state.att_data.get(sid, "มาเรียน")
                new_status = st.selectbox(
                    "สถานะ", status_options, key=f"sel_{sid}", 
                    label_visibility="collapsed",
                    index=status_options.index(current_val)
                )
                if new_status != current_val:
                    st.session_state.att_data[sid] = new_status
                    st.rerun()
            
            st.markdown("<hr style='margin: 2px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

        if st.button("🚀 บันทึกข้อมูล", type="primary", use_container_width=True):
            try:
                final_records = [[date_str, str(r['รหัสนักเรียน']), r.get('ชื่อ',''), 
                                 r.get('ชั้นเรียน',''), st.session_state.att_data[str(r['รหัสนักเรียน'])], 
                                 recorded_by] for _, r in df_room.iterrows()]
                ws_attendance.append_rows(final_records)
                st.success("✅ บันทึกสำเร็จ!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
