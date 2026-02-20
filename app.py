import streamlit as st
import pandas as pd
from datetime import datetime, date

# ==========================================
# 🎨 1. ตั้งค่าหน้าเพจและ CSS (HTML/CSS UI)
# ==========================================
st.set_page_config(page_title="SIS - Ban Chiang Wittaya", layout="wide", page_icon="🏫")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700&display=swap');
    * { font-family: 'Prompt', sans-serif; }
    .main { background-color: #f4f7f6; }
    .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .metric-card { text-align: center; padding: 20px; border-radius: 12px; color: white; }
    .bg-blue { background: linear-gradient(135deg, #1e56a0, #2a6fcc); }
    .bg-green { background: linear-gradient(135deg, #28a745, #34ce57); }
    .bg-orange { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
    .bg-red { background: linear-gradient(135deg, #dc3545, #e4606d); }
    .logout-btn { float: right; color: #dc3545; font-weight: bold; text-decoration: none; cursor: pointer; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 2. ระบบจัดการ Session & Login
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.ref_name = None

# [จำลองฐานข้อมูล Users] ในใช้งานจริงให้ดึงจาก ws_users.get_all_records()
mock_users = {
    "t01": {"pass": "1234", "role": "teacher", "name": "ครูอัครเดช"},
    "6326": {"pass": "1234", "role": "student", "name": "ด.ช.จารุกร หงส์สิงห์"},
    "admin": {"pass": "admin", "role": "admin", "name": "ผู้ดูแลระบบ"},
    "boss": {"pass": "boss", "role": "executive", "name": "ผู้อำนวยการ"}
}

def login(user, pwd):
    if user in mock_users and mock_users[user]["pass"] == pwd:
        st.session_state.logged_in = True
        st.session_state.role = mock_users[user]["role"]
        st.session_state.username = user
        st.session_state.ref_name = mock_users[user]["name"]
        st.rerun()
    else:
        st.error("❌ Username หรือ Password ไม่ถูกต้อง!")

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# --- หน้า Login ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='card' style='margin-top: 50px; text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.markdown("<h2>🏫 ระบบสารสนเทศ (SIS)</h2><p>โรงเรียนบ้านเชียงวิทยา</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 ชื่อผู้ใช้งาน (Username)")
            password = st.text_input("🔑 รหัสผ่าน (Password)", type="password")
            submit = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            if submit:
                login(username, password)
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # หยุดการทำงานตรงนี้ถ้ายังไม่ login

# ==========================================
# 🏛️ 3. ส่วนแสดงผลตามสิทธิ์ผู้ใช้งาน (Routing)
# ==========================================

# แถบ Header
col_header1, col_header2 = st.columns([3, 1])
col_header1.markdown(f"<h3>ยินดีต้อนรับ, {st.session_state.ref_name} ({st.session_state.role.upper()})</h3>", unsafe_allow_html=True)
with col_header2:
    if st.button("🚪 ออกจากระบบ", use_container_width=True):
        logout()
st.markdown("<hr style='margin-top: 0;'>", unsafe_allow_html=True)

# ------------------------------------------
# 👩‍🏫 สิทธิ์: ครู (Teacher)
# ------------------------------------------
if st.session_state.role == "teacher":
    st.markdown("#### 📝 บันทึกการมาเข้าแถว")
    with st.container():
        c1, c2 = st.columns(2)
        sel_class = c1.selectbox("เลือกชั้นเรียน", ["ม.1/1", "ม.1/2"])
        check_date = c2.date_input("วันที่บันทึก", datetime.today())
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        # จำลองรายชื่อ
        students = [{"id": "6326", "name": "ด.ช.จารุกร"}, {"id": "6329", "name": "ด.ช.จิรายุส"}]
        for std in students:
            col_id, col_name, col_status = st.columns([1, 3, 4])
            col_id.write(std["id"])
            col_name.write(std["name"])
            with col_status:
                st.radio("สถานะ", ["มา", "สาย", "ขาด", "ป่วย/ลา"], key=f"status_{std['id']}", horizontal=True, label_visibility="collapsed")
        
        if st.button("💾 บันทึกข้อมูลเข้าฐานข้อมูล", type="primary", use_container_width=True):
            st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# 👨‍🎓 สิทธิ์: นักเรียน (Student)
# ------------------------------------------
elif st.session_state.role == "student":
    st.markdown("#### 👤 ข้อมูลการเข้าเรียนของฉัน")
    
    # คำนวณสิทธิ์สอบจำลอง
    total_days = 100
    present_days = 85
    percent = (present_days / total_days) * 100
    is_eligible = "✅ มีสิทธิ์สอบ" if percent >= 80 else "❌ หมดสิทธิ์สอบ"
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card bg-blue'><h3>วันเปิดเรียนทั้งหมด</h3><h2>{total_days} วัน</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card bg-green'><h3>มาเรียน</h3><h2>{present_days} วัน</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card {'bg-green' if percent >= 80 else 'bg-red'}'><h3>สิทธิ์สอบ (>80%)</h3><h2>{is_eligible} ({percent}%)</h2></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📅 รายงานรายวัน", "📊 รายงานรายเดือน"])
    with tab1:
        st.info("จำลองตารางแสดงผลรายวัน (ดึงจาก Sheet Attendance เฉพาะรหัสของตัวเอง)")
        st.table(pd.DataFrame({"วันที่": ["20/02/2026", "19/02/2026"], "สถานะ": ["มา", "มา"], "ผู้บันทึก": ["ครูอัครเดช", "ครูอัครเดช"]}))
    with tab2:
        st.info("สรุปเป็นรายเดือน")

# ------------------------------------------
# ⚙️ สิทธิ์: ผู้ดูแลระบบ (Admin)
# ------------------------------------------
elif st.session_state.role == "admin":
    st.markdown("#### ⚙️ แผงควบคุมผู้ดูแลระบบ")
    tab_date, tab_users, tab_data = st.tabs(["📅 ตั้งค่าปฏิทินและวันหยุด", "👥 จัดการครู/นักเรียน", "📝 แก้ไขข้อมูลการบันทึก"])
    
    with tab_date:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.date_input("เริ่มบันทึกภาคเรียน (Start Date)")
        c2.date_input("สิ้นสุดการบันทึก (End Date)")
        st.markdown("##### กำหนดวันหยุด (ไม่ให้ระบบบันทึก)")
        st.date_input("เลือกวันหยุด (สามารถเลือกได้หลายวัน)", key="holidays")
        st.button("บันทึกปฏิทิน")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab_users:
        st.info("ส่วนสำหรับ เพิ่ม/แก้ไข/ลบ ข้อมูลในชีต Students และ Users")
        st.button("+ เพิ่มครูประจำชั้นใหม่")
        
    with tab_data:
        st.info("ค้นหานักเรียนหรือวันที่ เพื่อแก้ไขสถานะ มา/สาย/ขาด ย้อนหลัง")

# ------------------------------------------
# 📊 สิทธิ์: ผู้บริหาร (Executive)
# ------------------------------------------
elif st.session_state.role == "executive":
    st.markdown("#### 📊 รายงานสถิติภาพรวมโรงเรียน")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("<div class='metric-card bg-blue'><h3>นักเรียนทั้งหมด</h3><h2>1,250</h2></div>", unsafe_allow_html=True)
    c2.markdown("<div class='metric-card bg-green'><h3>มาเรียนวันนี้</h3><h2>1,100</h2></div>", unsafe_allow_html=True)
    c3.markdown("<div class='metric-card bg-orange'><h3>สาย/ลา</h3><h2>100</h2></div>", unsafe_allow_html=True)
    c4.markdown("<div class='metric-card bg-red'><h3>ขาดเรียน</h3><h2>50</h2></div>", unsafe_allow_html=True)
    
    st.markdown("<br><div class='card'><h4>📈 สถิติแยกตามระดับชั้น</h4>", unsafe_allow_html=True)
    # จำลองกราฟหรือตาราง
    df_exec = pd.DataFrame({
        "ชั้นเรียน": ["ม.1", "ม.2", "ม.3", "ม.4", "ม.5", "ม.6"],
        "มา (%)": [95, 92, 90, 88, 85, 96]
    })
    st.bar_chart(df_exec.set_index("ชั้นเรียน"))
    st.markdown("</div>", unsafe_allow_html=True)
