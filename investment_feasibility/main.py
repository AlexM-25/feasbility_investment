import numpy_financial as npf
import pandas as pd
from growth_helpers import (phase_absorption, net_occupancy, DEFAULT_CHURN_RATE,
                            DEFAULT_REABSORPTION_RATE, phase_sqft_absorption,DEFAULT_EARLY_OCCUPANCY_RATE,
                            commercial_churn, net_sqft_occupancy,forecast_rental_income,
                            cap_net_occupancy)
from inputs import get_user_inputs
from finance import (calculate_equity_multiple, find_break_even_year, calculate_irr,
                     calculate_development_cost, calculate_residential_dev_cost, calculate_commercial_dev_cost)

def fetch_average_sqft(zip_code, product_type=None):
    defaults = {
        "detached": 1600,
        "townhome": 1300,
        "multifamily": 950
    }
    return defaults.get(product_type, 1250)

def residential_model(custom_products: dict, shared_acq_cost: float, dev_cost_per_sqft: float, zip_code: str, years: int = 20):
    results = []
    portfolio_cashflows = [0] * years  # to sum across products (excluding acq cost)
    for name, vals in custom_products.items():
        avg_sqft = fetch_average_sqft(zip_code, product_type=vals.get("product_type", "").lower())

        absorbed = phase_absorption(vals["units"], vals["absorption_rate"], years)
        net_units = cap_net_occupancy(net_occupancy(
            absorbed,
            churn_rate=DEFAULT_CHURN_RATE,
            reabsorption_rate=DEFAULT_REABSORPTION_RATE,
            early_occupancy_rate=DEFAULT_EARLY_OCCUPANCY_RATE
        ), vals["units"])

        revenue_schedule = [units * vals["rental_price"] * 12 for units in net_units]
        total_revenue = sum(revenue_schedule)
        total_dev_cost = calculate_residential_dev_cost(vals["units"], vals["dev_cost"])

        yearly_opex = [vals["opex_per_unit"] * occupied for occupied in net_units]
        yearly_noi = [revenue_schedule[i] - yearly_opex[i] for i in range(years)]
        total_opex = sum(yearly_opex)
        noi = total_revenue - total_opex

        # Exclude acquisition cost at product level
        cashflows = [-total_dev_cost] + yearly_noi
        irr = calculate_irr(cashflows)
        equity_multiple = calculate_equity_multiple(cashflows)
        be_year = find_break_even_year(cashflows)


        for i in range(years):
            portfolio_cashflows[i] += yearly_noi[i]

        results.append({
            "Product": name,
            "Units": vals["units"],
            "Total_Revenue": total_revenue,
            "Acquisition_Cost": 0,  # for display only
            "Development_Cost": total_dev_cost,
            "Total_OpEx": total_opex,
            "NOI": noi,
            "IRR": irr,
            "Equity_Multiple": equity_multiple,
            "Break_Even_Year": be_year
        })
    return pd.DataFrame(results), portfolio_cashflows

def commercial_model(custom_products: dict, years=20):
    results = []
    portfolio_cashflows = [0] * years
    for prod_name, vals in custom_products.items():
        absorbed_schedule = phase_sqft_absorption(vals["sqft"], vals["absorption_rate"], years)

        raw_net_units = net_sqft_occupancy(
            absorbed_schedule,
            total_sqft=vals["sqft"],
            churn_rate=DEFAULT_CHURN_RATE,
            reabsorption_rate=DEFAULT_REABSORPTION_RATE,
            early_occupancy_rate=DEFAULT_EARLY_OCCUPANCY_RATE
        )

        net_units = cap_net_occupancy(raw_net_units, vals["sqft"])

        revenue_schedule = [round(units * vals["rental_price"] * 12, 2) for units in net_units]
        total_revenue = sum(revenue_schedule)

        dev_cost_per_sqft = vals.get("dev_cost", 0)
        total_dev_cost = calculate_commercial_dev_cost(vals["sqft"], dev_cost_per_sqft)
        opex_per_sqft = vals.get("opex_per_sqft", 6.0)
        total_opex = opex_per_sqft * vals["sqft"]

        yearly_noi = [revenue_schedule[i] - absorbed_schedule[i] * opex_per_sqft for i in range(years)]
        NOI = total_revenue - total_opex

        # Exclude acquisition cost at product level
        cashflows = [-total_dev_cost] + yearly_noi
        irr = calculate_irr(cashflows)
        equity_multiple = calculate_equity_multiple(cashflows)
        break_even_year = find_break_even_year(cashflows)

        # Add product cashflow to portfolio-level cashflow
        for i in range(years):
            portfolio_cashflows[i] += yearly_noi[i]

        net_cash_flow = NOI - total_dev_cost
        cap_rate = NOI / vals.get("acq_cost", 1) if vals.get("acq_cost", 0) else None  # optional display
        dscr = NOI / total_dev_cost if total_dev_cost > 0 else None

        results.append({
            "Product": prod_name,
            "SqFt_Planned": vals["sqft"],
            "Total_Revenue": total_revenue,
            "Acquisition_Cost": 0,
            "Development_Cost": total_dev_cost,
            "Total_OpEx": total_opex,
            "NOI": NOI,
            "Net_Cash_Flow": net_cash_flow,
            "DSCR": dscr,
            "Capitalization_Rate": cap_rate,
            "IRR": irr,
            "Equity_Multiple": equity_multiple,
            "Break_Even_Year": break_even_year,
        })
    return pd.DataFrame(results), portfolio_cashflows

def mixed_use_model(custom_products, dev_cost_per_sqft_res, dev_cost_per_sqft_com, zip_code, years=20):
    results = []

    for name, vals in custom_products.items():
        res_vals = vals.get("residential", {})
        com_vals = vals.get("commercial", {})
        acq_cost = vals.get("acq_cost", 0)

        # ----------- Residential Component -----------
        res_total_rev = 0
        res_dev_cost = 0
        res_opex = 0
        res_cashflow = [0] * years

        if res_vals and res_vals.get("units", 0) > 0:
            avg_sqft_res = fetch_average_sqft(zip_code, product_type=res_vals.get("product_type", "").lower())
            units = res_vals["units"]
            rent = res_vals["rental_price"]
            opex_per_unit = res_vals.get("opex_per_unit", 5000)
            absorption_rate = res_vals.get("absorption_rate", 0.25)

            res_absorbed = phase_absorption(units, absorption_rate, years)
            res_net_units = cap_net_occupancy(net_occupancy(
                res_absorbed,
                churn_rate=DEFAULT_CHURN_RATE,
                reabsorption_rate=DEFAULT_REABSORPTION_RATE,
                early_occupancy_rate=DEFAULT_EARLY_OCCUPANCY_RATE
            ), units)

            res_revenue = [u * rent * 12 for u in res_net_units]
            res_opex_list = [u * opex_per_unit for u in res_net_units]
            res_cashflow = [res_revenue[i] - res_opex_list[i] for i in range(years)]

            res_total_rev = sum(res_revenue)
            res_opex = sum(res_opex_list)
            res_dev_cost = units * res_vals["dev_cost"]

        # ----------- Commercial Component -----------
        com_total_rev = 0
        com_dev_cost = 0
        com_opex = 0
        com_cashflow = [0] * years

        if com_vals and isinstance(com_vals, dict):
            for com_name, com_prod in com_vals.items():
                try:
                    com_sqft = com_prod.get("sqft", 0)
                    if com_sqft <= 0:
                        continue

                    absorption_rate = com_prod.get("absorption_rate", 0.25)
                    churn_rate = com_prod.get("churn_rate", DEFAULT_CHURN_RATE)
                    reabsorption_rate = com_prod.get("reabsorption_rate", DEFAULT_REABSORPTION_RATE)
                    early_occupancy_rate = com_prod.get("early_occupancy_rate", DEFAULT_EARLY_OCCUPANCY_RATE)
                    rent = com_prod.get("rental_price", 0)
                    opex_rate = com_prod.get("opex_per_sqft", 6.0)
                    dev_cost_rate = com_prod.get("dev_cost", dev_cost_per_sqft_com)

                    com_absorbed = phase_sqft_absorption(com_sqft, absorption_rate, years)
                    com_net_units = cap_net_occupancy(net_sqft_occupancy(
                        com_absorbed,
                        total_sqft=com_sqft,
                        churn_rate=churn_rate,
                        reabsorption_rate=reabsorption_rate,
                        early_occupancy_rate=early_occupancy_rate
                    ), com_sqft)

                    com_revenue = [sf * rent * 12 for sf in com_net_units]
                    com_opex_list = [a * opex_rate for a in com_absorbed]
                    com_cf = [com_revenue[i] - com_opex_list[i] for i in range(years)]

                    com_total_rev += sum(com_revenue)
                    com_opex += sum(com_opex_list)
                    com_dev_cost += com_sqft * dev_cost_rate
                    com_cashflow = [com_cashflow[i] + com_cf[i] for i in range(years)]
                except Exception as e:
                    print(f"⚠️ Error processing commercial product '{com_name}': {e}")

        # ----------- Combined Metrics -----------
        total_revenue = res_total_rev + com_total_rev
        total_dev_cost = res_dev_cost + com_dev_cost
        total_opex = res_opex + com_opex
        total_cons_cost = acq_cost + total_dev_cost
        total_noi = total_revenue - total_opex

        combined_cashflow = [res + com for res, com in zip(res_cashflow, com_cashflow)]
        cashflows = [-total_cons_cost] + combined_cashflow

        irr = calculate_irr(cashflows)
        equity_multiple = calculate_equity_multiple(cashflows)
        break_even_year = find_break_even_year(cashflows)

        results.append({
            "Product": name,
            "Category": "Mixed-Use",
            "Total_Revenue": total_revenue,
            "Acquisition_Cost": acq_cost,
            "Development_Cost": total_dev_cost,
            "Total_OpEx": total_opex,
            "NOI": total_noi,
            "Net_Cash_Flow": total_noi - total_cons_cost,
            "IRR": irr,
            "Equity_Multiple": equity_multiple,
            "Break_Even_Year": break_even_year
        })

    return pd.DataFrame(results)

def format_and_display_results(df, category_label, file_name, portfolio_irr=None, portfolio_em=None, portfolio_be=None):
    if df.empty:
        print(f"\nNo data to display for {category_label} developments.\n")
        return

    print(f"\n{'=' * 60}")
    print(f"{category_label.upper()} DEVELOPMENT SUMMARY")
    print(f"{'=' * 60}")

    currency_cols = [
        "Total_Revenue", "Acquisition_Cost", "Development_Cost",
        "Total_OpEx", "NOI", "Net_Cash_Flow"
    ]
    for col in currency_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"${x:,.0f}")

    if "IRR" in df.columns:
        df["IRR"] = df["IRR"].apply(lambda x: f"{x:.2%}" if x is not None else "N/A")
    if "DSCR" in df.columns:
        df["DSCR"] = df["DSCR"].apply(lambda x: f"{x:.2f}" if x is not None else "N/A")
    if "Capitalization_Rate" in df.columns:
        df["Capitalization_Rate"] = df["Capitalization_Rate"].apply(lambda x: f"{x:.2%}" if x is not None else "N/A")
    if "Equity_Multiple" in df.columns:
        df["Equity_Multiple"] = df["Equity_Multiple"].apply(lambda x: f"{x:.2f}x" if x is not None else "N/A")
    if "Break_Even_Year" in df.columns:
        df["Break_Even_Year"] = df["Break_Even_Year"].apply(lambda x: f"Year {x}" if x is not None else "N/A")

    if "IRR" in df.columns:
        df.sort_values(by="IRR", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)

    display_df = df.drop(columns=[col for col in df.columns if col.startswith("Annual_")], errors="ignore")
    print(display_df.to_string(index=False))

    # 👇 NEW: Portfolio-Level Metrics
    print(f"\n📊 PORTFOLIO-LEVEL METRICS ({category_label.upper()}):")
    if portfolio_irr is not None:
        print(f"   • IRR: {portfolio_irr:.2%}")
    if portfolio_em is not None:
        print(f"   • Equity Multiple: {portfolio_em:.2f}x")
    if portfolio_be is not None:
        print(f"   • Break-Even Year: Year {portfolio_be}")

    print(f"\nExported summary to: {file_name}\n")
    df.to_csv(file_name, index=False)

def validate_entry(entry):
    required_keys = ["product", "category"]
    if not all(k in entry for k in required_keys):
        return False

    cat = entry.get("category", "").lower()

    if cat == "residential" and "units" not in entry:
        return False
    if cat == "commercial" and "sqft" not in entry:
        return False
    if cat == "mixed-use":
        res_valid = "residential" in entry and any(
            isinstance(v, dict) and "units" in v for v in entry["residential"].values()
        )
        com_valid = "commercial" in entry and any(
            isinstance(v, dict) and "sqft" in v for v in entry["commercial"].values()
        )
        return res_valid and com_valid

    return True

if __name__ == "__main__":
    residential_products = {}
    commercial_products = {}
    mixed_use_products = {}

    product_input = get_user_inputs()

    for entry in product_input:
        if not isinstance(entry, dict):
            print(f"⚠️ Skipping invalid entry: {entry}")
            continue

        # Normalize keys
        entry = {k.strip().lower(): v for k, v in entry.items()}

        if not validate_entry(entry):
            print(f"⚠️ Skipping incomplete entry: {entry.get('product', 'Unknown')}")
            continue

        name = entry.get("product", "Unnamed")
        category = entry.get("category", "").strip().lower()

        if "acq cost" in entry:
            entry["acq_cost"] = entry.pop("acq cost")

        if category == "residential":
            residential_products[name] = entry
        elif category == "commercial":
            if "square_feet" in entry:
                entry["sqft"] = entry.pop("square_feet")
            if "opex_per_unit" in entry:
                entry["opex_per_sqft"] = entry.pop("opex_per_unit")
            elif "opex" in entry:
                entry["opex_per_sqft"] = entry.pop("opex")
            if "opex_per_sqft" not in entry:
                entry["opex_per_sqft"] = 6.0
            commercial_products[name] = entry
        elif category == "mixed-use":
            if "residential" in entry:
                for k, v in entry["residential"].items():
                    if "opex" not in v and "opex_per_unit" in v:
                        v["opex_per_unit"] = v.pop("opex_per_unit")
            if "commercial" in entry:
                for k, v in entry["commercial"].items():
                    if "opex" not in v and "opex_per_sqft" in v:
                        v["opex_per_sqft"] = v.pop("opex_per_sqft")

            res_data = entry.get("residential", {})
            com_data = entry.get("commercial", {})
            has_valid_res = isinstance(res_data, dict) and any(
                isinstance(v, dict) and "units" in v for v in res_data.values()
            )
            has_valid_com = isinstance(com_data, dict) and any(
                isinstance(v, dict) and "sqft" in v for v in com_data.values()
            )
            if has_valid_res and has_valid_com:
                mixed_use_products[name] = entry
            else:
                print(f"⚠️ Skipping mixed-use entry '{name}' — incomplete residential or commercial data")

    print("\n" + "="*60)
    print("🔍 RUNNING FEASIBILITY ANALYSIS")
    print("="*60)

    if residential_products:
        df_res, res_cashflows = residential_model(
            residential_products,
            shared_acq_cost=1500000,  # total land cost
            dev_cost_per_sqft=200,
            zip_code="80302"
        )

        total_res_dev_cost = sum(row["Development_Cost"] for row in df_res.to_dict('records'))
        res_portfolio_cashflow = [-1500000 - total_res_dev_cost] + res_cashflows
        portfolio_irr = calculate_irr(res_portfolio_cashflow)
        portfolio_em = calculate_equity_multiple(res_portfolio_cashflow)
        portfolio_be = find_break_even_year(res_portfolio_cashflow)

        print(f"\n🏠 Residential Portfolio IRR: {portfolio_irr:.2%}")
        print(f"🏠 Residential Equity Multiple: {portfolio_em:.2f}x")
        print(f"🏠 Residential Break-Even Year: Year {portfolio_be}")

        format_and_display_results(df_res, "Residential", "residential_development_output.csv")
    else:
        print("\n⚠️ No commercial products entered.")

    if commercial_products:
        print("\n🏢 Processing Commercial Products...")
        df_com, com_cashflows = commercial_model(
            commercial_products,
            years=20
        )
        shared_com_acq_cost = 826829
        total_com_dev_cost = sum(row["Development_Cost"] for row in df_com.to_dict('records'))
        com_portfolio_cashflow = [-shared_com_acq_cost - total_com_dev_cost] + com_cashflows
        portfolio_irr = calculate_irr(com_portfolio_cashflow)
        portfolio_em = calculate_equity_multiple(com_portfolio_cashflow)
        portfolio_be = find_break_even_year(com_portfolio_cashflow)

        print(f"\n🏢 Commercial Portfolio IRR: {portfolio_irr:.2%}")
        print(f"🏢 Commercial Equity Multiple: {portfolio_em:.2f}x")
        print(f"🏢 Commercial Break-Even Year: Year {portfolio_be}")

        format_and_display_results(df_com, "Commercial", "commercial_development_output.csv")
    else:
        print("\n⚠️ No commercial products entered.")

    if mixed_use_products:
        print("\n🏙️ Processing Mixed-Use Products...")
        df_mix = mixed_use_model(
            mixed_use_products,
            dev_cost_per_sqft_res=200,
            dev_cost_per_sqft_com=150,
            zip_code="80302"
        )
        total_acq_cost = sum(row["Acquisition_Cost"] for row in df_mix.to_dict("records"))
        total_dev_cost = sum(row["Development_Cost"] for row in df_mix.to_dict("records"))
        total_noi = sum(row["NOI"] for row in df_mix.to_dict("records"))

        # Cash flow: [-Acq + Dev Cost] + [NOI for 20 years]
        annual_noi = total_noi / 20
        mixed_use_cashflows = [-total_acq_cost - total_dev_cost] + [annual_noi] * 20

        portfolio_irr = calculate_irr(mixed_use_cashflows)
        portfolio_em = calculate_equity_multiple(mixed_use_cashflows)
        portfolio_be = find_break_even_year(mixed_use_cashflows)

        print(f"\n🏙️ Mixed-Use Portfolio IRR: {portfolio_irr:.2%}")
        print(f"🏙️ Mixed-Use Equity Multiple: {portfolio_em:.2f}x")
        print(f"🏙️ Mixed-Use Break-Even Year: Year {portfolio_be}")

        format_and_display_results(
            df_mix,
            "Mixed-Use",
            "mixed_use_development_output.csv",
            portfolio_irr=portfolio_irr,
            portfolio_em=portfolio_em,
            portfolio_be=portfolio_be
        )
    else:
        print("\n⚠️ No mixed-use products entered.")

