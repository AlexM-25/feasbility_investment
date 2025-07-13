def get_user_inputs():
    product_categories = {
        "Residential": ["Detached", "Attached", "Multi-Family"],
        "Commercial": ["Industrial", "Office", "Retail", "Data Centers", "Hotel"]
    }

    project_data = []

    for category in ["Residential", "Commercial", "Mixed-Use"]:
        print(f"\n--- {category} Development ---")
        acq_cost = _get_positive_float(f"Enter total land (acquisition) cost for {category} development: ")

        if category in ["Residential", "Commercial"]:
            for product in product_categories[category]:
                print(f"\nEntering data for: {product}")
                entry = {
                    "category": category,
                    "product": product,
                    "acq cost": acq_cost,
                    "units" if category == "Residential" else "sqft":
                        _get_positive_int(f"Enter total number of {'units' if category == 'Residential' else 'square feet'}: "),
                    "rental_price":
                        _get_positive_float(f"Enter rental price per {'unit' if category == 'Residential' else 'SF'}: "),
                    "dev_cost":
                        _get_positive_float(f"Enter development cost per {'unit' if category == 'Residential' else 'SF'}: "),
                    "opex_per_unit" if category == "Residential" else "opex_per_sqft":
                        _get_positive_float(
                            f"Enter annual operating expense per {'unit' if category == 'Residential' else 'SF'}: "),
                    "product_type": product.lower(),
                    "absorption_rate":
                        _get_positive_float("Enter annual absorption rate (e.g., 0.15): ")
                }

                project_data.append(entry)

                another = input("Do you want to enter another product in this category? (yes/no): ").strip().lower()
                if another not in ["yes", "y"]:
                    break

        elif category == "Mixed-Use":
            mixed_use_entry = {
                "category": category,
                "product": "Mixed-Use Project",
                "acq cost": acq_cost,
                "residential": {},
                "commercial": {}
            }

            print("\nEntering RESIDENTIAL components for Mixed-Use:")
            for res_type in product_categories["Residential"]:
                add = input(f"Do you want to add residential product '{res_type}'? (yes/no): ").strip().lower()
                if add not in ["yes", "y"]:
                    continue

                mixed_use_entry["residential"][res_type] = {
                    "units": _get_positive_int(f"Enter total number of {res_type} units: "),
                    "rental_price": _get_positive_float(f"Enter rental price per unit for {res_type}: "),
                    "dev_cost": _get_positive_float(f"Enter development cost per unit for {res_type}: "),
                    "opex_per_unit": _get_positive_float(f"Enter annual operating expense per unit for {res_type}: "),
                    "absorption_rate": _get_positive_float("Enter annual absorption rate (e.g., 0.15): "),
                    "product_type": res_type.lower()
                }

            print("\nEntering COMMERCIAL components for Mixed-Use:")
            for com_type in product_categories["Commercial"]:
                add = input(f"Do you want to add commercial product '{com_type}'? (yes/no): ").strip().lower()
                if add not in ["yes", "y"]:
                    continue

                mixed_use_entry["commercial"][com_type] = {
                    "sqft": _get_positive_int(f"Enter total square feet for {com_type}: "),
                    "rental_price": _get_positive_float(f"Enter rental price per SF for {com_type}: "),
                    "dev_cost": _get_positive_float(f"Enter development cost per SF for {com_type}: "),
                    "opex_per_sqft": _get_positive_float(f"Enter annual operating expense per SF for {com_type}: "),
                    "absorption_rate": _get_positive_float("Enter annual absorption rate (e.g., 0.15): "),
                    "product_type": com_type.lower()
                }

            project_data.append(mixed_use_entry)

    return project_data

def _get_positive_float(prompt):
    while True:
        try:
            val = float(input(prompt))
            if val <= 0:
                print("Please enter a positive number.")
                continue
            return val
        except ValueError:
            print("Invalid input. Enter a numeric value.")

def _get_positive_int(prompt):
    while True:
        try:
            val = int(input(prompt))
            if val <= 0:
                print("Please enter a positive integer.")
                continue
            return val
        except ValueError:
            print("Invalid input. Enter an integer.")

