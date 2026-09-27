import math
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


class CityZone:
    def __init__(self, name: str, priority: int, consumption_kw: float):
        self.name = name
        self.priority = priority  # 1: Critical, 2: Important, 3: Non-Essential
        self.consumption_kw = float(consumption_kw)  # Peak load in kW
        self.active = True


class SmartCityStrategic:
    """
    AI Energy Enterprise - Enterprise Microgrid Core Engine
    ------------------------------------------------------
    - Real-time Microgrid Load and Battery Dispatch Strategy.
    - Deterministic Solar Physics & Demand Predictive Forecasting via Random Forest.
    - CO2 Footprint & Industrial Tariff Calculations.
    """

    def __init__(
        self,
        system_capex_mad: float = 150000.0,
        battery_capacity_kwh: float = 5000.0,
        initial_charge_kwh: float = 2500.0,
        max_solar_peak_kw: float = 2200.0,
        battery_efficiency: float = 0.92,
        co2_factor_kg_per_kwh: float = 0.73,
    ):
        self.zones = []

        # System parameters
        self.battery_capacity_kwh = max(0.0, battery_capacity_kwh)
        self.current_charge_kwh = max(
            0.0,
            min(initial_charge_kwh, self.battery_capacity_kwh)
        )
        self.max_solar_peak_kw = max(0.0, max_solar_peak_kw)
        self.battery_efficiency = min(max(battery_efficiency, 0.01), 1.0)

        # Financial parameters
        self.system_capex_mad = max(0.0, system_capex_mad)
        self.co2_factor = max(0.0, co2_factor_kg_per_kwh)

        self.model = None
        self.init_ml_model()

    # ============================================================
    # 1. ZONES MANAGEMENT
    # ============================================================

    def add_zone(self, zone: CityZone):
        self.zones.append(zone)

    def clear_zones(self):
        self.zones = []

    def get_total_requested_load(self) -> float:
        return float(sum(z.consumption_kw for z in self.zones if z.active))

    # ============================================================
    # 2. FINANCIAL ENGINE & TARIFFS
    # ============================================================

    def get_tariff_mad_per_kwh(self, hour: int) -> float:
        """Standard Time-of-Use Industrial Tariff Profile."""
        return 1.65 if 17 <= hour <= 22 else 1.05

    def calculate_financials(
        self,
        load_kwh: float,
        solar_to_load_kwh: float,
        battery_to_load_kwh: float,
        grid_import_kwh: float,
        hour: int,
        annualized_daily_profile_savings_mad: float | None = None,
    ):
        tariff = self.get_tariff_mad_per_kwh(hour)

        load_kwh = max(0.0, float(load_kwh))
        solar_to_load_kwh = max(0.0, float(solar_to_load_kwh))
        battery_to_load_kwh = max(0.0, float(battery_to_load_kwh))
        grid_import_kwh = max(0.0, float(grid_import_kwh))

        potential_grid_cost_mad = load_kwh * tariff
        current_grid_cost_mad = grid_import_kwh * tariff

        money_saved_mad = max(
            0.0,
            potential_grid_cost_mad - current_grid_cost_mad
        )

        annual_savings = (
            max(0.0, annualized_daily_profile_savings_mad) * 365.0
            if annualized_daily_profile_savings_mad is not None
            else None
        )

        if annual_savings is not None and self.system_capex_mad > 0:
            payback_years = self.system_capex_mad / annual_savings if annual_savings > 0 else None
            roi_percentage = (annual_savings / self.system_capex_mad) * 100.0
        else:
            payback_years = None
            roi_percentage = None

        return {
            "money_saved_mad": round(money_saved_mad, 2),
            "current_bill_mad": round(current_grid_cost_mad, 2),
            "potential_cost_mad": round(potential_grid_cost_mad, 2),
            "tariff_mad_kwh": round(tariff, 3),
            "load_kwh": round(load_kwh, 3),
            "solar_to_load_kwh": round(solar_to_load_kwh, 3),
            "battery_to_load_kwh": round(battery_to_load_kwh, 3),
            "grid_import_kwh": round(grid_import_kwh, 3),
            "annual_savings_mad": round(annual_savings, 2) if annual_savings is not None else None,
            "payback_years": round(payback_years, 2) if payback_years is not None else None,
            "roi_percentage": round(roi_percentage, 2) if roi_percentage is not None else None,
        }

    def calculate_daily_financial_projection(
        self,
        hourly_load_kw,
        hourly_solar_kw,
        start_hour: int = 0,
    ):
        if len(hourly_load_kw) != 24 or len(hourly_solar_kw) != 24:
            raise ValueError("hourly_load_kw and hourly_solar_kw must contain 24 values.")

        original_charge = self.current_charge_kwh
        daily_savings = 0.0
        daily_grid_cost = 0.0
        daily_potential_cost = 0.0

        try:
            self.current_charge_kwh = original_charge

            for index in range(24):
                hour = (start_hour + index) % 24
                load_kw = max(0.0, float(hourly_load_kw[index]))
                solar_kw = max(0.0, float(hourly_solar_kw[index]))

                flow = self.calculate_energy_flow(
                    solar_kw=solar_kw,
                    load_kw=load_kw,
                    delta_hours=1.0,
                    allow_battery=True,
                )

                financials = self.calculate_financials(
                    load_kwh=flow["load_kwh"],
                    solar_to_load_kwh=flow["solar_to_load_kwh"],
                    battery_to_load_kwh=flow["battery_to_load_kwh"],
                    grid_import_kwh=flow["grid_import_kwh"],
                    hour=hour,
                )

                daily_savings += financials["money_saved_mad"]
                daily_grid_cost += financials["current_bill_mad"]
                daily_potential_cost += financials["potential_cost_mad"]

        finally:
            self.current_charge_kwh = original_charge

        annual_savings = daily_savings * 365.0

        if self.system_capex_mad > 0 and annual_savings > 0:
            payback_years = self.system_capex_mad / annual_savings
            roi_percentage = (annual_savings / self.system_capex_mad) * 100.0
        else:
            payback_years = None
            roi_percentage = None

        return {
            "daily_savings_mad": round(daily_savings, 2),
            "annual_savings_mad": round(annual_savings, 2),
            "daily_grid_cost_mad": round(daily_grid_cost, 2),
            "daily_potential_cost_mad": round(daily_potential_cost, 2),
            "payback_years": round(payback_years, 2) if payback_years is not None else None,
            "roi_percentage": round(roi_percentage, 2) if roi_percentage is not None else None,
        }

    # ============================================================
    # 3. MACHINE LEARNING ENGINE
    # ============================================================

    def init_ml_model(self, data_file="energy_log.csv"):
        if os.path.exists(data_file):
            try:
                df = pd.read_csv(data_file)
                required_columns = {"temp", "clouds", "load_kw"}

                if len(df) >= 10 and required_columns.issubset(df.columns):
                    clean_df = df[["temp", "clouds", "load_kw"]].dropna()

                    if len(clean_df) >= 10:
                        X = clean_df[["temp", "clouds"]].values
                        y = clean_df["load_kw"].values

                        self.model = RandomForestRegressor(
                            n_estimators=100, random_state=42, n_jobs=-1
                        )
                        self.model.fit(X, y)
                        return
            except Exception:
                pass

        temps = np.linspace(15, 42, 200)
        clouds = np.linspace(0, 10, 200)
        X = np.column_stack((temps, clouds))
        y = 400 + (X[:, 0] * 25) + (X[:, 1] * 15)

        self.model = RandomForestRegressor(
            n_estimators=100, random_state=42, n_jobs=-1
        )
        self.model.fit(X, y)

    def forecast_tomorrow_demand(
        self,
        tomorrow_temp: float,
        tomorrow_clouds: float,
    ):
        if self.model is None:
            self.init_ml_model()

        prediction = float(
            self.model.predict([[float(tomorrow_temp), float(tomorrow_clouds)]])[0]
        )

        hourly_forecast = []
        for h in range(24):
            if 8 <= h <= 18:
                time_factor = 0.85 + (math.sin((h - 8) * math.pi / 10) * 0.25)
            else:
                time_factor = 0.35

            hourly_load = max(100.0, prediction * time_factor)
            hourly_forecast.append(round(hourly_load, 2))

        return round(prediction, 2), hourly_forecast

    # ============================================================
    # 4. SOLAR & ENERGY FLOW
    # ============================================================

    def get_solar_kw(self, hour: int, clouds: float) -> float:
        hour = int(hour)
        clouds = min(10.0, max(0.0, float(clouds)))

        if 6 <= hour <= 18:
            sun_angle = math.sin((hour - 6) * math.pi / 12)
            solar_power = self.max_solar_peak_kw * sun_angle
            cloud_attenuation = 1.0 - ((clouds / 10.0) * 0.70)
            return max(0.0, round(solar_power * cloud_attenuation, 2))

        return 0.0

    def calculate_energy_flow(
        self,
        solar_kw: float,
        load_kw: float,
        delta_hours: float = 1.0,
        allow_battery: bool = True,
    ):
        solar_kw = max(0.0, float(solar_kw))
        load_kw = max(0.0, float(load_kw))

        solar_kwh = solar_kw * delta_hours
        load_kwh = load_kw * delta_hours

        solar_to_load_kwh = min(solar_kwh, load_kwh)
        remaining_load_kwh = max(0.0, load_kwh - solar_to_load_kwh)
        excess_solar_kwh = max(0.0, solar_kwh - solar_to_load_kwh)

        battery_charge_kwh = 0.0
        battery_discharge_kwh = 0.0

        if allow_battery and excess_solar_kwh > 0:
            available_capacity_kwh = max(0.0, self.battery_capacity_kwh - self.current_charge_kwh)
            energy_storable_kwh = min(excess_solar_kwh * self.battery_efficiency, available_capacity_kwh)

            if energy_storable_kwh > 0:
                solar_used_for_charging_kwh = energy_storable_kwh / self.battery_efficiency
                battery_charge_kwh = energy_storable_kwh
                self.current_charge_kwh += battery_charge_kwh
                excess_solar_kwh = max(0.0, excess_solar_kwh - solar_used_for_charging_kwh)

        if allow_battery and remaining_load_kwh > 0:
            max_deliverable_kwh = self.current_charge_kwh * self.battery_efficiency
            battery_to_load_kwh = min(remaining_load_kwh, max_deliverable_kwh)

            if battery_to_load_kwh > 0:
                battery_discharge_kwh = battery_to_load_kwh
                battery_energy_removed_kwh = battery_to_load_kwh / self.battery_efficiency
                self.current_charge_kwh = max(0.0, self.current_charge_kwh - battery_energy_removed_kwh)
                remaining_load_kwh = max(0.0, remaining_load_kwh - battery_to_load_kwh)
        else:
            battery_to_load_kwh = 0.0

        grid_import_kwh = max(0.0, remaining_load_kwh)
        renewable_to_load_kwh = solar_to_load_kwh + battery_to_load_kwh
        curtailed_solar_kwh = max(0.0, excess_solar_kwh)

        soc_percentage = (
            (self.current_charge_kwh / self.battery_capacity_kwh) * 100.0
            if self.battery_capacity_kwh > 0
            else 0.0
        )

        return {
            "load_kwh": round(load_kwh, 3),
            "solar_kwh": round(solar_kwh, 3),
            "solar_to_load_kwh": round(solar_to_load_kwh, 3),
            "solar_to_battery_kwh": round(
                battery_charge_kwh / self.battery_efficiency if self.battery_efficiency > 0 else 0.0, 3
            ),
            "battery_to_load_kwh": round(battery_to_load_kwh, 3),
            "grid_import_kwh": round(grid_import_kwh, 3),
            "curtailed_solar_kwh": round(curtailed_solar_kwh, 3),
            "renewable_to_load_kwh": round(renewable_to_load_kwh, 3),
            "battery_charge_kwh": round(battery_charge_kwh, 3),
            "battery_discharge_kwh": round(battery_discharge_kwh, 3),
            "battery_soc_pct": round(soc_percentage, 1),
        }

    def calculate_co2_saved_kg(self, solar_to_load_kwh: float) -> float:
        return round(max(0.0, float(solar_to_load_kwh)) * self.co2_factor, 2)

    # ============================================================
    # 5. INTEGRATED CONTROL CENTER (RESTORED & OPTIMIZED)
    # ============================================================

    def control_center(self, hour: int, temp: float, clouds: float):
        """Dispatches relays and evaluates real-time system performance."""
        solar_kw = self.get_solar_kw(hour, clouds)
        total_requested_load = self.get_total_requested_load()

        decisions = {}
        for z in self.zones:
            decisions[z.name] = "ON" if z.active else "OFF"

        flow = self.calculate_energy_flow(
            solar_kw=solar_kw,
            load_kw=total_requested_load,
            delta_hours=1.0,
            allow_battery=True
        )

        financials = self.calculate_financials(
            load_kwh=flow["load_kwh"],
            solar_to_load_kwh=flow["solar_to_load_kwh"],
            battery_to_load_kwh=flow["battery_to_load_kwh"],
            grid_import_kwh=flow["grid_import_kwh"],
            hour=hour
        )

        co2_saved = self.calculate_co2_saved_kg(flow["solar_to_load_kwh"])

        return {
            "solar_kw": solar_kw,
            "load_kw": total_requested_load,
            "battery_soc": flow["battery_soc_pct"],
            "co2_saved_kg": co2_saved,
            "decisions": decisions,
            "energy_flow": flow,
            "financials": financials
        }
