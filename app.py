import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="ระบบบริหารจัดการ โรงเรียนบ้านเชียงวิทยา", layout="wide", page_icon="🏫")

# 🎨 CSS ตกแต่ง
st.markdown("""
    <style>
    .summary-box { background-color: #1e56a0; color: white; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 20px;}
    div[data-baseweb="select"] { width: 130px !important; }
    .stSelectbox label { display: none; }
    </style>
""", unsafe_allow_html=True)

# 🔗 ฟังก์ชันเชื่อมต่อฐานข้อมูล (ทำครั้งเดียวโหลดเร็วขึ้น)
@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_sheet"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    return gc.open("ระบบเช็คชื่อนักเรียน")

sh = init_connection()
ws_students = sh.worksheet("Students")
ws_attendance = sh.worksheet("Attendance")

# 📱 สร้างแถบเมนูด้านข้าง (Sidebar Navigation)
with st.sidebar:
    st.markdown("### 🏫 ระบบบริหารโรงเรียน")
    st.markdown("โรงเรียนบ้านเชียงวิทยา")
    st.markdown("---")
    menu = st.radio("📌 เลือกหน้าต่างการทำงาน:", ["📝 บันทึกลงเวลา", "📊 แดชบอร์ดผู้บริหาร"])
    st.markdown("---")

# ==========================================
# 🟢 หน้าที่ 1: บันทึกลงเวลา (สำหรับครู)
# ==========================================
if menu == "📝 บันทึกลงเวลา":
    st.markdown("<h2 style='text-align: center; color: #1e56a0;'>บันทึกลงเวลาโรงเรียน</h2>", unsafe_allow_html=True)
    data = ws_students.get_all_records()

    if len(data) > 0:
        df_students = pd.DataFrame(data)
        class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

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
            if 'att_data' not in st.session_state:
                st.session_state.att_data = {str(r['รหัสนักเรียน']): "มาเรียน" for _, r in df_room.iterrows()}
            
            stats = pd.Series(st.session_state.att_data.values()).value_counts()
            st.markdown(f"""
                <div class='summary-box'>
                    <b>มา: {stats.get('มาเรียน', 0)} | สาย: {stats.get('สาย', 0)} | ลา: {stats.get('ลา', 0) + stats.get('ป่วย', 0)} | ขาด: {stats.get('ขาด', 0)}</b>
                </div>
            """, unsafe_allow_html=True)

            status_options = ["มาเรียน", "สาย", "ลา", "ป่วย", "ขาด"]
            for index, row in df_room.iterrows():
                sid = str(row['รหัสนักเรียน'])
                col_name, col_status = st.columns([7, 3])
                with col_name:
                    st.markdown(f"<div style='padding-top:10px;'>{index+1}. {row.get('ชื่อ','')}</div>", unsafe_allow_html=True)
                with col_status:
                    current_val = st.session_state.att_data.get(sid, "มาเรียน")
                    new_status = st.selectbox("สถานะ", status_options, key=f"sel_{sid}", label_visibility="collapsed", index=status_options.index(current_val))
                    if new_status != current_val:
                        st.session_state.att_data[sid] = new_status
                        st.rerun()
                st.markdown("<hr style='margin: 2px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

            if st.button("🚀 บันทึกข้อมูล", type="primary", use_container_width=True):
                try:
                    final_records = [[date_str, str(r['รหัสนักเรียน']), r.get('ชื่อ',''), r.get('ชั้นเรียน',''), st.session_state.att_data[str(r['รหัสนักเรียน'])], recorded_by] for _, r in df_room.iterrows()]
                    ws_attendance.append_rows(final_records)
                    st.success("✅ บันทึกสำเร็จ!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# ==========================================
# 📊 หน้าที่ 2: แดชบอร์ด (สำหรับผู้บริหาร)
# ==========================================
elif menu == "📊 แดชบอร์ดผู้บริหาร":
    st.markdown("<h2 style='text-align: center; color: #1e56a0;'>📊 สรุปสถิติการมาเรียน</h2>", unsafe_allow_html=True)
    
    att_data = ws_attendance.get_all_records()
    if len(att_data) > 0:
        df_att = pd.DataFrame(att_data)
        
        # ตัวกรองข้อมูล
        with st.container(border=True):
            st.markdown("**🔍 คัดกรองข้อมูล**")
            col1, col2 = st.columns(2)
            with col1:
                selected_date_dash = st.selectbox("เลือกวันที่", df_att['วันที่'].unique())
            with col2:
                # เลือกได้หลายห้องพร้อมกัน
                selected_class_dash = st.multiselect("เลือกชั้นเรียน (ดูรวมได้)", df_att['ชั้นเรียน'].unique(), default=df_att['ชั้นเรียน'].unique())

        # กรองข้อมูลตามที่เลือก
        mask = (df_att['วันที่'] == selected_date_dash) & (df_att['ชั้นเรียน'].isin(selected_class_dash))
        df_filtered = df_att[mask]

        st.markdown("---")
        
        if not df_filtered.empty:
            # สรุปยอดรวม (Metric)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🟢 มาเรียน", len(df_filtered[df_filtered['สถานะ'] == 'มาเรียน']))
            m2.metric("🟡 สาย", len(df_filtered[df_filtered['สถานะ'] == 'สาย']))
            m3.metric("🟠 ลา (ป่วย/กิจ)", len(df_filtered[df_filtered['สถานะ'].isin(['ลา', 'ป่วย'])]))
            m4.metric("🔴 ขาด", len(df_filtered[df_filtered['สถานะ'] == 'ขาด']))
            
            # กราฟวงกลมแสดงสัดส่วน
            col_chart, col_table = st.columns([1, 1.2])
            with col_chart:
                fig = px.pie(df_filtered, names='สถานะ', title='สัดส่วนการมาเรียนประจำวัน', 
                             color='สถานะ', 
                             color_discrete_map={'มาเรียน':'#2e7d32', 'สาย':'#fbc02d', 'ลา':'#ef6c00', 'ป่วย':'#c62828', 'ขาด':'#757575'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col_table:
                st.markdown("**📋 รายละเอียดข้อมูลนักเรียน**")
                # แสดงตารางข้อมูลดิบ
                st.dataframe(df_filtered[['ชื่อ', 'ชั้นเรียน', 'สถานะ', 'ผู้บันทึก']], hide_index=True, use_container_width=True)
                
                # ปุ่มดาวน์โหลด Excel/CSV
                csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 ดาวน์โหลดรายงาน (CSV)", data=csv, file_name=f'report_{selected_date_dash}.csv', mime='text/csv', use_container_width=True)
        else:
            st.info("ไม่พบข้อมูลตามเงื่อนไขที่ค้นหาครับ")
    else:
        st.warning("ยังไม่มีข้อมูลการเช็คชื่อในระบบเลยครับ")
