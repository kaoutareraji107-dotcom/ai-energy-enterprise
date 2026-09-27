import random
import math
import os
import re
import sqlite3
from contextlib import contextmanager

import bcrypt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# =====================================================================
# ================= AUTHENTICATION (Multi-user Security) =============
# =====================================================================
# تخزين حقيقي: SQLite + bcrypt (ماشي plain text). خطوة أولى قبل الانتقال
# لـ PostgreSQL/Firebase بلا ما نبدلو الكود اللي كيستعمل هاد الدوال.

AUTH_DB_FILE = "users.db"


@contextmanager
def _get_connection():
    conn = sqlite3.connect(AUTH_DB_FILE)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """كتخلق جدول المستخدمين إلا ماكانش موجود. Safe تتنادى كل مرة."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                company TEXT,
                country TEXT,
                city TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def _is_valid_email(email: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or "") is not None


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def register_user(email: str, password: str, name: str, company: str, country: str, city: str):
    """Returns (success: bool, message: str)"""
    email = (email or "").strip().lower()

    if not _is_valid_email(email):
        return False, "⚠️ البريد الإلكتروني غير صحيح."
    if not password or len(password) < 6:
        return False, "⚠️ خاص الباسوورد يكون 6 خانات أو كثر."
    if not name or not company:
        return False, "⚠️ عافاك عمر اسم المدير و اسم الشركة."

    init_db()
    with _get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return False, "⚠️ هاد البريد الإلكتروني مسجل من قبل. جرب تدخل (Login)."

        conn.execute(
            """INSERT INTO users (email, password_hash, name, company, country, city)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (email, _hash_password(password), name.strip(), company.strip(), country, city),
        )
        conn.commit()

    return True, "✅ تم إنشاء الحساب بنجاح! دابا تقدر تدخل من Login."


def authenticate(email: str, password: str):
    """Returns the user dict on success, or None on failure."""
    email = (email or "").strip().lower()
    if not email or not password:
        return None

    init_db()
    with _get_connection() as conn:
        row = conn.execute(
            """SELECT id, email, password_hash, name, company, country, city
               FROM users WHERE email = ?""",
            (email,),
        ).fetchone()

    if not row:
        return None

    user_id, db_email, password_hash, name, company, country, city = row
    if not _verify_password(password, password_hash):
        return None

    return {
        "id": user_id,
        "email": db_email,
        "name": name,
        "company": company,
        "country": country,
        "city": city,
    }


def change_password(email: str, old_password: str, new_password: str):
    """Returns (success: bool, message: str)"""
    user = authenticate(email, old_password)
    if not user:
        return False, "⚠️ الباسوورد القديم غير صحيح."
    if not new_password or len(new_password) < 6:
        return False, "⚠️ خاص الباسوورد الجديد يكون 6 خانات أو كثر."

    with _get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (_hash_password(new_password), email.strip().lower()),
        )
        conn.commit()
    return True, "✅ تبدل الباسوورد بنجاح."


# =====================================================================
# ================= CITY ZONE =========================================
# =====================================================================
class CityZone:
    def __init__(self, name, priority, consumption):
        self.name = name
        self.priority = priority  # 1: Critical, 2: Important, 3: Non-Essential
        self.consumption = consumption  # kW
        self.active = True

# ================= SMART SYSTEM =================
class SmartCityStrategic:
    def __init__(self):
        self.zones = []
        self.battery_capacity = 5000.0  # kWh
        self.current_charge = 2500.0    # kWh
        self.max_solar_peak = 2200.0    # kW
        self.model = None
        self.model_score = None   # دقة النموذج (%) محسوبة بـ train/test حقيقي
        self.trained_on_real_data = False
        self.init_ml_model()

    def add_zone(self, zone):
        self.zones.append(zone)

    def clear_zones(self):
        self.zones = []

    # ================= FINANCIAL ENGINE (TOU TARIFF) =================
    def calculate_financials(self, solar, actual_load, hour=12):
        """حساب المؤشرات المالية مع مراعاة تعرفة ساعات الذروة ف المغرب"""
        # تعرفة متغيرة: Peak hours (17:00 - 22:00) أغلى
        if 17 <= hour <= 22:
            tariff_per_kwh = 1.65  # درهم ف ساعات الذروة
        else:
            tariff_per_kwh = 1.05  # درهم ف الساعات العادية

        potential_cost = actual_load * tariff_per_kwh
        energy_covered = min(solar, actual_load)
        money_saved = energy_covered * tariff_per_kwh

        grid_needed = max(0.0, actual_load - solar)
        current_bill = grid_needed * tariff_per_kwh

        return {
            "money_saved": round(money_saved, 2),
            "current_bill": round(current_bill, 2),
            "potential_cost": round(potential_cost, 2),
            "tariff": tariff_per_kwh
        }

    # ================= MACHINE LEARNING ENGINE =================
    def _diurnal_factor(self, hour):
        """الشكل الطبيعي لمنحنى الاستهلاك عبر اليوم (نهار أعلى، ليل أقل)."""
        if 8 <= hour <= 18:
            return 0.9 + (math.sin(hour * math.pi / 12) * 0.1)
        return 0.45

    def _generate_synthetic_training_data(self, n_days=90):
        """
        بيانات تدريب افتراضية (يستعملها الموديل غير كي ماكانش عندنا Log
        كافي من الاستعمال الحقيقي). كل يوم عندو طقس عشوائي، وكل ساعة
        فيه عندها حمل يتبع منحنى نهاري + تأثير الحرارة والغيوم.
        """
        np.random.seed(42)
        rows = []
        for _ in range(n_days):
            day_temp = np.random.uniform(15, 42)
            day_clouds = np.random.uniform(0, 10)
            base_load = 500 + (day_temp * 30) + (day_clouds * 20)
            for h in range(24):
                load = base_load * self._diurnal_factor(h) + np.random.normal(0, 15)
                rows.append({
                    "hour": h,
                    "temp": day_temp,
                    "clouds": day_clouds,
                    "load": max(150.0, load),
                })
        return pd.DataFrame(rows)

    def init_ml_model(self, data_file="energy_log.csv"):
        """
        تدريب نموذج التنبؤ الحقيقي: [الساعة، الحرارة، الغيوم] -> الحمل.
        كيستعمل بيانات الاستعمال الحقيقية (energy_log.csv) إلى كانت كافية،
        وإلا كيرجع لبيانات افتراضية واقعية. كيحسب كذلك دقة حقيقية بـ
        train/test split (ماشي رقم ثابت).
        """
        df = None
        self.trained_on_real_data = False

        if os.path.exists(data_file):
            try:
                log_df = pd.read_csv(data_file)
                required_cols = {"temp", "clouds", "load", "timestamp"}
                if len(log_df) >= 30 and required_cols.issubset(log_df.columns):
                    log_df = log_df.dropna(subset=list(required_cols))
                    log_df["hour"] = pd.to_datetime(log_df["timestamp"]).dt.hour
                    df = log_df[["hour", "temp", "clouds", "load"]]
                    self.trained_on_real_data = True
            except Exception:
                df = None

        if df is None or len(df) < 30:
            df = self._generate_synthetic_training_data()
            self.trained_on_real_data = False

        X = df[["hour", "temp", "clouds"]].values
        y = df["load"].values

        # ---- تقييم الدقة الحقيقي (train/test split) ----
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            eval_model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42)
            eval_model.fit(X_train, y_train)
            r2 = eval_model.score(X_test, y_test)
            self.model_score = round(max(0.0, r2) * 100.0, 1)
        except Exception:
            self.model_score = None

        # ---- تدريب الموديل النهائي على كل الداتا ----
        self.model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42)
        self.model.fit(X, y)

    def forecast_tomorrow_demand(self, tomorrow_temp, tomorrow_clouds):
        """
        كيتوقع الحمل ساعة بساعة لغد بناء على الموديل المدرب (ماشي منحنى
        ثابت + عشوائية). كيرجع (المعدل اليومي المتوقع، القيم الـ24 ساعة).
        """
        if self.model is None:
            self.init_ml_model()

        hourly_forecast = []
        for h in range(24):
            pred = float(self.model.predict([[h, tomorrow_temp, tomorrow_clouds]])[0])
            hourly_forecast.append(round(max(150.0, pred), 2))

        daily_avg = round(float(np.mean(hourly_forecast)), 2)
        return daily_avg, hourly_forecast

    def get_historical_hourly_average(self, data_file="energy_log.csv"):
        """
        المعدل الحقيقي للاستهلاك حسب الساعة، محسوب من الـ Log الفعلي.
        كيرجع None إلى ماكانتش الداتا كافية (باش المبيان ما يوريش خط مزيف).
        """
        if not os.path.exists(data_file):
            return None
        try:
            df = pd.read_csv(data_file)
            if len(df) < 24 or not {"timestamp", "load"}.issubset(df.columns):
                return None
            df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
            hourly = df.groupby("hour")["load"].mean().reindex(range(24))
            if hourly.isna().sum() > 12:  # ناقصة بزاف ساعات باش تكون معبرة
                return None
            return hourly.interpolate(limit_direction="both").round(2).tolist()
        except Exception:
            return None

    # ================= REAL SOLAR MODEL =================
    def get_solar(self, hour, clouds):
        if 6 <= hour <= 18:
            curve = math.sin((hour - 6) * math.pi / 12)
            solar = self.max_solar_peak * curve
            cloud_impact = (clouds / 10.0) * 0.75
            solar *= (1.0 - cloud_impact)
            return max(0.0, round(solar, 2))
        return 0.0

    def calculate_total_load(self, decisions=None):
        total = 0.0
        for zone in self.zones:
            if decisions and zone.name in decisions:
                status = decisions[zone.name]
                if status == "ON":
                    total += zone.consumption
                elif status == "LIMITED":
                    total += zone.consumption * 0.5
            else:
                if zone.active:
                    total += zone.consumption
        return total

    # ================= REAL BATTERY DYNAMICS =================
    def update_and_get_battery_pct(self, solar, actual_load, delta_minutes=60):
        net_energy = solar - actual_load
        
        # كفاءة الشحن والتفريغ (92%)
        if net_energy > 0:
            net_energy *= 0.92
        else:
            net_energy /= 0.92

        # تحويل الطاقة اللحظية حسب الوقت المنقضي
        self.current_charge += (net_energy * (delta_minutes / 60.0))
        self.current_charge = max(0.0, min(self.battery_capacity, self.current_charge))
        return round((self.current_charge / self.battery_capacity) * 100.0, 1)

    def optimize_zones(self, solar, current_battery_pct):
        decisions = {}
        total_potential_load = sum(z.consumption for z in self.zones)

        for zone in self.zones:
            if current_battery_pct < 25 and solar < 400:
                if zone.priority >= 2:
                    zone.active = False
                    decisions[zone.name] = "OFF"
                else:
                    zone.active = True
                    decisions[zone.name] = "ON"
            elif current_battery_pct < 45 and solar < total_potential_load:
                if zone.priority >= 3:
                    zone.active = False
                    decisions[zone.name] = "OFF"
                elif zone.priority == 2:
                    zone.active = True
                    decisions[zone.name] = "LIMITED"
                else:
                    zone.active = True
                    decisions[zone.name] = "ON"
            else:
                zone.active = True
                decisions[zone.name] = "ON"

        return decisions

    def control_center(self, hour, temp, clouds):
        solar = self.get_solar(hour, clouds)
        current_pct = round((self.current_charge / self.battery_capacity) * 100.0, 1)
        decisions = self.optimize_zones(solar, current_pct)
        actual_load = self.calculate_total_load(decisions)
        battery_pct = self.update_and_get_battery_pct(solar, actual_load)
        efficiency = self.calculate_efficiency(solar, actual_load)
        financials = self.calculate_financials(solar, actual_load, hour)

        return {
            "solar": solar,
            "load": actual_load,
            "battery": battery_pct,
            "efficiency": efficiency,
            "temperature": temp,
            "clouds": clouds,
            "decisions": decisions,
            "financials": financials
        }

    def calculate_efficiency(self, solar, load):
        if load == 0: return 100.0
        return round(min(100.0, (solar / load) * 100.0), 2)

    def calculate_co2_saved(self, solar_kw):
        # 1 كيلوواط ساعة شمسية كيوفر تقريباً 0.7 كجم من CO2 بالمغرب
        return round(solar_kw * 0.7, 1)

    def get_smart_recommendation(self, res, hour, language="EN"):
        tips = []
        if res["battery"] < 30:
            tips.append("🔋 Battery Protection active: DoD threshold protection triggered.")
        if res["solar"] > res["load"]:
            tips.append("☀️ Solar Surplus: Storing green energy to battery bank.")
        if 17 <= hour <= 22:
            tips.append("⏰ Peak Tariff Hour: Maximum reliance on battery/solar to avoid high grid cost.")
        return tips if tips else ["⚡ Microgrid Operating at Peak Efficiency."]

    def explain_decision(self, zone, status, battery_pct):
        if status == "OFF": 
            return f"⚠️ {zone} isolated automatically to protect battery life cycle."
        if status == "LIMITED": 
            return f"🟡 {zone} power capped at 50% via PWM control to reduce load."
        return f"☀️ {zone} fully powered via renewable microgrid busbar."
