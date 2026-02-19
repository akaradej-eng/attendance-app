import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import gspread
import json
from datetime import datetime, date
import plotly.express as px
import qrcode
from io import BytesIO
import base64

st.set_page_config(page_title="ระบบบริหารจัดการ โรงเรียนบ้านเชียงวิทยา", layout="wide", page_icon="🏫")

# 🔗 1. ฟังก์ชันเชื่อมต่อฐานข้อมูล
@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_sheet"]["credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open("ระบบเช็คชื่อนักเรียน")
    ws_stud = sh.worksheet("Students")
    ws_att = sh.worksheet("Attendance")
    try:
        ws_set = sh.worksheet("Settings")
    except gspread.exceptions.WorksheetNotFound:
        ws_set = sh.add_worksheet(title="Settings", rows=10, cols=2)
        ws_set.append_row(["Key", "Value"])
        ws_set.append_row(["StartDate", "2024-05-01"])
        ws_set.append_row(["EndDate", "2025-03-31"])
    return sh, ws_stud, ws_att, ws_set

sh, ws_students, ws_attendance, ws_settings = init_connection()

set_data = ws_settings.get_all_records()
settings_dict = {str(row['Key']): str(row['Value']) for row in set_data}
try:
    term_start = datetime.strptime(settings_dict.get('StartDate', '2024-05-01'), "%Y-%m-%d").date()
    term_end = datetime.strptime(settings_dict.get('EndDate', '2025-03-31'), "%Y-%m-%d").date()
except:
    term_start, term_end = date(2024, 5, 1), date(2025, 3, 31)

def generate_qr_base64(data):
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e56a0", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# 🎨 2. CSS สไตล์ Pluto Theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Prompt', sans-serif; }
    .stApp { background-color: #f4f7f6; }
    #MainMenu, footer, header {visibility: hidden;}
    .pluto-metric { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between;}
    .pluto-metric h4 { margin: 0; font-size: 14px; color: #8a909d; font-weight: 500; }
    .pluto-metric h2 { margin: 5px 0 0 0; font-size: 28px; color: #212529; font-weight: 700; }
    .pluto-icon { font-size: 35px; }
    .border-blue { border-left: 5px solid #17a2b8; }
    .border-green { border-left: 5px solid #28a745; }
    .border-red { border-left: 5px solid #dc3545; }
    .border-yellow { border-left: 5px solid #ffc107; }
    div[data-baseweb="select"] { border-radius: 8px; }
    .stSelectbox label { display: none; }
    .id-card { background-color: white; width: 300px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden; margin: 10px auto; border: 1px solid #e0e0e0; text-align: center; }
    .id-card-header { background-color: #1e56a0; color: white; padding: 15px 10px; font-weight: 600; font-size: 16px; }
    .id-card-body { padding: 20px; }
    .id-card img.avatar { width: 100px; height: 100px; border-radius: 50%; border: 3px solid #1e56a0; object-fit: cover; margin-bottom: 10px;}
    .id-card img.qr { width: 120px; margin-top: 10px;}
    .id-name { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 5px;}
    .id-detail { font-size: 14px; color: #666; }
    
    .scan-result-card {
        display: flex; align-items: center; background: #f0fdf4; padding: 20px; 
        border-radius: 12px; border-left: 8px solid #28a745; box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 15px;
    }
    .scan-result-card.warning { background: #fffbeb; border-left: 8px solid #ffc107; }
    .scan-result-card img { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-right: 20px; border: 3px solid #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    .scan-result-info h3 { margin: 0 0 5px 0; font-size: 22px; color: #1f2937; font-weight: 700;}
    .scan-result-info p.id-text { margin: 0; font-size: 16px; color: #4b5563; }
    .scan-result-info p.status-text { margin: 0 0 5px 0; font-size: 18px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 📱 3. สร้างแถบเมนูด้านข้าง
with st.sidebar:
    st.markdown("### 🏫 ระบบโรงเรียน")
    st.markdown("บ้านเชียงวิทยา")
    st.markdown("---")
    menu = st.radio("📌 เลือกหน้าต่างการทำงาน:", ["📝 บันทึกลงเวลา", "📊 แดชบอร์ด (วิเคราะห์ข้อมูล)", "⚙️ ตั้งค่าระบบ (Admin)"])
    st.markdown("---")
    st.info(f"📅 รอบการบันทึก:\n{term_start.strftime('%d/%m/%Y')} ถึง {term_end.strftime('%d/%m/%Y')}")

# ==========================================
# 🟢 หน้าที่ 1: บันทึกลงเวลา (สแกนปุ๊บ บันทึกปั๊บ)
# ==========================================
if menu == "📝 บันทึกลงเวลา":
    # เตรียมหน่วยความจำให้พร้อมเสมอ
    if 'scan_msg' not in st.session_state: st.session_state.scan_msg = ""
    if 'scan_status' not in st.session_state: st.session_state.scan_status = "info"
    if 'last_scanned' not in st.session_state: st.session_state.last_scanned = None
    if 'saved_today' not in st.session_state: st.session_state.saved_today = set()

    st.markdown("<h2 style='color: #212529; font-weight:700;'>📝 บันทึกลงเวลาเรียน</h2>", unsafe_allow_html=True)
    
    data_all_students = ws_students.get_all_records()

    if len(data_all_students) > 0:
        df_students = pd.DataFrame(data_all_students)
        class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())

        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1: selected_class = st.selectbox("📅 ชั้นเรียน", class_list)
            with c2: check_date = st.date_input("วันที่", datetime.today())
            
            room_info = df_students[df_students['ชั้นเรียน'] == selected_class].iloc[0]
            teachers = [t for t in [room_info.get('ครูที่ปรึกษา 1'), room_info.get('ครูที่ปรึกษา 2'), room_info.get('ครูที่ปรึกษา 3')] if t]
            recorded_by = st.radio("👤 ผู้บันทึก:", teachers, horizontal=True)

        df_room = df_students[df_students['ชั้นเรียน'] == selected_class].copy()
        df_room['รหัสนักเรียน'] = df_room['รหัสนักเรียน'].astype(str).str.strip()
        date_str = check_date.strftime("%d/%m/%Y")

        if not (term_start <= check_date <= term_end):
            st.error(f"⛔ ไม่สามารถบันทึกข้อมูลได้! วันที่ {date_str} อยู่นอกเหนือรอบการบันทึก")
        else:
            # ระบบดึงความจำอัจฉริยะ 
            class_date_key = f"{selected_class}_{date_str}"
            if st.session_state.get('current_class_date') != class_date_key:
                st.session_state.current_class_date = class_date_key
                st.session_state.att_data = {str(r['รหัสนักเรียน']): "ขาด" for _, r in df_room.iterrows()}
                st.session_state.saved_today = set()
                st.session_state.scan_msg = ""
                st.session_state.last_scanned = None 
                
                # โหลดข้อมูลเก่าของวันนี้
                all_attendance = ws_attendance.get_all_records()
                if all_attendance:
                    df_att_check = pd.DataFrame(all_attendance)
                    df_att_check['รหัสนักเรียน'] = df_att_check['รหัสนักเรียน'].astype(str).str.strip()
                    today_records = df_att_check[(df_att_check['วันที่'] == date_str) & (df_att_check['ชั้นเรียน'] == selected_class)]
                    for _, row in today_records.iterrows():
                        sid = str(row['รหัสนักเรียน'])
                        st.session_state.att_data[sid] = row['สถานะ']
                        st.session_state.saved_today.add(sid) 

            # 🌟 ฟังก์ชันจัดการข้อมูลเมื่อแสกนสำเร็จ (ถูกเรียกใช้เมื่อมีข้อความเข้าช่อง text_input)
            def handle_scan():
                scanned = st.session_state.scanner_input.strip()
                if not scanned: return

                student_match = df_room[df_room['รหัสนักเรียน'] == scanned]
                
                if not student_match.empty:
                    student_info = student_match.iloc[0]
                    name = str(student_info.get('ชื่อ', 'ไม่ทราบชื่อ'))
                    img_url = str(student_info.get('รูปภาพ', '')).strip()
                    if not img_url or img_url.lower() == 'nan':
                        img_url = f"https://ui-avatars.com/api/?name={name}&background=1e56a0&color=fff&rounded=true&size=128"

                    if scanned in st.session_state.saved_today:
                        st.session_state.scan_status = "warning"
                        st.session_state.scan_msg = "บันทึกแล้ว (สแกนซ้ำ)"
                    else:
                        st.session_state.att_data[scanned] = "มาเรียน"
                        st.session_state.scan_status = "success"
                        st.session_state.scan_msg = "มาโรงเรียนแล้ว"
                        
                        # บันทึกลง Google Sheets ทันที
                        row_data = [date_str, scanned, name, selected_class, "มาเรียน", recorded_by]
                        try:
                            ws_attendance.append_row(row_data)
                            try:
                                ws_class = sh.worksheet(selected_class)
                            except gspread.exceptions.WorksheetNotFound:
                                ws_class = sh.add_worksheet(title=selected_class, rows=100, cols=6)
                                ws_class.append_row(["วันที่", "รหัสนักเรียน", "ชื่อ", "ชั้นเรียน", "สถานะ", "ผู้บันทึก"])
                            ws_class.append_row(row_data)
                            st.session_state.saved_today.add(scanned)
                        except Exception as e:
                            st.session_state.scan_status = "error"
                            st.session_state.scan_msg = f"เซฟลงชีตไม่สำเร็จ: {e}"

                    st.session_state.last_scanned = {
                        "id": scanned, "name": name, "img": img_url, 
                        "status": st.session_state.scan_status, "msg": st.session_state.scan_msg
                    }
                else:
                    st.session_state.scan_status = "error"
                    st.session_state.scan_msg = f"ไม่พบรหัส {scanned} ในห้อง {selected_class}"
                    st.session_state.last_scanned = None
                
                # เคลียร์ช่องรับข้อมูลเตรียมรอคนต่อไป
                st.session_state.scanner_input = ""

            # ==========================================
            # 📸 ส่วนที่ 1: ระบบกล้อง (สแกนปุ๊บ บันทึกปั๊บ ทันที!)
            # ==========================================
            st.markdown("---")
            col_toggle, col_empty = st.columns([1, 1])
            with col_toggle:
                use_camera = st.toggle("📷 เปิดสวิตช์กล้องสแกน QR Code", value=False)
            
            if use_camera:
                with st.container(border=True):
                    st.caption("ส่อง QR Code ที่กล้อง ระบบจะเช็คชื่อและ **บันทึกลง Google Sheets ทันที**")
                    
                    # 🌟 ใช้ฟังก์ชัน Callback (on_change) เพื่อบังคับให้ Streamlit ทำงานทันที
                    st.text_input("scan_target", key="scanner_input", label_visibility="collapsed", placeholder="ช่องรับรหัสอัตโนมัติ", on_change=handle_scan)

                    # --- โชว์ป๊อปอัปบัตรนักเรียนหลังจากการสแกน ---
                    if st.session_state.last_scanned:
                        ls = st.session_state.last_scanned
                        card_class = "warning" if ls['status'] == "warning" else ""
                        icon = "⚠️" if ls['status'] == "warning" else "✅"
                        color = "#d97706" if ls['status'] == "warning" else "#16a34a"

                        st.markdown(f"""
                        <div class="scan-result-card {card_class}">
                            <img src="{ls['img']}">
                            <div class="scan-result-info">
                                <p class="status-text" style="color: {color};">{icon} {ls['msg']}</p>
                                <h3>{ls['name']}</h3>
                                <p class="id-text">รหัสประจำตัว: <b>{ls['id']}</b></p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif st.session_state.scan_status == "error":
                        st.error(f"❌ {st.session_state.scan_msg}")

                    # 🌟 Javascript กล้องสแกนแบบบังคับกด Enter ขั้นสุด
                    components.html(
                        """
                        <div id="reader" style="width: 100%; border-radius: 10px; overflow: hidden; border: 2px solid #eef2f5;"></div>
                        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
                        <script>
                        function onScanSuccess(decodedText, decodedResult) {
                            const parentDoc = window.parent.document;
                            // หาช่อง Streamlit โดยการอ้างอิงจาก Placeholder
                            const inputField = parentDoc.querySelector('input[placeholder="ช่องรับรหัสอัตโนมัติ"]');
                            
                            if(inputField) {
                                let lastScanned = sessionStorage.getItem("lastScanned");
                                let lastTime = sessionStorage.getItem("lastTime");
                                let now = Date.now();
                                
                                // ป้องกันการสแกนซ้ำติดๆ กันใน 3 วินาที (จากกล้อง)
                                if(lastScanned === decodedText && (now - lastTime) < 3000) { return; }
                                sessionStorage.setItem("lastScanned", decodedText);
                                sessionStorage.setItem("lastTime", now);
                                
                                // ยัดค่ารหัสเข้าไปในช่อง
                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                nativeInputValueSetter.call(inputField, decodedText);
                                
                                // สั่ง Event กระตุ้นให้ Streamlit รู้ตัว
                                inputField.dispatchEvent(new Event('input', { bubbles: true }));
                                inputField.dispatchEvent(new Event('change', { bubbles: true }));
                                
                                // บังคับกดปุ่ม Enter
                                const enterEvent = new KeyboardEvent('keydown', {
                                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                                });
                                inputField.dispatchEvent(enterEvent);
                            }
                        }
                        function onScanFailure(error) { }
                        let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 15, qrbox: {width: 250, height: 250}, videoConstraints: { facingMode: "environment" } }, false);
                        html5QrcodeScanner.render(onScanSuccess, onScanFailure);
                        </script>
                        """, height=350,
                    )

            # ==========================================
            # 📋 ส่วนที่ 2: ระบบรายชื่อแบบเดิม 
            # ==========================================
            st.markdown("---")
            st.markdown("### 📋 ตรวจสอบรายชื่อทั้งหมด")
            
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

                bg_color = "#e8f5e9" if st.session_state.att_data.get(sid) == "มาเรียน" else "#ffffff"

                st.markdown(f"<div style='background-color:{bg_color}; padding:10px; border-radius:10px; border:1px solid #e2e8f0; margin-bottom:8px;'>", unsafe_allow_html=True)
                col_img, col_info, col_status = st.columns([1.5, 5, 3.5])
                with col_img: st.image(img_url, width=50) 
                with col_info: st.markdown(f"<div style='padding-top:2px;'><b>{index+1}. {name}</b><br><span style='color:#8a909d; font-size:12px;'>รหัส: {sid}</span></div>", unsafe_allow_html=True)
                with col_status:
                    current_val = st.session_state.att_data.get(sid, "ขาด")
                    new_status = st.selectbox("สถานะ", status_options, key=f"sel_{sid}", label_visibility="collapsed", index=status_options.index(current_val))
                    if new_status != current_val:
                        st.session_state.att_data[sid] = new_status
                        if new_status == "ขาด" and sid in st.session_state.saved_today:
                            st.session_state.saved_today.remove(sid)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            st.write("")
            st.info("💡 เมื่อสแกนเสร็จครบทุกคนแล้ว ให้กดปุ่มด้านล่างเพื่อบันทึกคนที่เหลือเป็น 'ขาดเรียน'")
            
            if st.button("🚀 บันทึกคนยังไม่สแกน เป็น 'ขาดเรียน/ลา' เข้าชีต", type="primary", use_container_width=True):
                try:
                    final_records = []
                    for _, r in df_room.iterrows():
                        sid = str(r['รหัสนักเรียน'])
                        if sid not in st.session_state.saved_today:
                            status = st.session_state.att_data.get(sid, "ขาด")
                            final_records.append([date_str, sid, r.get('ชื่อ',''), r.get('ชั้นเรียน',''), status, recorded_by])
                            st.session_state.saved_today.add(sid)
                            
                    if final_records:
                        ws_attendance.append_rows(final_records)
                        try:
                            ws_class = sh.worksheet(selected_class)
                        except gspread.exceptions.WorksheetNotFound:
                            ws_class = sh.add_worksheet(title=selected_class, rows=100, cols=6)
                            ws_class.append_row(["วันที่", "รหัสนักเรียน", "ชื่อ", "ชั้นเรียน", "สถานะ", "ผู้บันทึก"])
                        ws_class.append_rows(final_records)
                        st.success(f"✅ บันทึกรายชื่อคนที่เหลือสำเร็จเรียบร้อย!")
                        st.balloons()
                    else:
                        st.warning("⚠️ ไม่มีรายชื่อใหม่ให้บันทึก (ทุกคนในห้องนี้ถูกบันทึกไปหมดแล้วครับ)")
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# ==========================================
# 📊 หน้าที่ 2: แดชบอร์ด (วิเคราะห์ข้อมูล)
# ==========================================
elif menu == "📊 แดชบอร์ด (วิเคราะห์ข้อมูล)":
    st.markdown("<h2 style='color: #212529; font-weight:700;'>📊 ศูนย์วิเคราะห์ข้อมูล (Analytics)</h2>", unsafe_allow_html=True)
    df_all_students = pd.DataFrame(ws_students.get_all_records())
    att_data = ws_attendance.get_all_records()
    
    if len(att_data) > 0 and not df_all_students.empty:
        df_att = pd.DataFrame(att_data)
        tab1, tab2 = st.tabs(["📅 สรุปรายวัน", "👤 สรุปรายบุคคล"])
        
        with tab1:
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1: selected_date_dash = st.selectbox("เลือกวันที่", sorted(df_att['วันที่'].unique(), reverse=True))
                all_classes = sorted(df_all_students['ชั้นเรียน'].unique().tolist())
                with col2: selected_class_dash = st.multiselect("เลือกชั้นเรียน (ปล่อยว่าง = ทั้งโรงเรียน)", all_classes, default=all_classes)

            if not selected_class_dash: selected_class_dash = all_classes
            total_std = len(df_all_students[df_all_students['ชั้นเรียน'].isin(selected_class_dash)])
            
            mask = (df_att['วันที่'] == selected_date_dash) & (df_att['ชั้นเรียน'].isin(selected_class_dash))
            df_filtered = df_att[mask]
            
            present = len(df_filtered[df_filtered['สถานะ'] == 'มาเรียน'])
            late = len(df_filtered[df_filtered['สถานะ'] == 'สาย'])
            leave = len(df_filtered[df_filtered['สถานะ'].isin(['ลา', 'ป่วย'])])
            
            absent = total_std - present - late - leave
            if absent < 0: absent = 0
            percent = (present / total_std) * 100 if total_std > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"""<div class="pluto-metric border-blue"><div class="metric-info"><h4>ยอดนักเรียน</h4><h2>{total_std}</h2></div></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="pluto-metric border-green"><div class="metric-info"><h4>มาเรียน</h4><h2>{present}</h2></div></div>""", unsafe_allow_html=True)
            with c3: st.markdown(f"""<div class="pluto-metric border-red"><div class="metric-info"><h4>ลา/ขาด/สาย</h4><h2>{absent + late + leave}</h2></div></div>""", unsafe_allow_html=True)
            with c4: st.markdown(f"""<div class="pluto-metric border-yellow"><div class="metric-info"><h4>เปอร์เซ็นต์</h4><h2>{percent:.1f}%</h2></div></div>""", unsafe_allow_html=True)

            st.markdown("<b>ข้อมูลที่บันทึกแล้วในระบบ</b>", unsafe_allow_html=True)
            st.dataframe(df_filtered, hide_index=True, use_container_width=True)

        with tab2:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1: ind_class = st.selectbox("เลือกชั้นเรียน:", sorted(df_all_students['ชั้นเรียน'].unique()))
                student_list = df_all_students[df_all_students['ชั้นเรียน'] == ind_class]['ชื่อ'].unique().tolist()
                with c2: ind_student = st.selectbox("เลือกชื่อนักเรียน:", sorted(student_list))
            
            df_ind = df_att[(df_att['ชั้นเรียน'] == ind_class) & (df_att['ชื่อ'] == ind_student)]
            if not df_ind.empty:
                st.dataframe(df_ind[['วันที่', 'สถานะ', 'ผู้บันทึก']].sort_values(by='วันที่', ascending=False), hide_index=True, use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลการบันทึกของนักเรียนท่านนี้")
    else:
        st.warning("ยังไม่มีข้อมูลในระบบ หรือ ชีต Students ว่างเปล่า")

# ==========================================
# ⚙️ หน้าที่ 3: ตั้งค่าระบบ (Admin)
# ==========================================
elif menu == "⚙️ ตั้งค่าระบบ (Admin)":
    st.markdown("<h2 style='color: #212529; font-weight:700;'>⚙️ ผู้ดูแลระบบ (Admin Panel)</h2>", unsafe_allow_html=True)
    
    tab_admin1, tab_admin2 = st.tabs(["📅 ตั้งค่าเปิด-ปิดเทอม", "🪪 สร้างบัตรประจำตัว (QR Code)"])
    
    with tab_admin1:
        with st.container(border=True):
            st.markdown("#### กำหนดช่วงเวลาที่อนุญาตให้เช็คชื่อ")
            c1, c2 = st.columns(2)
            with c1: new_start = st.date_input("วันเริ่มต้น (Start Date)", term_start)
            with c2: new_end = st.date_input("วันสิ้นสุด (End Date)", term_end)
            
            if st.button("💾 บันทึกการตั้งค่าระบบ", type="primary"):
                try:
                    cell_start = ws_settings.find("StartDate")
                    ws_settings.update_cell(cell_start.row, cell_start.col + 1, new_start.strftime("%Y-%m-%d"))
                    cell_end = ws_settings.find("EndDate")
                    ws_settings.update_cell(cell_end.row, cell_end.col + 1, new_end.strftime("%Y-%m-%d"))
                    st.success("✅ อัปเดตช่วงเวลาเรียบร้อยแล้ว!")
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")

    with tab_admin2:
        st.markdown("#### 🪪 สร้างบัตรประจำตัวนักเรียนพร้อม QR Code")
        data = ws_students.get_all_records()
        if len(data) > 0:
            df_students = pd.DataFrame(data)
            class_list = sorted(df_students['ชั้นเรียน'].unique().tolist())
            
            selected_id_class = st.selectbox("📌 เลือกชั้นเรียนที่ต้องการพิมพ์บัตร", class_list)
            df_id_room = df_students[df_students['ชั้นเรียน'] == selected_id_class]
            
            st.markdown("---")
            cols = st.columns(3)
            col_idx = 0
            
            for index, row in df_id_room.iterrows():
                sid = str(row['รหัสนักเรียน'])
                name = str(row.get('ชื่อ', ''))
                img_url = str(row.get('รูปภาพ', '')).strip()
                if not img_url or img_url.lower() == 'nan':
                    img_url = f"https://ui-avatars.com/api/?name={name}&background=1e56a0&color=fff&rounded=true&size=128"
                
                qr_base64 = generate_qr_base64(sid)
                
                with cols[col_idx % 3]:
                    st.markdown(f"""
                    <div class="id-card">
                        <div class="id-card-header">โรงเรียนบ้านเชียงวิทยา</div>
                        <div class="id-card-body">
                            <img src="{img_url}" class="avatar">
                            <div class="id-name">{name}</div>
                            <div class="id-detail">ชั้น {selected_id_class} | รหัส: {sid}</div>
                            <img src="data:image/png;base64,{qr_base64}" class="qr">
                            <div style="font-size:10px; color:#999; margin-top:5px;">สแกนเพื่อเช็คชื่อ</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                col_idx += 1
