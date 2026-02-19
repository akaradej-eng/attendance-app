import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime, date
import plotly.express as px

st.set_page_config(page_title="ระบบบริหารจัดการ โรงเรียนบ้านเชียงวิทยา", layout="wide", page_icon="🏫")

# 🔗 1. ฟังก์ชันเชื่อมต่อฐานข้อมูล (เพิ่มระบบสร้างชีต Settings อัตโนมัติ)
@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_sheet"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open("ระบบเช็คชื่อนักเรียน")
    
    ws_stud = sh.worksheet("Students")
    ws_att = sh.worksheet("Attendance")
    
    # ตรวจสอบและสร้างชีต Settings สำหรับแอดมิน (ถ้ายังไม่มี)
    try:
        ws_set = sh.worksheet("Settings")
    except gspread.exceptions.WorksheetNotFound:
        ws_set = sh.add_worksheet(title="Settings", rows=10, cols=2)
        ws_set.append_row(["Key", "Value"])
        ws_set.append_row(["StartDate", "2024-05-01"])
        ws_set.append_row(["EndDate", "2025-03-31"])
        
    return ws_stud, ws_att, ws_set

ws_students, ws_attendance, ws_settings = init_connection()

# ดึงค่าการตั้งค่าระบบ (วันเริ่มต้น-สิ้นสุด)
set_data = ws_settings.get_all_records()
settings_dict = {str(row['Key']): str(row['Value']) for row in set_data}
try:
    term_start = datetime.strptime(settings_dict.get('StartDate', '2024-05-01'), "%Y-%m-%d").date()
    term_end = datetime.strptime(settings_dict.get('EndDate', '2025-03-31'), "%Y-%m-%d").date()
except:
    term_start, term_end = date(2024, 5, 1), date(2025, 3, 31)

# 🎨 2. CSS สไตล์ Pluto Theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Prompt', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    #MainMenu, footer, header {visibility: hidden;}

    .pluto-metric {
        display: flex; align-items: center; justify-content: space-between;
        background: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03); margin-bottom: 15px;
    }
    .pluto-metric h4 { margin: 0; font-size: 14px; color: #8a909d; font-weight: 500; }
    .pluto-metric h2 { margin: 5px 0 0 0; font-size: 28px; color: #212529; font-weight: 700; }
    .pluto-icon { font-size: 35px; }
    
    .border-blue { border-left: 5px solid #17a2b8; }
    .border-green { border-left: 5px solid #28a745; }
    .border-red { border-left: 5px solid #dc3545; }
    .border-yellow { border-left: 5px solid #ffc107; }

    div[data-baseweb="select"] { border-radius: 8px; }
    .stSelectbox label { display: none; }
    </style>
""", unsafe_allow_html=True)

# 📱 3. สร้างแถบเมนูด้านข้าง (Sidebar Navigation)
with st.sidebar:
    st.markdown("### 🏫 ระบบโรงเรียน")
    st.markdown("บ้านเชียงวิทยา")
    st.markdown("---")
    menu = st.radio("📌 เลือกหน้าต่างการทำงาน:", ["📝 บันทึกลงเวลา", "📊 แดชบอร์ด (วิเคราะห์ข้อมูล)", "⚙️ ตั้งค่าระบบ (Admin)"])
    st.markdown("---")
    st.info(f"📅 รอบการบันทึกปัจจุบัน:\n{term_start.strftime('%d/%m/%Y')} ถึง {term_end.strftime('%d/%m/%Y')}")

# ==========================================
# 🟢 หน้าที่ 1: บันทึกลงเวลา (สำหรับครู)
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

        # 🛑 ตรวจสอบว่าวันที่เลือก อยู่ในช่วงเปิดเทอมหรือไม่
        if not (term_start <= check_date <= term_end):
            st.error(f"⛔ ไม่สามารถบันทึกข้อมูลได้! วันที่ {date_str} อยู่นอกเหนือรอบการบันทึกที่ผู้ดูแลระบบกำหนดไว้")
            st.warning("กรุณาติดต่อผู้ดูแลระบบ (Admin) เพื่อปรับปรุงช่วงเวลาเปิด-ปิดเทอมครับ")
        else:
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
                for index, row in df_room.iterrows():
                    sid = str(row['รหัสนักเรียน'])
                    name = str(row.get('ชื่อ', ''))
                    img_url = str(row.get('รูปภาพ', '')).strip()
                    if not img_url or img_url.lower() == 'nan':
                        img_url = f"https://ui-avatars.com/api/?name={name}&background=random&color=fff&rounded=true&size=128"

                    with st.container(border=True): 
                        col_img, col_info, col_status = st.columns([1.5, 5, 3.5])
                        with col_img: st.image(img_url, width=50) 
                        with col_info: st.markdown(f"<div style='padding-top:2px;'><b>{index+1}. {name}</b><br><span style='color:#8a909d; font-size:12px;'>รหัส: {sid}</span></div>", unsafe_allow_html=True)
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
# 📊 หน้าที่ 2: แดชบอร์ด และ วิเคราะห์ข้อมูล
# ==========================================
elif menu == "📊 แดชบอร์ด (วิเคราะห์ข้อมูล)":
    st.markdown("<h2 style='color: #212529; font-weight:700;'>📊 ศูนย์วิเคราะห์ข้อมูล (Analytics)</h2>", unsafe_allow_html=True)
    
    att_data = ws_attendance.get_all_records()
    if len(att_data) > 0:
        df_att = pd.DataFrame(att_data)
        
        # 🌟 แบ่งหน้าย่อย (Tabs) สำหรับดูภาพรวมรายวัน และ ดูเจาะจงรายบุคคล
        tab1, tab2 = st.tabs(["📅 สรุปรายวัน (ทั้งโรงเรียน / รายห้อง)", "👤 สรุปข้อมูลรายบุคคล"])
        
        # ----- หมวดย่อยที่ 1: ภาพรวมรายวัน -----
        with tab1:
            with st.container(border=True):
                st.markdown("<b>🔍 คัดกรองข้อมูล</b>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1: selected_date_dash = st.selectbox("เลือกวันที่", sorted(df_att['วันที่'].unique(), reverse=True))
                
                # เปลี่ยนให้ตัวเลือกแรกคือ "ดูข้อมูลทั้งโรงเรียน"
                all_classes = sorted(df_att['ชั้นเรียน'].unique().tolist())
                with col2: selected_class_dash = st.multiselect("เลือกชั้นเรียน (ปล่อยว่าง = ทั้งโรงเรียน)", all_classes, default=all_classes)

            # กรองข้อมูล
            if not selected_class_dash: # ถ้าปล่อยว่าง ให้เลือกทุกห้อง
                selected_class_dash = all_classes
            mask = (df_att['วันที่'] == selected_date_dash) & (df_att['ชั้นเรียน'].isin(selected_class_dash))
            df_filtered = df_att[mask]
            
            st.write("")
            if not df_filtered.empty:
                total_std = len(df_filtered)
                present = len(df_filtered[df_filtered['สถานะ'] == 'มาเรียน'])
                absent = len(df_filtered[df_filtered['สถานะ'] != 'มาเรียน'])
                percent = (present / total_std) * 100 if total_std > 0 else 0

                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f"""<div class="pluto-metric border-blue"><div class="metric-info"><h4>ยอดนักเรียน</h4><h2>{total_std}</h2></div><div class="pluto-icon">👥</div></div>""", unsafe_allow_html=True)
                with c2: st.markdown(f"""<div class="pluto-metric border-green"><div class="metric-info"><h4>มาเรียนปกติ</h4><h2>{present}</h2></div><div class="pluto-icon">✅</div></div>""", unsafe_allow_html=True)
                with c3: st.markdown(f"""<div class="pluto-metric border-red"><div class="metric-info"><h4>ลา/ขาด/สาย</h4><h2>{absent}</h2></div><div class="pluto-icon">⚠️</div></div>""", unsafe_allow_html=True)
                with c4: st.markdown(f"""<div class="pluto-metric border-yellow"><div class="metric-info"><h4>เปอร์เซ็นต์มาเรียน</h4><h2>{percent:.1f}%</h2></div><div class="pluto-icon">📈</div></div>""", unsafe_allow_html=True)

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

                with st.container(border=True):
                    col_tbl_head, col_btn = st.columns([7, 3])
                    with col_tbl_head: st.markdown("<b>📋 รายละเอียดข้อมูล</b>", unsafe_allow_html=True)
                    with col_btn:
                        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 โหลดไฟล์ CSV", data=csv, file_name=f'report_{selected_date_dash}.csv', use_container_width=True)
                    st.dataframe(df_filtered, hide_index=True, use_container_width=True)
            else:
                st.info("ไม่พบข้อมูลตามเงื่อนไขที่ค้นหาครับ")

        # ----- หมวดย่อยที่ 2: สรุปข้อมูลรายบุคคล -----
        with tab2:
            st.markdown("#### 👤 ค้นหาและดูสถิตินักเรียนรายบุคคล")
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1: ind_class = st.selectbox("เลือกชั้นเรียน:", sorted(df_att['ชั้นเรียน'].unique()))
                
                # กรองรายชื่อเด็กตามห้องที่เลือกเพื่อทำเป็นตัวเลือก
                student_list = df_att[df_att['ชั้นเรียน'] == ind_class]['ชื่อ'].unique().tolist()
                with c2: ind_student = st.selectbox("เลือกชื่อนักเรียน:", sorted(student_list))
            
            # กรองข้อมูลของเด็กคนนี้ทั้งหมด
            df_ind = df_att[(df_att['ชั้นเรียน'] == ind_class) & (df_att['ชื่อ'] == ind_student)]
            
            if not df_ind.empty:
                st.write("")
                total_days = len(df_ind)
                ind_present = len(df_ind[df_ind['สถานะ'] == 'มาเรียน'])
                ind_late = len(df_ind[df_ind['สถานะ'] == 'สาย'])
                ind_absent = len(df_ind[df_ind['สถานะ'].isin(['ลา', 'ป่วย', 'ขาด'])])
                ind_percent = (ind_present / total_days) * 100 if total_days > 0 else 0
                
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"""<div class="pluto-metric border-blue"><div class="metric-info"><h4>เช็คชื่อแล้ว (วัน)</h4><h2>{total_days}</h2></div></div>""", unsafe_allow_html=True)
                c2.markdown(f"""<div class="pluto-metric border-green"><div class="metric-info"><h4>มาเรียน / สาย</h4><h2>{ind_present} / {ind_late}</h2></div></div>""", unsafe_allow_html=True)
                c3.markdown(f"""<div class="pluto-metric border-red"><div class="metric-info"><h4>ลา / ป่วย / ขาด</h4><h2>{ind_absent}</h2></div></div>""", unsafe_allow_html=True)
                c4.markdown(f"""<div class="pluto-metric border-yellow"><div class="metric-info"><h4>ความสม่ำเสมอ</h4><h2>{ind_percent:.1f}%</h2></div></div>""", unsafe_allow_html=True)
                
                # แสดงประวัติการเข้าเรียนเป็นตารางเรียงตามวันที่
                st.markdown("<b>ประวัติการบันทึกย้อนหลัง</b>", unsafe_allow_html=True)
                st.dataframe(df_ind[['วันที่', 'สถานะ', 'ผู้บันทึก']].sort_values(by='วันที่', ascending=False), hide_index=True, use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลการบันทึกของนักเรียนท่านนี้ครับ")
                
    else:
        st.warning("ยังไม่มีข้อมูลการเช็คชื่อในระบบเลยครับ")

# ==========================================
# ⚙️ หน้าที่ 3: ตั้งค่าระบบ (Admin)
# ==========================================
elif menu == "⚙️ ตั้งค่าระบบ (Admin)":
    st.markdown("<h2 style='color: #212529; font-weight:700;'>⚙️ ตั้งค่าระบบส่วนกลาง (Admin)</h2>", unsafe_allow_html=True)
    st.markdown("หน้านี้สำหรับผู้ดูแลระบบ เพื่อกำหนดกรอบเวลาในการบันทึกข้อมูลของโรงเรียนครับ")
    
    with st.container(border=True):
        st.markdown("#### 📅 กำหนดช่วงเวลาที่อนุญาตให้เช็คชื่อ (เปิด-ปิดเทอม)")
        
        c1, c2 = st.columns(2)
        with c1: new_start = st.date_input("วันเริ่มต้นการบันทึก (Start Date)", term_start)
        with c2: new_end = st.date_input("วันสิ้นสุดการบันทึก (End Date)", term_end)
        
        st.markdown("<hr style='border-top:1px dashed #ccc;'>", unsafe_allow_html=True)
        
        if st.button("💾 บันทึกการตั้งค่าระบบ", type="primary"):
            try:
                # อัปเดตข้อมูลใน Google Sheets
                cell_start = ws_settings.find("StartDate")
                ws_settings.update_cell(cell_start.row, cell_start.col + 1, new_start.strftime("%Y-%m-%d"))
                
                cell_end = ws_settings.find("EndDate")
                ws_settings.update_cell(cell_end.row, cell_end.col + 1, new_end.strftime("%Y-%m-%d"))
                
                st.success("✅ อัปเดตช่วงเวลาเปิด-ปิดเทอมเรียบร้อยแล้ว! (ระบบจะรีเฟรชหน้าจอใน 2 วินาที)")
                st.rerun()
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดในการบันทึก: {e}")
