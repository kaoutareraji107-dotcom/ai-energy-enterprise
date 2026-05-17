import datetime
import os

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF

from engine import CityZone, SmartCityStrategic


st.set_page_config(page_title="AI Smart Energy", layout="wide")

API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY")
DATA_FILE = "energy_log.csv"


st.markdown(
    """
<style>
body {
    background-color: #0E1117;
    color: white;
}

.title {
    font-size: 42px;
    font-weight: bold;
    background: linear-gradient(90deg,#00FF9C,#00CFFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.card {
    background: linear-gradient(145deg, #1c1f26, #111318);
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.5);
    transition: 0.3s;
    text-align:center;
}

.card:hover {
    transform: scale(1.02);
}

.green {
    color:#00FF9C;
}

.red {
    color:#ff4b4b;
}

.small-text {
    color: #AAAAAA;
    font-size: 14px;
}
</style>
""",
    unsafe_allow_html=True,
)


def get_weather(city, country):
    if not city or not country or API_KEY == "YOUR_API_KEY":
        return 25, 2, "clear sky"

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": f"{city},{country}",
            "appid": API_KEY,
            "units": "metric",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        clouds = data["clouds"]["all"] / 10
        weather = data["weather"][0]["description"]
        return temp, clouds, weather
    except requests.RequestException:
        return 25, 2, "clear sky"
    except (KeyError, IndexError, TypeError):
        return 25, 2, "clear sky"


def generate_pdf(user, res, co2, weather):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "AI SMART ENERGY REPORT", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, f"Company: {user['company']}", ln=True)
    pdf.cell(0, 10, f"Manager: {user['name']}", ln=True)
    pdf.cell(0, 10, f"Country: {user['country']}", ln=True)
    pdf.cell(0, 10, f"City: {user['city']}", ln=True)

    pdf.ln(5)

    pdf.cell(0, 10, f"Solar Production: {res['solar']} kW", ln=True)
    pdf.cell(0, 10, f"Current Load: {res['load']} kW", ln=True)
    pdf.cell(0, 10, f"Battery Level: {res['battery']}%", ln=True)
    pdf.cell(0, 10, f"CO2 Saved: {co2} kg", ln=True)
    pdf.cell(0, 10, f"Weather: {weather}", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, f"Generated: {datetime.datetime.now()}", ln=True)

    pdf_data = pdf.output(dest="S")
    if isinstance(pdf_data, str):
        return pdf_data.encode("latin-1")
    return bytes(pdf_data)


def save_data(res):
    row = {
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "solar": res["solar"],
        "load": res["load"],
        "battery": res["battery"],
    }

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(DATA_FILE, index=False)


def generate_real_zones(company_type):
    text = company_type.lower()

    if "factory" in text or "usine" in text or "مصنع" in text:
        return [
            CityZone("Production Line", 1, 1500),
            CityZone("Cooling System", 2, 800),
            CityZone("Smart Lighting", 3, 350),
        ]

    if "hospital" in text or "hopital" in text or "مستشفى" in text:
        return [
            CityZone("ICU", 1, 1200),
            CityZone("Emergency", 1, 900),
            CityZone("Rooms", 2, 500),
        ]

    if "hotel" in text or "فندق" in text:
        return [
            CityZone("Rooms", 1, 1000),
            CityZone("Restaurant", 2, 600),
            CityZone("Pool", 3, 400),
        ]

    return [
        CityZone("Main System", 1, 900),
        CityZone("Office", 2, 500),
        CityZone("Lighting", 3, 300),
    ]


if "user" not in st.session_state:
    st.session_state.user = None

if "system" not in st.session_state:
    st.session_state.system = None


if st.session_state.user is None:
    st.markdown(
        '<div class="title">AI Smart Energy Platform</div>',
        unsafe_allow_html=True,
    )

    st.write("## مرحبا")
    st.write("### دخل معلومات المؤسسة ديالك")

    with st.form("user_form"):
        name = st.text_input("الاسم الكامل")
        company = st.text_input("الشركة / النشاط", placeholder="Factory / Hospital / Hotel ...")
        email = st.text_input("البريد الإلكتروني")
        country = st.text_input("الدولة")
        city = st.text_input("المدينة")

        submit = st.form_submit_button("دخول للمنصة")

        if submit:
            st.session_state.user = {
                "name": name.strip() or "Manager",
                "company": company.strip() or "Company",
                "email": email.strip(),
                "country": country.strip() or "Morocco",
                "city": city.strip() or "Casablanca",
            }

            sys = SmartCityStrategic()
            zones = generate_real_zones(st.session_state.user["company"])

            for zone in zones:
                sys.add_zone(zone)

            st.session_state.system = sys
            st.rerun()

    st.stop()


user = st.session_state.user
system = st.session_state.system

temp, clouds, weather = get_weather(user["city"], user["country"])
hour = datetime.datetime.now().hour

res = system.control_center(hour, temp, clouds)
co2 = system.calculate_co2_saved(res["solar"])
tips = system.get_smart_recommendation(res, hour, "English")

save_data(res)


st.markdown(f'<div class="title">{user["company"]}</div>', unsafe_allow_html=True)
st.write(f"Welcome {user['name']} | {user['city']}, {user['country']}")
st.write(f"Current Weather: **{weather}** | {temp}°C")


def card(title, value):
    st.markdown(
        f"""
    <div class="card">
        <h4>{title}</h4>
        <h2 class="green">{value}</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )


c1, c2, c3, c4 = st.columns(4)

with c1:
    card("Solar Production", f"{res['solar']} kW")

with c2:
    card("Current Load", f"{res['load']} kW")

with c3:
    card("Battery", f"{res['battery']}%")

with c4:
    card("CO2 Saved", f"{co2} kg")

st.divider()

st.subheader("Smart Energy Zones")

cols = st.columns(len(res["decisions"]))

for i, (name, status) in enumerate(res["decisions"].items()):
    color = "green" if "ON" in status or status == "LIMITED" else "red"

    with cols[i]:
        st.markdown(
            f"""
        <div class="card">
            <h4>{name}</h4>
            <h2 class="{color}">{status}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.caption(system.explain_decision(name, status, res["battery"]))

st.divider()

st.subheader("AI Recommendations")

for tip in tips:
    st.info(tip)

st.divider()

st.subheader("Live Energy Analytics")

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    st.line_chart(df[["solar", "load", "battery"]])

st.divider()

st.subheader("Smart Report")

pdf = generate_pdf(user, res, co2, weather)

st.download_button(
    "Download PDF Report",
    pdf,
    file_name="AI_Energy_Report.pdf",
    mime="application/pdf",
)

st.toast(f"System Running | Battery {res['battery']}%")
