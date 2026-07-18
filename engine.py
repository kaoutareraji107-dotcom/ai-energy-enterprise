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
        self.battery_capacity = 5000  # kWh (سعة البطارية الإجمالية)
        self.current_charge = 2500    # kWh (الشحن الحالي الفعلي)
        self.max_solar_peak = 2200    # kW (أقصى إنتاج للألواح الشمسية ف أكادير)
        
    # ================= FINANCIAL ENGINE =================
    def calculate_financials(self, solar, actual_load):
        """حساب المؤشرات المالية الحقيقية للمقاولات ف المغرب"""
        # متوسط تعرفة الكهرباء الصناعية/التجارية ف المغرب (شاملة الرسوم الثابتة)
        tariff_per_kwh = 1.25 # درهم مغربي
        
        potential_cost = actual_load * tariff_per_kwh
        energy_covered = min(solar, actual_load)
        money_saved = energy_covered * tariff_per_kwh
        
        grid_needed = max(0, actual_load - solar)
        current_bill = grid_needed * tariff_per_kwh
        
        return {
            "money_saved": round(money_saved, 2),
            "current_bill": round(current_bill, 2),
            "potential_cost": round(potential_cost, 2)
        }

    # ================= MACHINE LEARNING DEMAND FORECASTING =================
    def train_demand_model(self, data_file="energy_log.csv"):
        """تدريب النموذج بناء على السيناريوهات الفيزيائية الواقعية"""
        if os.path.exists(data_file) and len(pd.read_csv(data_file)) > 10:
            df = pd.read_csv(data_file)
            X = np.array([[random.randint(15, 38), random.randint(0, 10)] for _ in range(len(df))])
            y = df['load'].values
        else:
            np.random.seed(42)
            X = np.random.uniform(15, 42, (100, 2)) # درجات الحرارة والغيوم
            X[:, 1] = np.random.uniform(0, 10, 100)
            # الاستهلاك الحقيقي المرتبط بالتكييف الصناعي والإنتاج ف الصيف
            y = 600 + (X[:, 0] * 28) + (X[:, 1] * 35) + np.random.normal(0, 30, 100)
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        return model

    def forecast_tomorrow_demand(self, tomorrow_temp, tomorrow_clouds):
        model = self.train_demand_model()
        input_data = np.array([[tomorrow_temp, tomorrow_clouds]])
        prediction = model.predict(input_data)[0]
        
        hours = list(range(24))
        hourly_forecast = []
        for h in hours:
            # منحنى حمل واقعي للمصانع والشركات (الذروة من 8 صباحا لـ 6 مساء)
            if 8 <= h <= 18:
                time_factor = 0.9 + (math.sin(h * math.pi / 12) * 0.1)
            else:
                time_factor = 0.45
            
            hourly_load = prediction * time_factor + np.random.normal(0, 15)
            hourly_forecast.append(round(max(250, hourly_load), 2))
            
        return round(prediction, 2), hourly_forecast

    def add_zone(self, zone):
        self.zones.append(zone)

    # ================= REAL SOLAR MODEL =================
    def get_solar(self, hour, clouds):
        """حساب إنتاج الإشعاع الشمسي الفعلي (GHI) حسب ساعات النهار وغيوم أكادير"""
        if 6 <= hour <= 18:
            curve = math.sin((hour - 6) * math.pi / 12)
            solar = self.max_solar_peak * curve
            # تأثير الغيوم الحقيقي على الألواح الكهروضوئية
            cloud_impact = (clouds / 10) * 0.75
            solar *= (1 - cloud_impact)
            return max(0, int(solar))
        return 0

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

    # ================= REAL BATTERY DYNAMICS =================
    def update_and_get_battery_pct(self, solar, actual_load):
        """محاكاة حركة الشحن والتفريغ الفيزيائية وكفاءة البطارية (Round-trip efficiency)"""
        net_energy = solar - actual_load
        
        # كفاءة الشحن والتفريغ 92% (فقدان طاقة واقعي ف المقاومات والحرارة)
        if net_energy > 0:
            net_energy *= 0.92 
        else:
            net_energy /= 0.92
            
        self.current_charge += (net_energy / 60) # تحويل القدرة اللحظية لكيلوواط ساعة
        self.current_charge = max(0, min(self.battery_capacity, self.current_charge))
        return round((self.current_charge / self.battery_capacity) * 100, 1)

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
        current_pct = round((self.current_charge / self.battery_capacity) * 100, 1)
        decisions = self.optimize_zones(solar, current_pct)
        actual_load = self.calculate_total_load(decisions)
        battery_pct = self.update_and_get_battery_pct(solar, actual_load)
        efficiency = self.calculate_efficiency(solar, actual_load)
        financials = self.calculate_financials(solar, actual_load)

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
        if load == 0: return 100
        return round(min(100, (solar / load) * 100), 2)

    def get_smart_recommendation(self, res, hour, language="EN"):
        tips = []
        if res["battery"] < 30: tips.append("🔋 Battery Optimization active: Critical depth of discharge warning.")
        if res["solar"] > res["load"]: tips.append("☀️ Smart Grid: Net positive generation. Charging battery bank.")
        if res["load"] > 1800: tips.append("⚠️ Load shedding algorithm prepared for non-essential zones.")
        return tips if tips else ["⚡ Edge controller operational."]

    def explain_decision(self, zone, status, battery_pct):
        if status == "OFF": return f"⚠️ {zone} isolated by AI to prevent battery degradation below safe threshold."
        if status == "LIMITED": return f"🟡 {zone} throttled to 50% duty cycle via PWM control to stabilize microgrid."
        return f"☀️ {zone} connected to primary renewable busbar. Power supply stable."

    def predict_tomorrow(self):
        return {"prediction": random.randint(3, 15)}
