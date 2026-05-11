import random
import math

class CityZone:
    def __init__(self, name, priority, consumption):
        self.name = name
        self.priority = priority # 1: Critical, 2: Important, 3: Non-Essential
        self.consumption = consumption # kW
        self.active = True

class SmartCityStrategic:
    def __init__(self):
        self.zones = []
        self.battery_capacity = 5000  # kWh (سعة البطارية الكلية)
        self.current_charge = 2500    # kWh (الشحن الحالي - نبدأ بـ 50%)
        self.grid_price_per_kwh = 1.2 # سعر الكيلوواط بالدرهم/الدولار
        self.co2_factor = 0.42        # kg CO2 per kWh

    def add_zone(self, zone):
        self.zones.append(zone)

    # --- ☀️ نظام توليد الطاقة المتطور ---
    def get_solar_production(self, hour, clouds):
        """محاكاة إنتاج الطاقة الشمسية مع تأثير السحب"""
        if 6 <= hour <= 18:
            peak = 2200 # زيادة الكفاءة القصوى
            # معادلة جيبية لمحاكاة حركة الشمس
            curve = math.sin((hour - 6) * math.pi / 12)
            production = peak * curve
            # تأثير السحب (كلما زادت السحب قل الإنتاج بنسبة تصل لـ 60%)
            cloud_impact = (clouds / 10) * 0.6
            production *= (1 - cloud_impact)
            return max(0, round(production, 2))
        return 0

    # --- 🔋 إدارة البطارية الذكية (Enterprise Logic) ---
    def update_battery(self, solar, load):
        """تحديث حالة البطارية بناءً على الفائض أو العجز"""
        net_energy = solar - load # الفرق بين الإنتاج والاستهلاك
        
        # تحديث الشحن (نعتبر التحديث يحدث كل ساعة dt=1)
        self.current_charge += net_energy
        
        # التأكد من عدم تجاوز الحدود
        self.current_charge = max(0, min(self.battery_capacity, self.current_charge))
        
        # إرجاع النسبة المئوية
        return round((self.current_charge / self.battery_capacity) * 100, 1)

    # --- 🧠 منطق اتخاذ القرار (AI Optimization) ---
    def optimize_infrastructure(self, solar, battery_pct):
        """اتخاذ قرارات ديناميكية لتشغيل أو إطفاء المناطق"""
        decisions = {}
        total_potential_load = sum(z.consumption for z in self.zones)
        
        for zone in self.zones:
            # حالة طوارئ: بطارية ضعيفة جداً ولا توجد شمس
            if battery_pct < 15 and solar < 200:
                if zone.priority > 1: # إطفاء كل شيء ما عدا الضروري جداً
                    zone.active = False
                    decisions[zone.name] = "OFF (Emergency)"
                else:
                    zone.active = True
                    decisions[zone.name] = "ON (Critical)"
            
            # حالة توفير: بطارية متوسطة
            elif battery_pct < 40 and solar < (total_potential_load * 0.5):
                if zone.priority >= 3:
                    zone.active = False
                    decisions[zone.name] = "OFF (Eco Mode)"
                elif zone.priority == 2:
                    zone.active = True
                    decisions[zone.name] = "LIMITED"
                else:
                    zone.active = True
                    decisions[zone.name] = "ON"
            
            # حالة وفرة طاقة
            else:
                zone.active = True
                decisions[zone.name] = "ON (Optimized)"
                
        return decisions

    # --- 💰 التحليل المالي (ROI Analytics) ---
    def calculate_roi(self, solar_used):
        """حساب الأموال التي تم توفيرها باستخدام الطاقة البديلة"""
        money_saved = solar_used * self.grid_price_per_kwh
        return round(money_saved, 2)

    # --- 🚀 مركز التحكم الرئيسي ---
    def control_center(self, hour, temp, clouds):
        solar = self.get_solar_production(hour, clouds)
        
        # حساب الحمل الفعلي بناءً على المناطق النشطة فقط
        active_load = sum(z.consumption for z in self.zones if z.active)
        
        battery_pct = self.update_battery(solar, active_load)
        decisions = self.optimize_infrastructure(solar, battery_pct)
        
        # حساب التوفير
        co2_saved = round(solar * self.co2_factor, 2)
        money_saved = self.calculate_roi(solar)
        
        return {
            "solar": solar,
            "load": active_load,
            "battery": battery_pct,
            "decisions": decisions,
            "co2_saved": co2_saved,
            "money_saved": money_saved,
            "efficiency": round((solar / active_load * 100), 1) if active_load > 0 else 100
        }

    # --- 🔍 شرح القرارات (Explainability) ---
    def explain_decision(self, zone_name, status, battery_pct):
        if "OFF" in status:
            return f"❌ تم إيقاف {zone_name} لأن مستوى البطارية ({battery_pct}%) منخفض جداً وللحفاظ على استمرارية العمليات الحرجة."
        if "LIMITED" in status:
            return f"⚠️ {zone_name} يعمل بقدرة محدودة لموازنة الأحمال وتجنب استنزاف البطارية قبل الغروب."
        return f"✅ {zone_name} يعمل بشكل كامل مدعوماً بالطاقة الشمسية المتوفرة."
