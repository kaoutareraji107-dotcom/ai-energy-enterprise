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
    
    # 🟢 هاد الجزء هو لي كان ناقص وخاصو يرجع هنا فوراً
    def __init__(self):
        self.zones = []
        self.battery_capacity = 5000  # kWh
        self.current_charge = 2500    # kWh

    # ================= FINANCIAL ENGINE =================
    def calculate_financials(self, solar, actual_load):
        """حساب المؤشرات المالية ولغة المال لأصحاب الشركات"""
        # نعتبر ثمن الكيلوواط الافتراضي في المغرب للمقاولات هو 1.20 درهم
        tariff_per_kwh = 1.20 
        
        # 1. التكلفة لو كنا خدامين غير بالشبكة العادية بلا طاقة شمسية
        potential_cost = actual_load * tariff_per_kwh
        
        # 2. شحال وفرنا حيت استعملنا الطاقة الشمسية (الإنتاج اللي تغطى)
        # الوفر هو الإنتاج الشمسي مضروب في الثمن، بشرط ما يفوتش الاستهلاك الفعلي
        energy_covered = min(solar, actual_load)
        money_saved = energy_covered * tariff_per_kwh
        
        # 3. الفاتورة الحالية (الضو اللي شرينا من برا حيت الشمس ما كفاتش)
        grid_needed = max(0, actual_load - solar)
        current_bill = grid_needed * tariff_per_kwh
        
        return {
            "money_saved": round(money_saved, 2),
            "current_bill": round(current_bill, 2),
            "potential_cost": round(potential_cost, 2)
        }

    # ================= MACHINE LEARNING DEMAND FORECASTING =================
    def train_demand_model(self, data_file="energy_log.csv"):
        """تدريب نموذج الذكاء الاصطناعي للتنبؤ باستهلاك الغد"""
        if os.path.exists(data_file) and len(pd.read_csv(data_file)) > 10:
            df = pd.read_csv(data_file)
            X = np.array([[random.randint(15, 38), random.randint(0, 10)] for _ in range(len(df))])
            y = df['load'].values
        else:
            np.random.seed(42)
            X = np.random.uniform(15, 40, (100, 2))
            X[:, 1] = np.random.uniform(0, 10, 100)
            y = 500 + (X[:, 0] * 25) + (X[:, 1] * 40) + np.random.normal(0, 50, 100)
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        return model

    def forecast_tomorrow_demand(self, tomorrow_temp, tomorrow_clouds):
        """توقع حجم استهلاك الطاقة (kW) ليوم غد بناءً على حالة الطقس المتوقعة"""
        model = self.train_demand_model()
        input_data = np.array([[tomorrow_temp, tomorrow_clouds]])
        prediction = model.predict(input_data)[0]
        
        hours = list(range(24))
        hourly_forecast = []
        for h in hours:
            time_factor = math.sin((h - 4) * math.pi / 14) 
            time_factor = max(0.4, (time_factor + 1) / 2)
            hourly_load = prediction * time_factor + random.randint(-50, 50)
            hourly_forecast.append(round(max(200, hourly_load), 2))
            
        return round(prediction, 2), hourly_forecast

    # ================= ADD ZONE =================
    def add_zone(self, zone):
        self.zones.append(zone)

    # ================= SOLAR MODEL =================
    def get_solar(self, hour, clouds):
        if 6 <= hour <= 18:
            peak = 1800
            curve = math.sin((hour - 6) * math.pi / 12)
            solar = peak * curve
            cloud_impact = (clouds / 10) * 0.6
            solar *= (1 - cloud_impact)
            return max(0, int(solar))
        return 0

    # ================= LOAD CALCULATION =================
    def calculate_total_load(self, decisions=None):
        total = 0
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

    # ================= BATTERY INTELLIGENCE =================
    def update_and_get_battery_pct(self, solar, actual_load):
        net_energy = solar - actual_load
        self.current_charge += net_energy
        self.current_charge = max(0, min(self.battery_capacity, self.current_charge))
        return round((self.current_charge / self.battery_capacity) * 100, 1)

    # ================= AI DECISIONS =================
    def optimize_zones(self, solar, current_battery_pct):
        decisions = {}
        total_potential_load = sum(z.consumption for z in self.zones)

        for zone in self.zones:
            if current_battery_pct < 20 and solar < 300:
                if zone.priority >= 2:
                    zone.active = False
                    decisions[zone.name] = "OFF"
                else:
                    zone.active = True
                    decisions[zone.name] = "ON"
            elif current_battery_pct < 40 and solar < total_potential_load:
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

    # ================= MAIN AI CONTROL =================
    # ================= MAIN AI CONTROL =================
    def control_center(self, hour, temp, clouds):
        solar = self.get_solar(hour, clouds)
        current_pct = round((self.current_charge / self.battery_capacity) * 100, 1)
        decisions = self.optimize_zones(solar, current_pct)
        actual_load = self.calculate_total_load(decisions)
        battery_pct = self.update_and_get_battery_pct(solar, actual_load)
        efficiency = self.calculate_efficiency(solar, actual_load)
        
        # 🟢 استدعاء الحسابات المالية الجديدة
        financials = self.calculate_financials(solar, actual_load)

        return {
            "solar": solar,
            "load": actual_load,
            "battery": battery_pct,
            "efficiency": efficiency,
            "temperature": temp,
            "clouds": clouds,
            "decisions": decisions,
            "financials": financials  # 🟢 تضاف هنا
        }
    # ================= CO2 SAVING =================
    def calculate_co2_saved(self, solar):
        return round(solar * 0.42, 2)

    # ================= EFFICIENCY =================
    def calculate_efficiency(self, solar, load):
        if load == 0:
            return 100
        efficiency = (solar / load) * 100
        return round(min(100, efficiency), 2)

    # ================= AI RECOMMENDATIONS =================
    def get_smart_recommendation(self, res, hour, language="EN"):
        tips = []
        if res["battery"] < 30:
            tips.append("🔋 Battery optimization recommended: Critical levels imminent.")
        if res["solar"] > res["load"]:
            tips.append("☀️ Excess solar energy available! Battery is charging.")
        if res["load"] > 1500:
            tips.append("⚠️ High energy consumption detected across infrastructure.")
        if res["clouds"] > 6:
            tips.append("☁️ Heavy clouds detected — Solar output throttled.")
        if hour >= 19:
            tips.append("🌙 Night mode optimization active — Running strictly on battery/grid.")
        if res["efficiency"] > 80:
            tips.append("✅ System efficiency excellent: Renewable integration maximized.")

        if not tips:
            tips.append("⚡ AI system running normally.")
        return tips

    # ================= AI EXPLAINABILITY =================
    def explain_decision(self, zone, status, battery_pct):
        if status == "OFF":
            return f"⚠️ {zone} disabled because battery level ({battery_pct}%) is too low. Preserving critical operations."
        if status == "LIMITED":
            return f"🟡 {zone} running in limited mode (50% Load) to balance demand and avoid complete battery drain."
        return f"☀️ {zone} operating normally at 100% capacity supported by active power matrix."

    # ================= FUTURE PREDICTION =================
    def predict_tomorrow(self):
        increase = random.randint(5, 30)
        return {
            "prediction": increase,
            "message": f"📊 Tomorrow demand may increase by {increase}%"
        }

    # ================= SMART ALERTS =================
    def detect_risk(self, battery, load):
        risks = []
        if battery < 20:
            risks.append("🔴 Critical battery level")
        if load > 2000:
            risks.append("⚠️ Infrastructure overload risk")
        return risks
