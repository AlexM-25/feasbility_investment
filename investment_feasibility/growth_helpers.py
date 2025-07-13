import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf

inflation = 0.03
import numpy_financial as npf

# Residential Helper Functions!!

# growth_changes.py

DEFAULT_CHURN_RATE = 0.2
DEFAULT_REABSORPTION_RATE = 0.5
DEFAULT_EARLY_OCCUPANCY_RATE = 0.25

def phase_absorption(total_units, absorption_rate, years):
    remaining = total_units
    absorption_schedule = []
    for _ in range(years):
        absorbed = min(int(total_units * absorption_rate), remaining)
        absorption_schedule.append(absorbed)
        remaining -= absorbed
        if remaining <= 0:
            break
    while len(absorption_schedule) < years:
        absorption_schedule.append(0)
    return absorption_schedule

def early_occupancy(units_absorbed, early_occupancy_rate=.25):
    return [round(units * early_occupancy_rate, 2) for units in units_absorbed]

def market_churn(units_absorbed, churn_rate=0.2):
    return [round(units * churn_rate, 2) for units in units_absorbed]

def net_occupancy(units_absorbed, churn_rate=0.2, reabsorption_rate=0.5, early_occupancy_rate=.25):
    churned_units = market_churn(units_absorbed, churn_rate)
    reabsorbed_units = [round(c * reabsorption_rate, 2) for c in churned_units]
    pre_rental = early_occupancy(units_absorbed, early_occupancy_rate)
    return [round(a - c + r + p, 2) for a, c, r, p in zip(units_absorbed, churned_units, reabsorbed_units, pre_rental)]

# Commercial Helper Functions!!

def phase_sqft_absorption(total_sqft, absorption_rate, years):
    remaining = total_sqft
    absorption_schedule = []
    for _ in range(years):
        absorbed = min(int(total_sqft * absorption_rate), remaining)
        absorption_schedule.append(absorbed)
        remaining -= absorbed
        if remaining <= 0:
            break
    while len(absorption_schedule) < years:
        absorption_schedule.append(0)
    return absorption_schedule

def early_sqft_occupancy(sqft_absorbed, early_occupancy_rate=0.2):
    return [round(sqft * early_occupancy_rate, 2) for sqft in sqft_absorbed]

def commercial_churn(sqft_absorbed, churn_rate=0.08):
    return [round(sqft * churn_rate, 2) for sqft in sqft_absorbed]

def net_sqft_occupancy(sqft_absorbed, total_sqft, churn_rate=0.08, reabsorption_rate=0.5, early_occupancy_rate=0.2):
    net = []
    running_total = 0
    for year, absorbed in enumerate(sqft_absorbed):
        churned = round(absorbed * churn_rate, 2)
        reabsorbed = round(churned * reabsorption_rate, 2)

        # Only apply early occupancy in the first year
        pre_leased = round(absorbed * early_occupancy_rate, 2) if year == 0 else 0

        leased_this_year = absorbed - churned + reabsorbed + pre_leased

        available = total_sqft - running_total
        leased_capped = min(leased_this_year, available)

        net.append(leased_capped)
        running_total += leased_capped

        if running_total >= total_sqft:
            # Stop further leasing if fully occupied
            net.extend([0] * (len(sqft_absorbed) - len(net)))
            break
    return net

def forecast_rental_income(sqft, rent_per_sqft, occupancy_rate, years, growth_rate): # Rental income collected
    incomes = []
    effective_rent = rent_per_sqft * occupancy_rate
    for year in range(years):
        income = sqft * effective_rent * ((1 + growth_rate) ** year)
        incomes.append(income)
    return incomes

def cap_net_occupancy(net_units, total_units):
    capped = []
    running_total = 0
    for n in net_units:
        available = total_units - running_total
        adjusted = min(n, available)
        capped.append(adjusted)
        running_total += adjusted
        if running_total >= total_units:
            capped.extend([0] * (len(net_units) - len(capped)))
            break
    return capped

# Example usage:
if __name__ == "__main__":
    # Example residential absorption - "Apartments and SF"
    # Residential inputs
    # Acreage needed:
    # Detached : 37.5 acres
    # Attached : 12.5 acres
    # Multi-Family : 7.5 acres
    # Res acreage = 57.5 acres

    product_types = {
        "Detached": {"total_units": 150, "absorption_rate": 0.15, "rent_per_unit": 3250},
        "Attached": {"total_units": 150, "absorption_rate": 0.20, "rent_per_unit": 2625},
        "Multi-Family": {"total_units": 150, "absorption_rate": 0.25, "rent_per_unit": 1925}
    }
    print("------ Residential Rental Revenue Forecast ------")
    for product, params in product_types.items():
        units_absorbed = phase_absorption(params["total_units"], params["absorption_rate"], years=20)
        raw_net_units = net_occupancy(units_absorbed)
        net_units = cap_net_occupancy(raw_net_units, params["total_units"])
        revenues = [round(units * params["rent_per_unit"] * 12, 2) for units in net_units]  # Annual rent

        print(f"\n{product}:")
        print(f"  Units Absorbed per Year: {units_absorbed}")
        formatted_units = ', '.join(f"{u:,.2f}" for u in net_units)
        print(f"  Net Occupied Units per Year: [{formatted_units}]")
        print(f"  Rental Revenues:")
        for i, revenue in enumerate(revenues, start=1):
            print(f"    Year {i}: ${revenue:,.2f}")

    # Example commercial rental forecast
    # Forecast rental income for different commercial types
    # Rentable square feet!
    # Assuming acreage:
    # Industrial : 6.6 acres
    # Office : 1.15 acres
    # Retail : 2.1 acres
    # Data Centers : .69 acres

    # Average rental prices are based on Colliers Q1 reporting for 2025
    commercial_types = {
        "Industrial": {"sqft": 100000, "rent_per_sqft": 12, "occupancy_rate": 0.915, "years": 20, "growth_rate": 0.02},
        "Office": {"sqft": 20000, "rent_per_sqft": 33.5, "occupancy_rate": 0.744, "years": 20, "growth_rate": 0.02},
        "Retail": {"sqft": 30000, "rent_per_sqft": 26.4, "occupancy_rate": 0.959, "years": 20, "growth_rate": 0.02},
        "Data Centers": {"sqft": 100000, "rent_per_sqft": 125, "occupancy_rate": 0.9, "years": 20, "growth_rate": 0.02},
        "Hotels": {"sqft": 35000, "rent_per_sqft": 4.5, "occupancy_rate": 0.7, "years": 20, "growth_rate": 0.02}
    }
    print("\n------ Commercial Rental Revenue Forecast (Absorption-Based) ------")
    for product, params in commercial_types.items():
        sqft_absorbed = phase_sqft_absorption(params["sqft"], 0.25, params["years"])
        net_sqft = net_sqft_occupancy(
            sqft_absorbed,
            total_sqft=params["sqft"],  # <- this is what was missing
            churn_rate=0.08,
            reabsorption_rate=0.5,
            early_occupancy_rate=0.2
        )
        revenues = [
            round(sqft * params["rent_per_sqft"] * ((1 + params["growth_rate"]) ** i), 2)
            for i, sqft in enumerate(net_sqft)
        ]
        print(f"\n{product}:")
        print(f"  Absorbed SF per Year: {sqft_absorbed}")
        print(f"  Net Leased SF per Year: {net_sqft}")
        print(f"  Rental Income per Year:")
        for i, rev in enumerate(revenues, start=1):
            print(f"    Year {i}: ${rev:,.2f}")




