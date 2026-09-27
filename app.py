import datetime
import os
import requests
import pandas as pd
from fpdf import FPDF
import plotly.express as px
import folium
from streamlit_folium import st_folium
import streamlit as st

from engine import CityZone, SmartCityStrategic

# ================= CONFIG =================
st.set_page_config(
    page_title="AI Energy Enterprise ⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 🟢 الأمان: قراءة المفتاح من st.secrets أو متغيرة البيئة
API_KEY = st.secrets.get("OPENWEATHER_API_KEY", os.getenv("OPENWEATHER_API_KEY", ""))
DATA_FILE = "energy_log.csv"

# ================= UI STYLE =================
st.markdown(
    """
<style>
html, body, [class*="css"] {
    background: #050816;
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.main {
    background: linear-gradient(180deg, #050816, #0f172a);
}
.title {
    font-size: 42px;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, #00FF9C, #00CFFF, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 5px;
}
.subtitle {
    text-align: center;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 25px;
    font-size: 16px;
}
.card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    transition: 0.3s ease-in-out;
}
.card:hover {
    transform: translateY(-3px);
    border: 1px solid #00FF9C;
}
.green { color: #00FF9C; }
.red { color: #ff4b4b; }
.blue { color: #00CFFF; }
.purple { color: #8B5CF6; }
</style>
""",
    unsafe_allow_html=True,
)

# ================= WEATHER (WITH ERROR HANDLING) =================
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

# ================= REAL ZONES GENERATOR =================
def generate_real_zones(company_type):
    company_type = company_type.lower()
    if "factory" in company_type or "مصنع" in company_type:
        return [
            CityZone("🏭 Production Line", 1, 1500),
            CityZone("❄️ Cooling System", 2, 800),
            CityZone("💡 Smart Lighting", 3, 300),
        ]
    elif "hospital" in company_type or "مستشفى" in company_type:
        return [
            CityZone("🏥 ICU", 1, 1000),
            CityZone("🚑 Emergency", 1, 900),
            CityZone("🛏️ Rooms", 2, 500),
        ]
    elif "mall" in company_type or "فندق" in company_type or "مول" in company_type:
        return [
            CityZone("🛍️ Shops", 1, 1200),
            CityZone("❄️ Cooling", 2, 700),
            CityZone("🚗 Parking", 3, 300),
        ]
    else:
        return [
            CityZone("⚡ Main System", 1, 800),
            CityZone("🔧 Support Operations", 2, 400),
            CityZone("💡 Non-Essential", 3, 200),
        ]

# ================= SAVE DATA =================
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
        "co2_saved_kg": res.get("co2_saved_kg", 0.0),
    }

    df_new = pd.DataFrame([row])
    if os.path.exists(DATA_FILE):
        df_new.to_csv(DATA_FILE, mode="a", header=False, index=False)
    else:
        df_new.to_csv(DATA_FILE, mode="w", header=True, index=False)

# ================= PDF REPORT =================
def generate_pdf(user, res):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "AI ENERGY ENTERPRISE AUDIT REPORT", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", size=11)
    clean_company = str(user.get("company", "Enterprise")).encode("ascii", "ignore").decode("ascii") or "Enterprise"
    clean_manager = str(user.get("name", "Manager")).encode("ascii", "ignore").decode("ascii") or "Manager"
    clean_city = str(user.get("city", "City")).encode("ascii", "ignore").decode("ascii") or "City"

    pdf.cell(0, 8, f"Company: {clean_company}", ln=True)
    pdf.cell(0, 8, f"Manager: {clean_manager}", ln=True)
    pdf.cell(0, 8, f"Location: {clean_city}", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", style="B", size=13)
    pdf.cell(0, 8, "Technical Operational Metrics", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, f"- Solar Output: {res['solar_kw']} kW", ln=True)
    pdf.cell(0, 8, f"- Load Consumption: {res['load_kw']} kW", ln=True)
    pdf.cell(0, 8, f"- Battery State of Charge (SoC): {res['battery_soc']}%", ln=True)
    pdf.cell(0, 8, f"- CO2 Saved: {res['co2_saved_kg']} kg", ln=True)
    pdf.ln(5)

    financials = res["financials"]
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.cell(0, 8, "Financial Assessment", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, f"- Hourly Savings: {financials['money_saved_mad']} MAD", ln=True)
    pdf.cell(0, 8, f"- Current Net Bill: {financials['current_bill_mad']} MAD", ln=True)

    payback = financials.get("payback_years")
    roi = financials.get("roi_percentage")
    payback_str = f"{payback} Years" if payback is not None else "N/A"
    roi_str = f"{roi}%" if roi is not None else "N/A"

    pdf.cell(0, 8, f"- Projected Payback: {payback_str} (ROI: {roi_str})", ln=True)
    pdf.ln(10)

    pdf.set_font("Helvetica", style="I", size=10)
    pdf.multi_cell(0, 8, "Generated by AI Energy Enterprise Edge Controller. Confidential Audit Report.")
    return bytes(pdf.output())

# ================= SESSION STATE INIT =================
if "user" not in st.session_state:
    st.session_state.user = None
if "system" not in st.session_state:
    st.session_state.system = SmartCityStrategic()

# ================= SIDEBAR =================
st.sidebar.title("🧠 AI Edge Controller")
st.sidebar.markdown("### 🔌 IoT Sensor Pins")
hardware_status = st.sidebar.toggle("📡 Enable IoT Simulation", value=True)
if hardware_status:
    st.sidebar.success("IoT Status: SIMULATION ACTIVE")
    st.sidebar.caption("Real hardware sensor streams simulated.")
else:
    st.sidebar.warning("IoT Status: SIMULATION OFF")

st.sidebar.markdown("---")
mode = st.sidebar.selectbox("⚙️ System Optimization Mode", ["Eco Mode 🌿", "Balanced ⚡", "Performance 🚀"])

if st.session_state.user is not None:
    st.sidebar.markdown("---")
    if st.sidebar.button("🔴 Logout / Switch Enterprise"):
        st.session_state.user = None
        st.rerun()

# ================= LOGIN / ENTERPRISE FORM =================
if st.session_state.user is None:
    st.markdown('<div class="title">⚡ AI Energy Enterprise</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Smart Microgrid • AI Optimization • Enterprise Sustainability 🌍</div>', unsafe_allow_html=True)

    with st.form("user_form"):
        name = st.text_input("👤 Manager Name")
        company = st.text_input("🏭 Company / Facility Name", value="Agadir Solar Factory")
        email = st.text_input("📧 Business Email")
        country = st.text_input("🌍 Country", value="Morocco")
        city = st.text_input("🏙️ City", value="Agadir")
        submitted = st.form_submit_button("🚀 Launch AI Microgrid Dashboard")

        if submitted:
            st.session_state.user = {
                "name": name or "Manager",
                "company": company or "Enterprise Facility",
                "email": email,
                "country": country,
                "city": city,
            }
            system = SmartCityStrategic()
            system.clear_zones()
            for z in generate_real_zones(st.session_state.user["company"]):
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
save_data(res, temp, clouds)
financials = res["financials"]

# ================= HEADER =================
st.markdown(f'<div class="title">🏭 {user["company"]} Control Room</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="subtitle">Weather Node: {user["city"]} ({temp}°C) • Active Tariff Rate: {financials["tariff_mad_kwh"]} MAD/kWh</div>',
    unsafe_allow_html=True,
)
st.markdown("---")

# ================= HELPER UI CARD =================
def card(title, value, color="green"):
    st.markdown(
        f"""
    <div class="card">
        <h4 style="margin:0; font-size: 14px; opacity: 0.8;">{title}</h4>
        <h2 class="{color}" style="margin: 10px 0 0 0; font-size: 26px;">{value}</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ================= METRICS =================
st.markdown("### ⚡ Physical Energy Metrics")
c1, c2, c3, c4 = st.columns(4)
with c1:
    card("☀️ Solar Output", f"{res['solar_kw']} kW", "green")
with c2:
    card("⚡ Load Demand", f"{res['load_kw']} kW", "red")
with c3:
    card("🔋 Battery SoC", f"{res['battery_soc']}%", "blue")
with c4:
    card("🌿 CO2 Avoided", f"{res['co2_saved_kg']} kg", "purple")

# ================= ENERGY FLOW =================
flow = res.get("energy_flow", {})
st.markdown("### 🔄 Energy Flow Accounting")
e1, e2, e3, e4 = st.columns(4)
with e1:
    card("☀️ Solar → Load", f"{flow.get('solar_to_load_kwh', 0)} kWh", "green")
with e2:
    card("🔋 Battery → Load", f"{flow.get('battery_to_load_kwh', 0)} kWh", "blue")
with e3:
    card("🏭 Grid Import", f"{flow.get('grid_import_kwh', 0)} kWh", "red")
with e4:
    card("☀️ Solar → Battery", f"{flow.get('solar_to_battery_kwh', 0)} kWh", "purple")

# ================= FINANCIALS =================
st.markdown("---")
st.markdown("### 📊 Real-time Financial Performance")
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    card("💰 Money Saved (Hourly)", f"{financials['money_saved_mad']} MAD", "green")
with f_col2:
    card("📉 Net Grid Bill", f"{financials['current_bill_mad']} MAD", "red")
with f_col3:
    payback_text = f"{financials.get('payback_years')} Yrs" if financials.get("payback_years") is not None else "N/A"
    roi_text = f"({financials.get('roi_percentage')}%)" if financials.get("roi_percentage") is not None else ""
    card("🏦 Est. Payback / ROI", f"{payback_text} {roi_text}", "blue")

# ================= ZONES =================
st.markdown("---")
st.subheader("🔌 Automated Relays Status")
if res["decisions"]:
    cols = st.columns(len(res["decisions"]))
    for i, (name, status) in enumerate(res["decisions"].items()):
        color = "green" if status in ["ON", "LIMITED"] else "red"
        with cols[i]:
            card(name, status, color)

# ================= ML PREDICTIONS =================
st.markdown("---")
st.subheader("🔮 AI Demand Forecasting & Daily Projection")
col_p1, col_p2 = st.columns([1, 2])

with col_p1:
    st.markdown("#### الأرصاد المتوقعة لغد 🌤️")
    next_temp = st.slider("الحرارة المتوقعة (°C)", 10, 45, int(temp) + 1)
    next_clouds = st.slider("الغيوم (0-10)", 0, 10, int(clouds))
    predicted_total, hourly_curve = system.forecast_tomorrow_demand(next_temp, next_clouds)
    st.metric(label="📊 الحمل المتوسط المتوقع لغد", value=f"{predicted_total} kW")

with col_p2:
    forecast_df = pd.DataFrame(
        {
            "Hour": [f"{h:02d}:00" for h in range(24)],
            "Predicted Load (kW)": hourly_curve,
        }
    )
    fig = px.line(
        forecast_df,
        x="Hour",
        y="Predicted Load (kW)",
        title="📈 منحنى الحمل المتوقع لـ 24 ساعة القادمة",
        template="plotly_dark",
        color_discrete_sequence=["#8B5CF6"],
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # حساب التوقعات المالية بناءً على منحنى 24 ساعة كامل
    hourly_solar_curve = [
        system.get_solar_kw(h, next_clouds)
        for h in range(24)
    ]
    projection = system.calculate_daily_financial_projection(
        hourly_load_kw=hourly_curve,
        hourly_solar_kw=hourly_solar_curve,
    )

    st.markdown("#### 💰 24h Daily Financial Projection")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        card("Daily Savings", f"{projection['daily_savings_mad']} MAD", "green")
    with p2:
        card("Annualized Savings", f"{projection['annual_savings_mad']} MAD", "green")
    with p3:
        payback = projection.get("payback_years")
        card("Payback", f"{payback} yrs" if payback is not None else "N/A", "blue")
    with p4:
        roi = projection.get("roi_percentage")
        card("Annualized ROI", f"{roi}%" if roi is not None else "N/A", "purple")

# ================= MAP & AUDIT =================
st.markdown("---")
st.subheader("📍 Enterprise Location & Edge Node")
m = folium.Map(location=[30.4278, -9.5981], zoom_start=12)
folium.Marker(
    [30.4278, -9.5981],
    tooltip="AI Edge Gateway ☀️",
    popup=f"{user['company']} Microgrid Hub",
).add_to(m)
st_folium(m, use_container_width=True, height=350, key="main_map")

st.markdown("---")
pdf_data = generate_pdf(user, res)
st.download_button(
    label="⬇️ Download Financial & Technical Audit Report (PDF)",
    data=pdf_data,
    file_name=f"{user['company'].lower().replace(' ', '_')}_audit.pdf",
    mime="application/pdf",
)
