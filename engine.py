import random
import math
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# ================= CITY ZONE =================
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
    def init_ml_model(self, data_file="energy_log.csv"):
        """تدريب نموذج التنبؤ مرة واحدة عند التشغيل"""
        if os.path.exists(data_file):
            try:
                df = pd.read_csv(data_file)
                if len(df) >= 10 and 'temp' in df.columns and 'clouds' in df.columns:
                    X = df[['temp', 'clouds']].values
                    y = df['load'].values
                    self.model = RandomForestRegressor(n_estimators=50, random_state=42)
                    self.model.fit(X, y)
                    return
            except Exception:
                pass
        
        # بيانات افتراضية للتدريب ف حالة عدم وجود ملف داتا كافي
        np.random.seed(42)
        X = np.random.uniform(15, 42, (150, 2))
        y = 500 + (X[:, 0] * 30) + (X[:, 1] * 20) + np.random.normal(0, 25, 150)
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.model.fit(X, y)

    def forecast_tomorrow_demand(self, tomorrow_temp, tomorrow_clouds):
        if self.model is None:
            self.init_ml_model()

        input_data = np.array([[tomorrow_temp, tomorrow_clouds]])
        prediction = float(self.model.predict(input_data)[0])

        hours = list(range(24))
        hourly_forecast = []
        for h in hours:
            if 8 <= h <= 18:
                time_factor = 0.9 + (math.sin(h * math.pi / 12) * 0.1)
            else:
                time_factor = 0.45

            hourly_load = prediction * time_factor + np.random.normal(0, 10)
            hourly_forecast.append(round(max(150.0, hourly_load), 2))

        return round(prediction, 2), hourly_forecast

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
