import numpy_financial as npf

def calculate_residential_dev_cost(units, dev_cost_per_unit):
    return units * dev_cost_per_unit

def calculate_commercial_dev_cost(sqft, dev_cost_per_sqft):
    return sqft * dev_cost_per_sqft

def calculate_development_cost(units_or_sqft, dev_cost_per_sqft, avg_sqft_per_unit=None):
    """
    Generic development cost calculator.
    If avg_sqft_per_unit is provided, assumes residential product.
    Otherwise, assumes commercial sqft total.
    """
    if avg_sqft_per_unit is not None:
        total_sqft = units_or_sqft * avg_sqft_per_unit
    else:
        total_sqft = units_or_sqft
    return total_sqft * dev_cost_per_sqft

def calculate_irr(cashflows):
    try:
        irr = npf.irr(cashflows)
        return irr if irr is not None and not isinstance(irr, complex) else None
    except Exception as e:
        print(f"IRR calculation error: {e}")
        return None

def calculate_equity_multiple(cashflows):
    if not cashflows or cashflows[0] >= 0:
        return None
    try:
        total_inflows = sum(cashflows[1:])
        return total_inflows / abs(cashflows[0])
    except ZeroDivisionError:
        return None

def run_scenario(name, rent_per_unit, dev_cost_per_unit, units, opex_per_unit, absorption_years):
    print(f"\n--- Scenario: {name} ---")

    # Revenue
    annual_income = rent_per_unit * units
    total_income = annual_income * absorption_years

    # Costs
    total_cost = dev_cost_per_unit * units
    total_opex = opex_per_unit * units * absorption_years

    # Cashflows
    cashflows = [-total_cost]
    for _ in range(absorption_years):
        cashflows.append((annual_income - total_opex / absorption_years))

    irr = calculate_irr(cashflows)
    equity_multiple = calculate_equity_multiple(cashflows)

    print(f"Initial Investment: ${-cashflows[0]:,.0f}")
    print(f"Annual Income: ${annual_income:,.0f}")
    print(f"IRR: {irr:.2%}" if irr is not None else "IRR: Not calculable")
    print(f"Equity Multiple: {equity_multiple:.2f}x\n")

def find_break_even_year(cashflows):
    cumulative = 0
    for year, cf in enumerate(cashflows):
        cumulative += cf
        if cumulative >= 0:
            return year
    return None

# Optional: Run scenarios
scenarios = [
    {"name": "Base Case", "rent_per_unit": 3600, "dev_cost_per_unit": 450000, "units": 50, "opex_per_unit": 5000, "absorption_years": 5},
    {"name": "High Rent", "rent_per_unit": 4200, "dev_cost_per_unit": 450000, "units": 50, "opex_per_unit": 5000, "absorption_years": 5},
    {"name": "Low Rent, High Cost", "rent_per_unit": 3000, "dev_cost_per_unit": 480000, "units": 50, "opex_per_unit": 6000, "absorption_years": 5},
]
if __name__ == "__main__":
    for scenario in scenarios:
        run_scenario(**scenario)

