import random
import math

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
        # إضافة خصائص حقيقية للبطارية للحفاظ على حالة الشحن بمرور الوقت
        self.battery_capacity = 5000  # kWh
        self.current_charge = 2500    # kWh (تبدأ بـ 50%)

    # ================= ADD ZONE =================
    def add_zone(self, zone):
        self.zones.append(zone)

    # ================= SOLAR MODEL =================
    def get_solar(self, hour, clouds):
        if 6 <= hour <= 18:
            peak = 1800
            curve = math.sin((hour - 6) * math.pi / 12)
            solar = peak * curve
            # تعديل تأثير الغيوم ليكون نسبي منطقي (Clouds من 0 لـ 10)
            cloud_impact = (clouds / 10) * 0.6
            solar *= (1 - cloud_impact)
            return max(0, int(solar))
        return 0

    # ================= LOAD CALCULATION =================
    def calculate_total_load(self, decisions=None):
        """حساب الأحمال الفعلية بناءً على حالة المناطق الحالية أو القرارات المتخذة"""
        total = 0
        for zone in self.zones:
            if decisions and zone.name in decisions:
                status = decisions[zone.name]
                if status == "ON":
                    total += zone.consumption
                elif status == "LIMITED":
                    total += zone.consumption * 0.5  # نصف الاستهلاك في وضع الموازنة
                # لو OFF كيزيد 0
            else:
                if zone.active:
                    total += zone.consumption
        return total

    # ================= BATTERY INTELLIGENCE =================
    def update_and_get_battery_pct(self, solar, actual_load):
        """تحديث السعة الحقيقية للبطارية بناءً على الفائض أو النقص الفعلي في الطاقة"""
        net_energy = solar - actual_load
        # محاكاة التحديث (الإنتاج بالكيلوواط في الساعة)
        self.current_charge += net_energy
        # نضمن أن الشحن ما يفوتش السعة وما ينزلش تحت الصفر
        self.current_charge = max(0, min(self.battery_capacity, self.current_charge))
        
        # إرجاع النسبة المئوية
        return round((self.current_charge / self.battery_capacity) * 100, 1)

    # ================= AI DECISIONS =================
    def optimize_zones(self, solar, current_battery_pct):
        """اتخاذ القرارات بناءً على الطاقة الشمسية المتاحة ونسبة البطارية الحالية"""
        decisions = {}
        # حساب مجموع الأحمال المحتملة لو كانت كل المناطق مشغلة
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
    def control_center(self, hour, temp, clouds):
        # 1. حساب إنتاج الطاقة الشمسية أولاً
        solar = self.get_solar(hour, clouds)
        
        # 2. معرفة نسبة البطارية الحالية قبل أخذ القرار
        current_pct = round((self.current_charge / self.battery_capacity) * 100, 1)
        
        # 3. الـ AI كياخد القرار بناءً على المعطيات الحالية
        decisions = self.optimize_zones(solar, current_pct)
        
        # 4. دابا كنحسبو الـ Load الفعلي (الحقيقي) اللي غيتستهلك بناء على القرارات
        actual_load = self.calculate_total_load(decisions)
        
        # 5. كنحدثو البطارية بالـ Load الفعلي الجديد ونحصلو على النسبة المحدثة
        battery_pct = self.update_and_get_battery_pct(solar, actual_load)
        
        # 6. حساب الكفاءة العامة للنظام
        efficiency = self.calculate_efficiency(solar, actual_load)

        return {
            "solar": solar,
            "load": actual_load,
            "battery": battery_pct,
            "efficiency": efficiency,
            "temperature": temp,
            "clouds": clouds,
            "decisions": decisions
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
