import streamlit as st
import datetime
import requests
import pandas as pd
import os
from fpdf import FPDF
import plotly.express as px
import folium
from streamlit_folium import st_folium

from engine import SmartCityStrategic, CityZone

# ================= CONFIG =================
st.set_page_config(
    page_title="AI Energy Enterprise ⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_KEY = "YOUR_API_KEY"
DATA_FILE = "energy_log.csv"

# ================= UI STYLE =================
st.markdown("""
<style>
html, body, [class*="css"] {
    background: #050816;
    color: white;
    font-family: 'Segoe UI';
}
.main {
    background: linear-gradient(180deg,#050816,#0f172a);
}
.title {
    font-size: 48px;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg,#00FF9C,#00CFFF,#8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    text-align: center;
    color: rgba(255,255,255,0.7);
    margin-bottom: 20px;
}
.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 24px;
    text-align: center;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.45);
    transition: 0.3s;
}
.card:hover {
    transform: translateY(-4px) scale(1.02);
    border: 1px solid #00FF9C;
}
.green { color: #00FF9C; }
.red { color: #ff4b4b; }
.blue { color: #00CFFF; }
.purple { color: #8B5CF6; }
</style>
""", unsafe_allow_html=True)

# ================= WEATHER =================
def get_weather(city, country):
    if API_KEY == "YOUR_API_KEY" or not city:
        return 25, 2
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={API_KEY}&units=metric"
        data = requests.get(url, timeout=5).json()
        temp = data["main"]["temp"]
        clouds = data["clouds"]["all"] / 10
        return temp, clouds
    except:
        return 25, 2

# ================= REAL ZONES =================
def generate_real_zones(company_type):
    company_type = company_type.lower()
    if "factory" in company_type or "مصنع" in company_type:
        return [
            CityZone("🏭 Production Line", 1, 1500),
            CityZone("❄️ Cooling System", 2, 800),
            CityZone("💡 Smart Lighting", 3, 300)
        ]
    elif "hospital" in company_type or "مستشفى" in company_type:
        return [
            CityZone("🏥 ICU", 1, 1000),
            CityZone("🚑 Emergency", 1, 900),
            CityZone("🛏️ Rooms", 2, 500)
        ]
    elif "mall" in company_type or "فندق" in company_type:
        return [
            CityZone("🛍️ Shops", 1, 1200),
            CityZone("❄️ Cooling", 2, 700),
            CityZone("🚗 Parking", 3, 300)
        ]
    else:
        return [
            CityZone("⚡ Main System", 1, 800),
            CityZone("🔧 Support", 2, 400)
        ]

# ================= SAVE DATA =================
def save_data(res):
    # نمنع الحفظ المتكرر في نفس الدقيقة لتفادي عشوائية البيانات
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if "last_log" in st.session_state and st.session_state.last_log == now_str:
        return
    st.session_state.last_log = now_str

    row = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "solar": res["solar"],
        "load": res["load"],
        "battery": res["battery"]
    }
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
        
    df.tail(30).to_csv(DATA_FILE, index=False) # نحتفظ بآخر 30 سطر فقط

# ================= PDF =================
def generate_pdf(user, res, co2):
    pdf = FPDF()
    pdf.add_page()
    
    # نختاروا خط افتراضي سليم
    pdf.set_font("Helvetica", size=16)
    pdf.cell(0, 10, "AI ENERGY ENTERPRISE REPORT", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=12)
    
    # دالة لتنظيف النصوص وحذف الإيموجي أو الحروف الغريبة باش الـ PDF ما يوقعش فيه خطأ ترميز
    def clean_text(text):
        return str(text).encode('ascii', 'ignore').decode('ascii')

    # تنظيف اسم الشركة والمدينة
    clean_company = clean_text(user['company']) or "Enterprise"
    clean_manager = clean_text(user['name']) or "Manager"
    clean_city = clean_text(user['city']) or "City"

    pdf.cell(0, 10, f"Company: {clean_company}", ln=True)
    pdf.cell(0, 10, f"Manager: {clean_manager}", ln=True)
    pdf.cell(0, 10, f"Location: {clean_city}", ln=True)
    pdf.ln(5)
    
    pdf.cell(0, 10, f"Solar Production: {res['solar']} kW", ln=True)
    pdf.cell(0, 10, f"Energy Consumption: {res['load']} kW", ln=True)
    pdf.cell(0, 10, f"Battery Level: {res['battery']}%", ln=True)
    pdf.cell(0, 10, f"CO2 Saved: {co2} kg", ln=True)
    pdf.ln(10)
    
    pdf.multi_cell(0, 10, "This report was generated automatically by AI Energy Enterprise Platform.")
    
    # في fpdf2 الحديثة، استدعاء الدالة بدون متغيرات يرجع bytes مباشرة وجاهزة للتحميل
    return pdf.output()

# ================= SESSION =================
if "user" not in st.session_state:
    st.session_state.user = None
if "system" not in st.session_state:
    st.session_state.system = SmartCityStrategic()

# ================= SIDEBAR =================
st.sidebar.title("🧠 AI Control Center")
mode = st.sidebar.selectbox("⚙️ System Mode", ["Eco Mode 🌿", "Balanced ⚡", "Performance 🚀"])
st.sidebar.markdown("---")
st.sidebar.info("AI Enterprise Dashboard Active ⚡")

# ================= LOGIN =================
if st.session_state.user is None:
    st.markdown('<div class="title">⚡ AI Energy Enterprise</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Smart Infrastructure • AI • Sustainability 🌍</div>', unsafe_allow_html=True)

    with st.form("user_form"):
        name = st.text_input("👤 Name")
        company = st.text_input("🏭 Company")
        email = st.text_input("📧 Email")
        country = st.text_input("🌍 Country")
        city = st.text_input("🏙️ City")
        submitted = st.form_submit_button("🚀 Launch Platform")

        if submitted:
            st.session_state.user = {
                "name": name or "Manager", "company": company or "Enterprise",
                "email": email, "country": country or "Morocco", "city": city or "Agadir"
            }
            system = SmartCityStrategic()
            zones = generate_real_zones(st.session_state.user["company"])
            for z in zones:
                system.add_zone(z)
            st.session_state.system = system
            st.rerun()
    st.stop()

# ================= DASHBOARD CORE =================
user = st.session_state.user
system = st.session_state.system

temp, clouds = get_weather(user["city"], user["country"])
hour = datetime.datetime.now().hour
res = system.control_center(hour, temp, clouds)
co2 = system.calculate_co2_saved(res["solar"])
tips = system.get_smart_recommendation(res, hour, "EN")
save_data(res)

# ================= HEADER =================
st.markdown(f'<div class="title">🏭 {user["company"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Welcome {user["name"]} • {user["city"]} • Enterprise Dashboard ⚡</div>', unsafe_allow_html=True)
st.markdown("---")

# ================= CARDS =================
def card(title, value, color="green"):
    st.markdown(f"""
    <div class="card">
        <h4>{title}</h4>
        <h2 class="{color}">{value}</h2>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: card("☀️ Solar", f"{res['solar']} kW", "green")
with c2: card("⚡ Load", f"{res['load']} kW", "red")
with c3: card("🔋 Battery", f"{res['battery']}%", "blue")
with c4: card("🌿 CO2 Saved", f"{co2} kg", "purple")

# ================= ALERTS =================
st.markdown("---")
st.subheader("🔔 Smart Alerts")
if res["battery"] < 20: st.error("🔋 Critical Battery Level")
if res["load"] > 1500: st.warning("⚠️ High Consumption Detected")
if clouds > 7: st.info("☁️ Cloud Density High — Solar Efficiency Reduced")

# ================= ZONES =================
st.markdown("---")
st.subheader("⚡ Smart Zones Status")
cols = st.columns(len(res["decisions"]))
for i, (name, status) in enumerate(res["decisions"].items()):
    color = "green" if "ON" in status or "LIMITED" in status else "red"
    with cols[i]:
        st.markdown(f"""
        <div class="card">
            <h4>{name}</h4>
            <h2 class="{color}">{status}</h2>
        </div>
        """, unsafe_allow_html=True)

# ================= AI EXPLAINABILITY =================
st.markdown("---")
st.subheader("🧠 AI Explainability")
for name, status in res["decisions"].items():
    explanation = system.explain_decision(name, status, res["battery"]) # تصحيح المعطى هنا ليكون نسبة البطارية
    st.info(explanation)

# ================= AI INSIGHTS =================
st.markdown("---")
st.subheader("🤖 AI Insights")
for tip in tips: st.success(tip)

# ================= ANALYTICS =================
st.markdown("---")
st.subheader("📈 Live Analytics")
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    fig = px.line(df, x="time", y=["solar", "load", "battery"], 
                  title="⚡ Enterprise Energy Analytics", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ================= MAP =================
st.markdown("---")
st.subheader("🗺️ Smart Infrastructure Map")
# الإحداثيات الافتراضية لأكادير كمثال متناسق مع الخريطة
m = folium.Map(location=[30.4278, -9.5981], zoom_start=13)
folium.Marker([30.4278, -9.5981], tooltip="Solar Station ☀️", popup="AI Solar Infrastructure").add_to(m)
folium.Marker([30.4178, -9.5881], tooltip="Battery Center 🔋", popup="Smart Battery Storage").add_to(m)
st_folium(m, width=1200, height=400, key="main_map")

# ================= REPORT =================
st.markdown("---")
st.subheader("📄 Enterprise Report")

# الحل الصحيح لزر التحميل المباشر في Streamlit
pdf_data = generate_pdf(user, res, co2)
st.download_button(
    label="⬇️ Download Enterprise Report (PDF)",
    data=pdf_data,
    file_name="enterprise_report.pdf",
    mime="application/pdf"
)

# ================= FOOTER =================
st.markdown("---")
st.markdown("<center>⚡ AI Energy Enterprise • Smart Cities Future • Powered by AI</center>", unsafe_allow_html=True)
st.toast(f"⚡ System Running | Temp: {temp}°C")
