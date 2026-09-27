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

API_KEY = st.secrets.get("OPENWEATHER_API_KEY", os.getenv("OPENWEATHER_API_KEY", ""))
DATA_FILE = "energy_log.csv"

# ================= UI STYLE =================
st.markdown("""
<style>
html, body, [class*="css"] {
    background: #050816;
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.main {
    background: linear-gradient(180deg,#050816,#0f172a);
}
.title {
    font-size: 44px;
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
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.45);
    transition: 0.3s;
}
.card:hover {
    transform: translateY(-4px);
    border: 1px solid #00FF9C;
}
.green { color: #00FF9C; }
.red { color: #ff4b4b; }
.blue { color: #00CFFF; }
.purple { color: #8B5CF6; }
</style>
""", unsafe_allow_html=True)

# ================= WEATHER API =================
@st.cache_data(ttl=600)
def get_weather(city, country):
    if not API_KEY or not city:
        return 25.0, 2.0
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            clouds = data["clouds"]["all"] / 10.0
            return float(temp), float(clouds)
    except Exception as e:
        st.sidebar.warning(f"Weather API Warning: {e}")
    return 25.0, 2.0

# ================= REAL ZONES =================
def generate_real_zones(company_type):
    company_type = str(company_type).lower()
    if "factory" in company_type or "مصنع" in company_type:
        return [
            CityZone("Production Line", 1, 1500),
            CityZone("Cooling System", 2, 800),
            CityZone("Smart Lighting", 3, 300)
        ]
    elif "hospital" in company_type or "مستشفى" in company_type:
        return [
            CityZone("ICU Unit", 1, 1000),
            CityZone("Emergency Ward", 1, 900),
            CityZone("General Rooms", 2, 500)
        ]
    elif "mall" in company_type or "فندق" in company_type:
        return [
            CityZone("Retail Outlets", 1, 1200),
            CityZone("HVAC Cooling", 2, 700),
            CityZone("Parking Facilities", 3, 300)
        ]
    else:
        return [
            CityZone("Main Facilities", 1, 800),
            CityZone("Support Systems", 2, 400)
        ]

# ================= DATA LOGGING =================
def save_data(res, temp, clouds):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if st.session_state.get("last_log") == now_str:
        return
    st.session_state.last_log = now_str

    row = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "solar_kw": res["solar_kw"],
        "load_kw": res["load_kw"],
        "battery_soc": res["battery_soc"],
        "temp": temp,
        "clouds": clouds,
        "savings_mad": res["financials"]["money_saved_mad"],
        "grid_import_kwh": res.get("energy_flow", {}).get("grid_import_kwh", 0.0),
        "solar_to_load_kwh": res.get("energy_flow", {}).get("solar_to_load_kwh", 0.0),
        "battery_to_load_kwh": res.get("energy_flow", {}).get("battery_to_load_kwh", 0.0),
        "co2_saved_kg": res.get("co2_saved_kg", 0.0)
    }
    
    df_new = pd.DataFrame([row])
    header = not os.path.exists(DATA_FILE)
    df_new.to_csv(DATA_FILE, mode='a', header=header, index=False)

# ================= SAFE PDF REPORT GENERATION =================
def sanitize_str(val):
    """Sanitizes text strings to avoid Latin-1 / ASCII FPDF errors."""
    return str(val).encode('ascii', 'ignore').decode('ascii') or "N/A"

def generate_pdf(user, res):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "AI ENERGY ENTERPRISE AUDIT REPORT", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, f"Company Name: {sanitize_str(user['company'])}", ln=True)
    pdf.cell(0, 8, f"Facility Manager: {sanitize_str(user['name'])}", ln=True)
    pdf.cell(0, 8, f"Location Node: {sanitize_str(user['city'])}, {sanitize_str(user['country'])}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.cell(0, 8, "Technical Microgrid Performance:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, f"- Solar Active Generation: {res['solar_kw']} kW", ln=True)
    pdf.cell(0, 7, f"- Instant Power Demand: {res['load_kw']} kW", ln=True)
    pdf.cell(0, 7, f"- Storage Battery SoC: {res['battery_soc']}%", ln=True)
    pdf.cell(0, 7, f"- CO2 Emissions Offset: {res['co2_saved_kg']} kg", ln=True)
    pdf.ln(5)
    
    financials = res["financials"]
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.cell(0, 8, "Financial Performance Metrics:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, f"- Instant Hourly Savings: {financials['money_saved_mad']} MAD", ln=True)
    pdf.cell(0, 7, f"- Net Grid Import Bill: {financials['current_bill_mad']} MAD", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", style="I", size=9)
    pdf.multi_cell(0, 5, "Automated Audit generated by AI Energy Enterprise hardware-edge controller.")
    return bytes(pdf.output())

# ================= SESSION INITIALIZATION =================
if "user" not in st.session_state:
    st.session_state.user = None
if "system" not in st.session_state:
    st.session_state.system = SmartCityStrategic()

# ================= SIDEBAR =================
st.sidebar.title("🧠 AI Edge Controller")
hardware_status = st.sidebar.toggle("📡 Enable IoT Simulation", value=True)
if hardware_status:
    st.sidebar.success("IoT Status: ACTIVE SIMULATION")
else:
    st.sidebar.warning("IoT Status: OFF")

st.sidebar.markdown("---")
mode = st.sidebar.selectbox("⚙️ Optimization Strategy", ["Eco Mode 🌿", "Balanced ⚡", "Performance 🚀"])

# ================= LOGIN FLOW =================
if st.session_state.user is None:
    st.markdown('<div class="title">⚡ AI Energy Enterprise</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Smart Infrastructure • Edge Hardware AI • Sustainability</div>', unsafe_allow_html=True)

    with st.form("user_form"):
        name = st.text_input("👤 Manager Name")
        company = st.text_input("🏭 Enterprise/Factory Name")
        email = st.text_input("📧 Business Email")
        country = st.text_input("🌍 Country", value="Morocco")
        city = st.text_input("🏙️ City", value="Agadir")
        submitted = st.form_submit_button("🚀 Launch AI Microgrid Platform")

        if submitted:
            st.session_state.user = {
                "name": name or "Manager", 
                "company": company or "Enterprise Factory",
                "email": email, "country": country, "city": city
            }
            system = SmartCityStrategic()
            system.clear_zones()
            for z in generate_real_zones(st.session_state.user["company"]):
                system.add_zone(z)
            st.session_state.system = system
            st.rerun()
    st.stop()

# ================= DASHBOARD MAIN =================
user = st.session_state.user
system = st.session_state.system

temp, clouds = get_weather(user["city"], user["country"])
hour = datetime.datetime.now().hour

res = system.control_center(hour, temp, clouds)
save_data(res, temp, clouds)
financials = res["financials"]

# ================= HEADER =================
st.markdown(f'<div class="title">🏭 {user["company"]} Control Room</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Real-Time Sensor Node: {user["city"]} ({temp}°C) | Tariff: {financials["tariff_mad_kwh"]} MAD/kWh</div>', unsafe_allow_html=True)
st.markdown("---")

# ================= METRICS =================
st.markdown("### ⚡ Microgrid Physical Metrics")
def card(title, value, color="green"):
    st.markdown(f"""
    <div class="card">
        <h4>{title}</h4>
        <h2 class="{color}">{value}</h2>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: card("☀️ Solar Power", f"{res['solar_kw']} kW", "green")
with c2: card("⚡ Total Demand", f"{res['load_kw']} kW", "red")
with c3: card("🔋 Battery SoC", f"{res['battery_soc']}%", "blue")
with c4: card("🌿 CO2 Reduced", f"{res['co2_saved_kg']} kg", "purple")

# ================= FINANCIAL METRICS =================
st.markdown("---")
st.markdown("### 📊 Real-Time Financial Performance")
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1: card("💰 Instant Hourly Savings", f"{financials['money_saved_mad']} MAD", "green")
with f_col2: card("📉 Current Net Bill", f"{financials['current_bill_mad']} MAD", "red")
with f_col3: card("⚡ Solar Coverage Rate", f"{round((res['solar_kw']/(res['load_kw']+0.01))*100, 1)}%", "blue")

# ================= RELAYS =================
st.markdown("---")
st.subheader("🔌 Automated Relays & Priority Dispatch")
if res["decisions"]:
    cols = st.columns(len(res["decisions"]))
    for i, (name, status) in enumerate(res["decisions"].items()):
        color = "green" if status in ["ON", "LIMITED"] else "red"
        with cols[i]:
            card(name, status, color)

# ================= PREDICTIONS & AI =================
st.markdown("---")
st.subheader("🔮 Predictive Analytics & AI Forecasting")
col_p1, col_p2 = st.columns([1, 2])

with col_p1:
    st.markdown("#### Forecast Parameters (Tomorrow)")
    next_temp = st.slider("Expected Temperature (°C)", 10, 45, int(temp) + 1)
    next_clouds = st.slider("Expected Cloudiness (0-10)", 0, 10, int(clouds))
    predicted_total, hourly_curve = system.forecast_tomorrow_demand(next_temp, next_clouds)
    st.metric(label="📊 Estimated Daily Demand Peak", value=f"{predicted_total} kW")

with col_p2:
    forecast_df = pd.DataFrame({
        "Hour": [f"{h:02d}:00" for h in range(24)],
        "Predicted Demand (kW)": hourly_curve
    })
    fig = px.line(
        forecast_df, x="Hour", y="Predicted Demand (kW)",
        title="📈 24-Hour Predictive Load Profile",
        template="plotly_dark", color_discrete_sequence=["#8B5CF6"]
    )
    st.plotly_chart(fig, use_container_width=True)

    hourly_solar_curve = [system.get_solar_kw(h, next_clouds) for h in range(24)]
    projection = system.calculate_daily_financial_projection(
        hourly_load_kw=hourly_curve,
        hourly_solar_kw=hourly_solar_curve,
    )

    st.markdown("#### 💰 24h Projections Strategy")
    p1, p2, p3, p4 = st.columns(4)
    with p1: card("Daily Savings", f"{projection['daily_savings_mad']} MAD", "green")
    with p2: card("Est. Annual Savings", f"{projection['annual_savings_mad']} MAD", "green")
    with p3: card("Payback Period", f"{projection.get('payback_years', 'N/A')} Yrs", "blue")
    with p4: card("Est. ROI", f"{projection.get('roi_percentage', 'N/A')}%", "purple")

# ================= MAP & AUDIT REPORT =================
st.markdown("---")
st.subheader("📍 Geolocation Node Map")
m = folium.Map(location=[30.4278, -9.5981], zoom_start=12)
folium.Marker(
    [30.4278, -9.5981],
    tooltip=f"{user['company']} Node",
    popup=f"AI Controller Hub: {user['company']}"
).add_to(m)
st_folium(m, width=1200, height=320, key="enterprise_map")

st.markdown("---")
pdf_data = generate_pdf(user, res)
st.download_button(
    label="⬇️ Download Enterprise Audit Report (PDF)",
    data=pdf_data,
    file_name="enterprise_audit.pdf",
    mime="application/pdf"
)
