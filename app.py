import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime
import plotly.express as px

# ตั้งค่าหน้าเว็บต้องอยู่บรรทัดแรกสุด
st.set_page_config(page_title="ระบบบริหารจัดการ โรงเรียนบ้านเชียงวิทยา", layout="wide", page_icon="🏫")

# 🔗 ฟังก์ชันเชื่อมต่อฐานข้อมูล
@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_sheet"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open("ระบบเช็คชื่อนักเรียน")
    return sh.worksheet("Students"), sh.worksheet("Attendance")

ws_students, ws_attendance = init_connection()

# 🎨 CSS สไตล์ Pluto Theme และ Mobile Responsive
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Prompt', sans-serif; }
    .stApp { background-color: #f4f7f6; } /* สีพื้นหลังสไตล์ Pluto */
    
    /* ปิดส่วนที่ไม่จำเป็นของ Streamlit */
    #MainMenu, footer, header {visibility: hidden;}

    /* กล่อง Dashboard สไตล์ Pluto */
    .pluto-metric {
        display: flex; align-items: center; justify-content: space-between;
        background: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        margin-bottom: 15px;
    }
    .pluto-metric h4 { margin: 0; font-size: 14px; color: #8a909d; font-weight: 500; }
    .pluto-metric h2 { margin: 5px 0 0 0; font-size: 28px; color: #212529; font-weight: 700; }
    .pluto-icon { font-size: 35px; }
    
    /* แถบสีด้านซ้ายของกล่อง */
    .border-blue { border-left: 5px solid #17a2b8; }
    .border-green { border-left: 5px solid #28a745; }
    .border-red { border-left: 5px solid #dc3545; }
    .border-yellow { border-left: 5px solid #ffc107; }

    /* ปรับแต่ง Dropdown ให้สวยและกะทัดรัด */
    div[data-baseweb="select"] { border-radius: 8px; }
    .stSelectbox label { display: none; }
    </style>
""", unsafe_allow_html=True)

# 📱 สร้างแถบเมนูด้านข้าง (Sidebar Navigation)
with st.sidebar:
    st.markdown("### 🏫 ระบบบริหารโรงเรียน")
    st.markdown("โรงเรียนบ้านเชียงวิทยา")
    st.markdown("---")
    menu = st.radio("📌 เลือกหน้าต่างการทำงาน:", ["📝 บันทึกลงเวลา", "📊 แดชบอร์ดผู้บริหาร"])
    st.markdown("---")

# ==========================================
# 🟢 หน้าที่ 1: บันทึกลงเวลา (พร้อมรูปภาพนักเรียน)
# ==========================================
if menu == "📝 บันทึกลงเวลา":
    st.markdown("<h2 style='color: #212529; font-weight:700;'>📝 บันทึกลงเวลาเรียน</h2>", unsafe_allow_html=True)
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

        all_attendance = ws_attendance.get_all_records()
        df_att_check = pd.DataFrame(all_attendance)
        is_already_checked = False
        if not df_att_check.empty:
            if not df_att_check[(df_att_check['วันที่'] == date_str) & (df_att_check['ชั้นเรียน'] == selected_class)].empty:
                is_already_checked = True

        if is_already_checked:
            st.error(f"⚠️ ห้อง {selected_class} บันทึกข้อมูลวันที่ {date_str} เรียบร้อยแล้ว")
        else:
            if 'current_class' not in st.session_state or st.session_state.current_class != selected_class:
                st.session_state.current_class = selected_class
                st.session_state.att_data = {str(r['รหัสนักเรียน']): "มาเรียน" for _, r in df_room.iterrows()}
            
            # สรุปยอดจิ๋ว
            stats = pd.Series(st.session_state.att_data.values()).value_counts()
            st.markdown(f"""
                <div style='background-color:#fff; padding:15px; border-radius:10px; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,0.02); margin-bottom:15px; border:1px solid #eef2f5;'>
                    <span style='color:#28a745; font-weight:bold;'>มา: {stats.get('มาเรียน', 0)}</span> | 
                    <span style='color:#ffc107; font-weight:bold;'>สาย: {stats.get('สาย', 0)}</span> | 
                    <span style='color:#dc3545; font-weight:bold;'>ลา/ป่วย: {stats.get('ลา', 0) + stats.get('ป่วย', 0)}</span> | 
                    <span style='color:#6c757d; font-weight:bold;'>ขาด: {stats.get('ขาด', 0)}</span>
                </div>
            """, unsafe_allow_html=True)

            status_options = ["มาเรียน", "สาย", "ลา", "ป่วย", "ขาด"]
            
            # 📋 วนลูปแสดงรายชื่อพร้อมรูปภาพแบบ Responsive Card
            for index, row in df_room.iterrows():
                sid = str(row['รหัสนักเรียน'])
                name = str(row.get('ชื่อ', ''))
                
                # ตรวจสอบว่ามีลิงก์รูปไหม ถ้าไม่มีให้สร้างรูปจากชื่ออัตโนมัติ (UI Avatars)
                img_url = str(row.get('รูปภาพ', '')).strip()
                if not img_url or img_url.lower() == 'nan':
                    img_url = f"https://ui-avatars.com/api/?name={name}&background=random&color=fff&rounded=true&size=128"

                with st.container(border=True): # สร้างกรอบให้เด็กแต่ละคน
                    # แบ่งคอลัมน์ (รูปภาพ 15%, ชื่อ 50%, ปุ่ม 35%)
                    col_img, col_info, col_status = st.columns([1.5, 5, 3.5])
                    
                    with col_img:
                        st.image(img_url, width=50) # แสดงรูปโปรไฟล์
                    
                    with col_info:
                        st.markdown(f"<div style='padding-top:2px;'><b>{index+1}. {name}</b><br><span style='color:#8a909d; font-size:12px;'>รหัส: {sid}</span></div>", unsafe_allow_html=True)
                    
                    with col_status:
                        current_val = st.session_state.att_data.get(sid, "มาเรียน")
                        new_status = st.selectbox("สถานะ", status_options, key=f"sel_{sid}", label_visibility="collapsed", index=status_options.index(current_val))
                        if new_status != current_val:
                            st.session_state.att_data[sid] = new_status
                            st.rerun()

            st.write("")
            if st.button("🚀 ยืนยันบันทึกข้อมูล", type="primary", use_container_width=True):
                try:
                    final_records = [[date_str, str(r['รหัสนักเรียน']), r.get('ชื่อ',''), r.get('ชั้นเรียน',''), st.session_state.att_data.get(str(r['รหัสนักเรียน']), "มาเรียน"), recorded_by] for _, r in df_room.iterrows()]
                    ws_attendance.append_rows(final_records)
                    st.success("✅ บันทึกข้อมูลเรียบร้อย!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# ==========================================
# 📊 หน้าที่ 2: แดชบอร์ด (สไตล์ Pluto ของแท้)
# ==========================================
elif menu == "📊 แดชบอร์ดผู้บริหาร":
    st.markdown("<h2 style='color: #212529; font-weight:700;'>📊 สรุปสถิติการมาเรียน</h2>", unsafe_allow_html=True)
    
    att_data = ws_attendance.get_all_records()
    if len(att_data) > 0:
        df_att = pd.DataFrame(att_data)
        
        with st.container(border=True):
            st.markdown("<b>🔍 คัดกรองข้อมูล</b>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1: selected_date_dash = st.selectbox("เลือกวันที่", df_att['วันที่'].unique())
            with col2: selected_class_dash = st.multiselect("เลือกชั้นเรียน", df_att['ชั้นเรียน'].unique(), default=df_att['ชั้นเรียน'].unique())

        mask = (df_att['วันที่'] == selected_date_dash) & (df_att['ชั้นเรียน'].isin(selected_class_dash))
        df_filtered = df_att[mask]
        st.write("")
        
        if not df_filtered.empty:
            
            # คำนวณยอด
            total_std = len(df_filtered)
            present = len(df_filtered[df_filtered['สถานะ'] == 'มาเรียน'])
            absent = len(df_filtered[df_filtered['สถานะ'] != 'มาเรียน'])
            percent = (present / total_std) * 100 if total_std > 0 else 0

            # 📈 วาดกล่องตัวเลขสไตล์ Pluto (จะเรียงอัตโนมัติ 1 คอลัมน์ในมือถือ และ 4 คอลัมน์ในคอม)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""<div class="pluto-metric border-blue"><div class="metric-info"><h4>นักเรียนทั้งหมด</h4><h2>{total_std}</h2></div><div class="pluto-icon">👥</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="pluto-metric border-green"><div class="metric-info"><h4>มาเรียนปกติ</h4><h2>{present}</h2></div><div class="pluto-icon">✅</div></div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="pluto-metric border-red"><div class="metric-info"><h4>ลา/ขาด/สาย</h4><h2>{absent}</h2></div><div class="pluto-icon">⚠️</div></div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""<div class="pluto-metric border-yellow"><div class="metric-info"><h4>อัตราการเข้าเรียน</h4><h2>{percent:.1f}%</h2></div><div class="pluto-icon">📈</div></div>""", unsafe_allow_html=True)

            # 📊 กราฟสวยๆ
            col_chart1, col_chart2 = st.columns([1.5, 1])
            with col_chart1:
                with st.container(border=True):
                    st.markdown("<b>📈 สถิติแยกตามห้องเรียน</b>", unsafe_allow_html=True)
                    df_bar = df_filtered.groupby(['ชั้นเรียน', 'สถานะ']).size().reset_index(name='จำนวน')
                    fig_bar = px.bar(df_bar, x='ชั้นเรียน', y='จำนวน', color='สถานะ', barmode='group',
                                     color_discrete_map={'มาเรียน':'#28a745', 'สาย':'#ffc107', 'ลา':'#fd7e14', 'ป่วย':'#dc3545', 'ขาด':'#6c757d'})
                    fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0))
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_chart2:
                with st.container(border=True):
                    st.markdown("<b>🎯 สัดส่วนสถานะ</b>", unsafe_allow_html=True)
                    fig_pie = px.pie(df_filtered, names='สถานะ', hole=0.55,
                                     color='สถานะ', color_discrete_map={'มาเรียน':'#28a745', 'สาย':'#ffc107', 'ลา':'#fd7e14', 'ป่วย':'#dc3545', 'ขาด':'#6c757d'})
                    fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), showlegend=False)
                    fig_pie.update_traces(textposition='outside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)

            # 📋 ตาราง
            with st.container(border=True):
                col_tbl_head, col_btn = st.columns([7, 3])
                with col_tbl_head: st.markdown("<b>📋 รายละเอียดข้อมูลการลงเวลา</b>", unsafe_allow_html=True)
                with col_btn:
                    csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 โหลดไฟล์ CSV", data=csv, file_name=f'report_{selected_date_dash}.csv', use_container_width=True)
                
                # ถ้าในชีตตั้งชื่อว่า 'ชื่อ-นามสกุล' ให้แก้คำว่า 'ชื่อ' ด้วยนะครับ
                st.dataframe(df_filtered[['รหัสนักเรียน', 'ชื่อ', 'ชั้นเรียน', 'สถานะ', 'ผู้บันทึก']], hide_index=True, use_container_width=True)
        else:
            st.info("ไม่พบข้อมูลตามเงื่อนไขที่ค้นหาครับ")
    else:
        st.warning("ยังไม่มีข้อมูลการเช็คชื่อในระบบเลยครับ")
