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

st.set_page_config(page_title="Dschool Style - ระบบเช็คชื่อ", layout="wide", page_icon="🏫")

# 🎨 Custom CSS เพื่อปรับแต่งให้ใกล้เคียงกับตัวอย่าง
st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    .stHeader { background-color: #1e56a0; color: white; padding: 10px; border-radius: 0 0 20px 20px; text-align: center; }
    .summary-card { background-color: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .student-row { background-color: white; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 8px; display: flex; align-items: center; }
    .status-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; text-align: center; width: 100px; }
    /* สีสถานะ */
    .status-ma { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32; }
    .status-sai { background-color: #fffde7; color: #fbc02d; border: 1px solid #fbc02d; }
    .status-la { background-color: #fff3e0; color: #ef6c00; border: 1px solid #ef6c00; }
    .status-puey { background-color: #ffebee; color: #c62828; border: 1px solid #c62828; }
    </style>
    """, unsafe_allow_html=True)

# ส่วนหัวแอป
st.markdown("<div class='stHeader'><h1>บันทึกลงเวลาโรงเรียน</h1></div>", unsafe_allow_html=True)

data = ws_students.get_all_records()

if len(data) > 0:
    df_students = pd.DataFrame(data)
    class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

    # การตั้งค่าเบื้องต้น
    c1, c2 = st.columns(2)
    with c1: selected_class = st.selectbox("📅 ชั้นเรียน", class_list, index=0)
    with c2: check_date = st.date_input("เลือกวันที่", datetime.today())
    
    teacher_name = st.text_input("👨‍🏫 ชื่อครูที่ปรึกษา", value="ครูที่ปรึกษา")

    df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()
    total_std = len(df_room)

    # 📊 ส่วนสรุปจำนวน (Dashboard แบบในรูป)
    if 'att_data' not in st.session_state:
        st.session_state.att_data = {str(r['รหัสนักเรียน']): "มาเรียน" for _, r in df_room.iterrows()}

    # คำนวณยอดสรุปแบบ Real-time
    stats = pd.Series(st.session_state.att_data.values()).value_counts()
    
    st.markdown(f"""
    <div class='summary-card'>
        <h3 style='text-align:center;'>สรุปยอด {selected_class}</h3>
        <table style='width:100%; text-align:right;'>
            <tr style='color:#1e56a0; font-weight:bold;'><td>ประเภท</td><td>รวม</td></tr>
            <tr><td>จำนวนเต็ม</td><td>{total_std}</td></tr>
            <tr style='color:green;'><td>มาเรียน</td><td>{stats.get('มาเรียน', 0)}</td></tr>
            <tr style='color:orange;'><td>สาย</td><td>{stats.get('สาย', 0)}</td></tr>
            <tr style='color:red;'><td>ลาป่วย/ลากิจ</td><td>{stats.get('ลา', 0) + stats.get('ป่วย', 0)}</td></tr>
            <tr style='color:grey;'><td>ขาด</td><td>{stats.get('ขาด', 0)}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 📋 รายการนักเรียน
    status_options = ["มาเรียน", "สาย", "ลา", "ป่วย", "ขาด"]
    status_emoji = {"มาเรียน": "🟢", "สาย": "🟡", "ลา": "🟠", "ป่วย": "🔴", "ขาด": "⚪"}

    for index, row in df_room.iterrows():
        sid = str(row['รหัสนักเรียน'])
        
        # สร้างแถวนักเรียนแบบ Responsive
        with st.container():
            col_img, col_info, col_btn = st.columns([1, 3, 2])
            
            with col_img:
                # จำลองรูปภาพ (ถ้ามี URL รูปในชีตให้นำมาใส่ตรงนี้ได้)
                st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
            
            with col_info:
                st.markdown(f"**{index+1}. {row.get('ชื่อ','')}**")
                st.caption(f"รหัส: {sid}")
            
            with col_btn:
                # ปุ่มเลือกสถานะแบบ Dropdown ที่ดูสะอาดตา
                current_val = st.session_state.att_data.get(sid, "มาเรียน")
                new_status = st.selectbox(
                    "สถานะ", 
                    status_options, 
                    key=f"sel_{sid}", 
                    label_visibility="collapsed",
                    index=status_options.index(current_val)
                )
                if new_status != current_val:
                    st.session_state.att_data[sid] = new_status
                    st.rerun()

    st.write("")
    if st.button("🚀 ยืนยันบันทึกข้อมูล", type="primary", use_container_width=True):
        try:
            date_str = check_date.strftime("%d/%m/%Y")
            final_records = [[date_str, str(r['รหัสนักเรียน']), r.get('ชื่อ',''), 
                             r.get('ชั้นเรียน',''), st.session_state.att_data[str(r['รหัสนักเรียน'])], 
                             teacher_name] for _, r in df_room.iterrows()]
            ws_attendance.append_rows(final_records)
            st.success("✅ บันทึกข้อมูลเรียบร้อย!")
            st.balloons()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
