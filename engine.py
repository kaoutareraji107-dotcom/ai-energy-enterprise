import math


class CityZone:
    def __init__(self, name, priority, consumption):
        self.name = name
        self.priority = priority  # 1: Critical, 2: Important, 3: Non-Essential
        self.consumption = consumption  # kW
        self.active = True


class SmartCityStrategic:
    def __init__(self):
        self.zones = []
        self.battery_capacity = 5000  # kWh
        self.current_charge = 2500  # kWh
        self.grid_price_per_kwh = 1.2
        self.co2_factor = 0.42  # kg CO2 per kWh

    def add_zone(self, zone):
        self.zones.append(zone)

    def get_solar_production(self, hour, clouds):
        """Simulate solar production with cloud impact."""
        if 6 <= hour <= 18:
            peak = 2200
            curve = math.sin((hour - 6) * math.pi / 12)
            production = peak * curve
            cloud_impact = (clouds / 10) * 0.6
            production *= 1 - cloud_impact
            return max(0, round(production, 2))
        return 0

    def update_battery(self, solar, load):
        """Update battery charge based on production and load."""
        net_energy = solar - load
        self.current_charge += net_energy
        self.current_charge = max(0, min(self.battery_capacity, self.current_charge))
        return round((self.current_charge / self.battery_capacity) * 100, 1)

    def optimize_infrastructure(self, solar, battery_pct):
        """Turn zones on/off dynamically based on energy availability."""
        decisions = {}
        total_potential_load = sum(z.consumption for z in self.zones)

        for zone in self.zones:
            if battery_pct < 15 and solar < 200:
                if zone.priority > 1:
                    zone.active = False
                    decisions[zone.name] = "OFF (Emergency)"
                else:
                    zone.active = True
                    decisions[zone.name] = "ON (Critical)"
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
            else:
                zone.active = True
                decisions[zone.name] = "ON (Optimized)"

        return decisions

    def calculate_roi(self, solar_used):
        """Calculate money saved by using generated solar energy."""
        money_saved = solar_used * self.grid_price_per_kwh
        return round(money_saved, 2)

    def calculate_co2_saved(self, solar_used):
        return round(solar_used * self.co2_factor, 2)

    def control_center(self, hour, temp, clouds):
        solar = self.get_solar_production(hour, clouds)
        active_load = sum(z.consumption for z in self.zones if z.active)
        battery_pct = self.update_battery(solar, active_load)
        decisions = self.optimize_infrastructure(solar, battery_pct)

        co2_saved = self.calculate_co2_saved(solar)
        money_saved = self.calculate_roi(solar)

        return {
            "solar": solar,
            "load": active_load,
            "battery": battery_pct,
            "decisions": decisions,
            "co2_saved": co2_saved,
            "money_saved": money_saved,
            "efficiency": round((solar / active_load * 100), 1) if active_load > 0 else 100,
        }

    def explain_decision(self, zone_name, status, battery_pct):
        if "OFF" in status:
            return (
                f"تم إيقاف {zone_name} لأن مستوى البطارية ({battery_pct}%) منخفض "
                "وللحفاظ على استمرارية العمليات الحرجة."
            )
        if "LIMITED" in status:
            return (
                f"{zone_name} يعمل بقدرة محدودة لموازنة الأحمال وتجنب استنزاف "
                "البطارية قبل الغروب."
            )
        return f"{zone_name} يعمل بشكل كامل مدعوما بالطاقة الشمسية المتوفرة."

    def get_smart_recommendation(self, res, hour, language="English"):
        recommendations = []

        if res["battery"] < 20:
            recommendations.append("Battery is critically low. Keep only priority zones active.")
        elif res["battery"] < 40:
            recommendations.append("Battery is moderate. Use eco mode for non-essential zones.")
        else:
            recommendations.append("Battery level is healthy. Current energy strategy is stable.")

        if res["solar"] < res["load"]:
            recommendations.append("Solar production is below demand. Consider reducing optional loads.")
        else:
            recommendations.append("Solar production is covering current demand efficiently.")

        if hour >= 17:
            recommendations.append("Sunset is approaching. Preserve battery for evening operations.")

        recommendations.append(f"Estimated savings: {res['money_saved']} from solar energy usage.")
        return recommendations


