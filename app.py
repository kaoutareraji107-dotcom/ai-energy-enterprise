import streamlit as st
import datetime
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from streamlit_folium import st_folium
import folium
import sqlite3
import hashlib

# استيراد المحرك المطور (كودك الأصلي)
from engine import SmartCityStrategic, CityZone

# ================= 1. DATABASE + LOGIN =================
@st.cache_resource
def init_db():
    conn = sqlite3.connect('enterprise_users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, 
                  company TEXT, is_pro INTEGER DEFAULT 0, 
                  analysis_count INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

init_db()

# ================= 2. LOGIN SYSTEM =================
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.is_pro = False
    st.session_state.analysis_count = 0

def check_login():
    if st.session_state.user:
        return True
    
    st.title("⚡ AI Energy Enterprise v2.0")
    st.subheader("Professional Infrastructure Management System")
    
    tab1, tab2 = st.tabs(["دخول", "حساب جديد"])
    
    with tab1:
        with st.form("login"):
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة السر", type="password")
            if st.form_submit_button("دخول"):
                conn = sqlite3.connect('enterprise_users.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?",
                         (username, hash_password(password)))
                user_data = c.fetchone()
                conn.close()
                
                if user_data:
                    st.session_state.user = {"username": username, "company": user_data[2]}
                    st.session_state.is_pro = bool(user_data[3])
                    st.session_state.analysis_count = user_data[4]
                    st.success("✅ تم تسجيل الدخول!")
                    st.rerun()
                else:
                    st.error("❌ خطأ في اسم المستخدم أو كلمة السر!")
    
    with tab2:
        with st.form("signup"):
            new_username = st.text_input("اسم مستخدم جديد")
            new_password = st.text_input("كلمة سر", type="password")
            company = st.text_input("اسم الشركة")
            if st.form_submit_button("إنشاء حساب"):
                try:
                    conn = sqlite3.connect('enterprise_users.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, password, company) VALUES (?, ?, ?)",
                             (new_username, hash_password(new_password), company))
                    conn.commit()
                    conn.close()
                    st.success("✅ تم إنشاء الحساب! الآن قم بتسجيل الدخول.")
                except:
                    st.error("❌ اسم مستخدم موجود بالفعل!")
    
    st.stop()

# ================= 3. CONFIG & STYLE (كودك الأصلي) =================
st.set_page_config(page_title="AI Energy Enterprise v2.0", layout="wide")
check_login()  # التحقق من تسجيل الدخول

st.markdown("""
<style>
    .main { background: #050816; color: white; }
    .stMetric { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; border: 1px solid #00FF9C; }
    .card-stat { padding: 20px; border-radius: 20px; text-align: center;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,156,0.2); }
    h1, h2, h3 { color: #00FF9C !important; }
    .pro-badge { background: #FFD700; color: #000; padding: 5px 10px; border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ================= 4. INITIALIZE SYSTEM (كودك الأصلي + تحسين) =================
if "system" not in st.session_state:
    st.session_state.system = SmartCityStrategic()
    st.session_state.user_data = st.session_state.user

# ================= 5. SIDEBAR PRO STATUS =================
st.sidebar.title(f"👤 {st.session_state.user['username']}")
st.sidebar.markdown(f"🏢 {st.session_state.user_data['company']}")

if st.session_state.is_pro:
    st.sidebar.markdown('<div class="pro-badge">⭐ PRO</div>', unsafe_allow_html=True)
    st.sidebar.success("تحليلات غير محدودة + تقارير متقدمة")
else:
    st.sidebar.warning(f"تحليلات متبقية: {5 - st.session_state.analysis_count}/5")
    if st.sidebar.button("⭐ ترقية Pro (99$/سنة)"):
        st.info("🚀 سيتم إعداد الدفع قريباً! تواصل: support@aienergy.com")

# ================= 6. MAIN DASHBOARD (كودك الأصلي محسن) =================
sys = st.session_state.system
user = st.session_state.user_data

# محاكاة الوقت والطقس
hour = st.sidebar.slider("🕐 الساعة", 0, 23, datetime.datetime.now().hour)
clouds = st.sidebar.slider("☁️ تغطية السحب (0-10)", 0, 10, 2)

# تحديث عدد التحليلات للحسابات المجانية
if not st.session_state.is_pro:
    st.session_state.analysis_count += 1
    if st.session_state.analysis_count >= 5:
        st.error("❌ وصلت للحد الأقصى! قم بالترقية إلى Pro")
        st.stop()

# معالجة البيانات (كودك الأصلي)
res = sys.control_center(hour, 25, clouds)

# HEADER
st.title(f"🏢 {user['company']} - لوحة التحكم الذكية")
st.metric("الحالة", "✅ AI محسن", delta="Real-time")

# KPIs (كودك الأصلي محسن)
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("☀️ إنتاج الطاقة الشمسية", f"{res['solar']} kW", f"{res['efficiency']}%")
with m2:
    st.metric("⚡ الحمل الفعلي", f"{res['load']} kW", "-15% توفير AI")
with m3:
    st.metric("💰 التوفير المالي", f"${res['money_saved']}", "يومياً")
with m4:
    st.metric("🌿 CO2 محفوظ", f"{res['co2_saved']} kg", "صديق البيئة")

# بطارية (كودك الأصلي)
st.markdown("### 🔋 حالة البطارية الذكية")
b_color = "#00FF9C" if res['battery'] > 40 else "#FF9500" if res['battery'] > 20 else "#FF4B4B"
st.markdown(f"""
    <div style="width:100%; height:40px; background:#222; border-radius:15px; overflow:hidden;">
        <div style="width:{res['battery']}%; height:40px; background:{b_color}; 
                    border-radius:15px; display:flex; align-items:center; justify-content:center; font-weight:bold;">
            {res['battery']}%
        </div>
    </div>
""", unsafe_allow_html=True)

# الرسوم البيانية + المناطق (كودك الأصلي)
col_left, col_right = st.columns([2, 1])

with col_left:
    st.write("### 📈 التحليلات الحية")
    chart_data = pd.DataFrame({
        'الوقت': pd.date_range(start='today', periods=24, freq='H'),
        'الطاقة الشمسية': [res['solar'] * (math.sin(i/24*3.14)) for i in range(24)],
        'الحمل': [res['load']] * 24
    })
    fig = px.line(chart_data, x='الوقت', y=['الطاقة الشمسية', 'الحمل'], 
                  title="24 ساعة قادمة", markers=True)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.write("### 🏭 قرارات المناطق الذكية")
    for zone, status in res['decisions'].items():
        color = "#00FF9C" if "ON" in status else "#FF4B4B"
        st.markdown(f"""
            <div style="padding:12px; margin:5px 0; background:rgba(0,255,156,0.1); 
                        border-radius:10px; border-left:4px solid {color}">
                <b>{zone}</b><br><small style="color:{color}">{status}</small>
            </div>
        """, unsafe_allow_html=True)

# شرح AI
with st.expander("🤖 شرح قرارات الذكاء الاصطناعي"):
    for zone, status in res['decisions'].items():
        st.info(sys.explain_decision(zone, status, res['battery']))

# PDF Report (كودك الأصلي محسن)
def generate_enterprise_pdf(user, res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 255, 156)
    pdf.cell(0, 15, f"AI ENERGY ENTERPRISE REPORT", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"{user['company']}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"التوفير: ${res['money_saved']}", ln=True)
    pdf.cell(0, 10, f"كفاءة النظام: {res['efficiency']}%", ln=True)
    pdf.cell(0, 10, f"CO2 محفوظ: {res['co2_saved']} كجم", ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

if st.button("📄 تحميل تقرير PDF الاحترافي", use_container_width=True):
    pdf_bytes = generate_enterprise_pdf(user, res)
    st.download_button("⬇️ تحميل التقرير", pdf_bytes, 
                      file_name=f"{user['company']}_energy_report.pdf", use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
**✨ AI Energy Enterprise** | للشركات المتوسطة والكبيرة | 
تواصل: support@aienergyenterprise.com | Pro: غير محدود
""")

st.toast("تم تحديث البيانات بنجاح! ✅", icon="⚡")
