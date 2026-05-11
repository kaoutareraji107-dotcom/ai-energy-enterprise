import streamlit as st
import datetime
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from streamlit_folium import st_folium
import folium

# استيراد المحرك المطور
from engine import SmartCityStrategic, CityZone

# ================= 1. CONFIGURATION & STYLE =================
st.set_page_config(page_title="AI Energy Enterprise v2.0", layout="wide")

st.markdown("""
<style>
    .main { background: #050816; color: white; }
    .stMetric { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; border: 1px solid #00FF9C; }
    .card-stat { 
        padding: 20px; border-radius: 20px; text-align: center;
        background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,156,0.2);
    }
    h1, h2, h3 { color: #00FF9C !important; }
</style>
""", unsafe_allow_html=True)

# ================= 2. SESSION STATE =================
if "system" not in st.session_state:
    st.session_state.system = SmartCityStrategic()
if "user" not in st.session_state:
    st.session_state.user = None

# ================= 3. HELPERS =================
def generate_enterprise_pdf(user, res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"ENTERPRISE ENERGY REPORT: {user['company'].upper()}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Location: {user['city']}, {user['country']}", ln=True)
    pdf.ln(5)
    
    # Financials
    pdf.set_text_color(0, 150, 0)
    pdf.cell(0, 10, f"Total ROI (Money Saved): {res['money_saved']} MAD/USD", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(0, 10, f"Solar Production: {res['solar']} kW", ln=True)
    pdf.cell(0, 10, f"System Efficiency: {res['efficiency']}%", ln=True)
    pdf.cell(0, 10, f"CO2 Reduction: {res['co2_saved']} kg", ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# ================= 4. LOGIN INTERFACE =================
if st.session_state.user is None:
    st.title("⚡ AI Energy Enterprise")
    st.subheader("Professional Infrastructure Management System")
    
    with st.form("enterprise_login"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Manager Name")
            company = st.text_input("Enterprise Name (e.g. Tesla Factory)")
        with col2:
            city = st.text_input("City")
            country = st.text_input("Country")
        
        biz_type = st.selectbox("Industry Type", ["Manufacturing", "Healthcare", "Data Center", "Retail"])
        submit = st.form_submit_button("Initialize Enterprise Dashboard")
        
        if submit:
            st.session_state.user = {"name": name, "company": company, "city": city, "country": country}
            # إضافة مناطق بناءً على نوع الصناعة
            if biz_type == "Manufacturing":
                st.session_state.system.add_zone(CityZone("Main Production Line", 1, 1200))
                st.session_state.system.add_zone(CityZone("Warehouse Cooling", 2, 600))
                st.session_state.system.add_zone(CityZone("Office HVAC", 3, 300))
            else:
                st.session_state.system.add_zone(CityZone("Critical Servers", 1, 800))
                st.session_state.system.add_zone(CityZone("Standard Lighting", 3, 200))
            st.rerun()
    st.stop()

# ================= 5. MAIN DASHBOARD =================
sys = st.session_state.system
user = st.session_state.user

# محاكاة الوقت والطقس
hour = st.sidebar.slider("Simulation Hour", 0, 23, datetime.datetime.now().hour)
clouds = st.sidebar.slider("Cloud Coverage (0-10)", 0, 10, 2)

# معالجة البيانات من الـ Engine
res = sys.control_center(hour, 25, clouds)

# --- HEADER ---
st.title(f"🏢 {user['company']} Dashboard")
st.write(f"Welcome, **{user['name']}** | Status: <span style='color:#00FF9C'>AI-Optimized</span>", unsafe_allow_html=True)

# --- KPI METRICS (Enterprise Standard) ---
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Solar Production", f"{res['solar']} kW", delta=f"{res['efficiency']}% Eff.")
with m2:
    st.metric("Active Load", f"{res['load']} kW", delta="-12% AI Reduced", delta_color="normal")
with m3:
    # ROI التحليل المالي
    st.metric("Financial ROI", f"${res['money_saved']}", delta="Daily Savings", delta_color="normal")
with m4:
    st.metric("CO2 Saved", f"{res['co2_saved']} kg", delta="🌿 Eco-Mode")

# --- BATTERY INTELLIGENCE (Visual) ---
st.write("### 🔋 Battery Intelligence System")
b_color = "green" if res['battery'] > 40 else "orange" if res['battery'] > 20 else "red"
st.markdown(f"""
    <div style="width:100%; background:#222; border-radius:10px; height:30px;">
        <div style="width:{res['battery']}%; background:{b_color}; height:30px; border-radius:10px; text-align:center;">
            <b>{res['battery']}%</b>
        </div>
    </div>
""", unsafe_allow_html=True)



# --- LIVE ANALYTICS & SMART ZONES ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.write("### 📈 Live Performance Analytics")
    # محاكاة بيانات الرسم البياني
    chart_data = pd.DataFrame({
        'Time': pd.date_range(start='2023-01-01', periods=10, freq='h'),
        'Solar': [res['solar']*0.8, res['solar']*0.9, res['solar'], res['solar']*1.1, res['solar']*0.7, 0, 0, 0, 0, 0],
        'Load': [res['load']]*10
    })
    fig = px.area(chart_data, x='Time', y=['Solar', 'Load'], color_discrete_sequence=['#00FF9C', '#FF4B4B'])
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.write("### ⚡ AI Zone Decisions")
    for zone, status in res['decisions'].items():
        color = "#00FF9C" if "ON" in status else "#FF4B4B"
        st.markdown(f"""
            <div style="padding:10px; border-bottom:1px solid #333">
                <span style="font-weight:bold">{zone}</span>: 
                <span style="color:{color}">{status}</span>
            </div>
        """, unsafe_allow_html=True)

# --- AI EXPLAINABILITY ---
with st.expander("🧠 Why did AI make these decisions? (AI Explainability)"):
    for zone, status in res['decisions'].items():
        explanation = sys.explain_decision(zone, status, res['battery'])
        st.info(explanation)

# --- PDF REPORTING ---
st.write("---")
if st.button("Generate Enterprise PDF Report 📄"):
    pdf_bytes = generate_enterprise_pdf(user, res)
    st.download_button("Download Report", pdf_bytes, file_name="enterprise_report.pdf")

st.toast("System Data Updated", icon="✅")
