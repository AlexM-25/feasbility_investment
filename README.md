Investment Feasibility Model

This Python-based project models the financial feasibility of residential, commercial, and mixed-use real estate developments. It supports dynamic user inputs and simulates project cash flows, absorption schedules, rental income, development and operating costs, and key investment metrics including:

•	Net Operating Income (NOI)

•	Internal Rate of Return (IRR)

•	Equity Multiple

•	Debt Service Coverage Ratio (DSCR)

•	Capitalization Rate

•	Break-Even Year


The model incorporates real-world absorption dynamics, market churn, reabsorption, and early occupancy behaviors, making it a powerful tool for scenario testing and investment decision-making. It also includes portfolio-level rollups and automated summary exports (CSV).

Features

•	Modular input collection for Residential, Commercial, and Mixed-Use products

•	Unit- and square-foot-based absorption forecasting with churn, reabsorption, and early occupancy

•	Full cash flow analysis and financial metric outputs per product and at the portfolio level

•	Built-in sensitivity analysis for key drivers like rent and development cost

•	Portfolio-level visualizations (heatmaps and IRR curves)

•	Exportable results for all development types (CSV summaries)

Structure

•	growth_helpers.py: Handles absorption schedules, net occupancy, and revenue modeling

•	finance.py: Calculates IRR, equity multiple, DSCR, and development costs

•	inputs.py: Interactive CLI prompts for collecting structured product inputs

•	main.py: Runs full simulation and outputs results

•	sensitivity_analysis.py: Generates charts to analyze risk and return under changing assumptions

Technologies

•	Python (Pandas, NumPy, Matplotlib)

•	NumPy financial for IRR and financial metrics

•	Structured modular design for easy expansion and customization
