# Supply Chain Analytics Dashboard

An interactive web application for supply chain network optimization using linear programming. This tool helps businesses minimize total costs (transportation + operational) while meeting supply and demand constraints across their distribution network.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-%20%20GNU%20GPLv3%20-green?style=plastic)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)

## Features

- **Optimization Engine**: Mixed-Integer Linear Programming (MILP) solver using PuLP
- **Interactive Dashboard**: Real-time visualization with Streamlit
- **Network Visualization**: Interactive maps showing plants, customers, and product flow
- **Cost Analysis**: Comprehensive breakdown of transportation and operational costs
- **What-If Scenarios**: Upload custom data to explore different network configurations
- **Dynamic Filtering**: Filter by plants, customers, and supply volumes
- **Multiple Views**: Map visualization, descriptive statistics, and data tables

## Screenshots

<img width="1847" height="890" alt="Screenshot from 2026-01" src="https://github.com/user-attachments/assets/2ee7e834-9944-40ae-824a-2af129c4c96a" />
<img width="1847" height="890" alt="02" src="https://github.com/user-attachments/assets/dcfbdca0-dd43-4ac9-8ddd-071f3d0a4058" />



### Network Map

Interactive map showing optimized supply chain network with plants (blue), customers (black), and closed facilities (red).

### Descriptive Statistics

- **Sankey Diagram**: Visualize product flow from plants to customers
- **Stacked Bar Chart**: Supply distribution breakdown
- **Cost Analysis**: Transportation vs operational costs
- **Heatmap**: Transportation cost matrix

### Data Tables

Side-by-side comparison of input data and optimization results.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:

```bash
git clone https://github.com/moxlos/supply_chain_analytics.git
cd supply-chain-analytics
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install GLPK solver (optional, for better performance):

```bash
# Ubuntu/Debian
sudo apt-get install glpk-utils

# macOS
brew install glpk

# Windows
# Download from: https://sourceforge.net/projects/winglpk/
```

## Usage

### Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

### Input Data Format

Upload a CSV file with the following structure (tab-separated, comma as decimal):

```
From_To     Customer_0  Customer_1  Customer_2  ...  Supply  Cost
Plant_0     8,11        7,38        8,52        ...  544     5010
Plant_1     10,29       1,45        5,04        ...  621     5220
...
Demand      553         592         472    
```

**Column Description:**

- `From_To`: Plant identifier
- `Customer_0, Customer_1, ...`: Transportation costs from plant to each customer
- `Supply`: Maximum supply capacity at the plant
- `Cost`: Fixed operational cost for running the plant
- `Demand` row: Required demand at each customer location

**Note:** The CSV uses whitespace as column separator and comma as decimal separator (European format).

### Running Optimization Standalone

You can also use the optimization engine programmatically:

```python
import numpy as np
from supply_demand_opt import SupplyDemand

# Define problem parameters
transportation_costs = np.array([[10, 20], [15, 25]])  # 2 plants, 2 customers
demand = np.array([100, 150])  # Demand at each customer
supply_capacity = np.array([120, 130])  # Capacity at each plant
operational_costs = np.array([5000, 6000])  # Fixed cost per plant

# Solve optimization
optimizer = SupplyDemand(transportation_costs, demand, supply_capacity, operational_costs)
report = optimizer.get_report()

print(report)
```

## Problem Formulation

### Decision Variables

- **x[i,j]**: Continuous variable representing quantity of product shipped from plant i to customer j
- **y[i]**: Binary variable (1 if plant i is operational, 0 otherwise)

### Objective Function

Minimize:

```
Σ(transportation_cost[i,j] * x[i,j]) + Σ(operational_cost[i] * y[i])
```

### Constraints

1. **Supply Constraint**: `Σ(x[i,j]) ≤ supply_capacity[i] * y[i]` for all plants i
   - Total outflow from each plant cannot exceed its capacity
   - Plant must be operational (y[i]=1) to ship products
2. **Demand Constraint**: `Σ(x[i,j]) = demand[j]` for all customers j
   - Customer demand must be satisfied exactly
3. **Non-negativity**: `x[i,j] ≥ 0`
4. **Binary**: `y[i] ∈ {0, 1}`

## Project Structure

```
supply-chain-analytics/
│
├── dashboard.py                 # Streamlit dashboard application
├── supply_demand_opt.py         # Optimization engine (PuLP)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── LICENSE                      # GNU General Public License v3.0
├── CLAUDE.md                    # Development guidance
│
└── data/
    ├── demand.csv               # Sample input data
    └── opt_log/                 # Optimization logs (auto-generated)
        ├── pulp_problem.lp      # LP formulation
        └── optimization_results.txt  # Solver output
```

## Example Scenarios

### 1. Base Case Analysis

Upload the provided `data/demand.csv` to see the optimal network configuration.

### 2. What-If: Increase Operational Costs

Modify the `Cost` column for specific plants to see how the network adapts (e.g., expensive plants may close).

### 3. What-If: Demand Surge

Increase demand values to test if current plant capacity is sufficient or if new plants need to open.

### 4. What-If: New Transportation Routes

Adjust transportation costs to explore alternative distribution strategies.

### 5. What-If: Plant Closure

Set operational cost very high for specific plants to simulate closure and observe rerouting.

## Technical Details

### Technologies Used

- **Python 3.8+**: Core programming language
- **PuLP**: Linear programming solver interface
- **GLPK**: Default open-source solver (GNU Linear Programming Kit)
- **Streamlit**: Web application framework
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **Babel**: Internationalization and currency formatting

### Solver Information

The application uses **GLPK** (GNU Linear Programming Kit) as the default solver. This is an open-source solver suitable for small to medium-sized problems. Alternative commercial solvers (CPLEX, Gurobi) can be configured in `supply_demand_opt.py` for larger-scale problems.

## Limitations & Assumptions

**Note:** This is a proof-of-concept/portfolio project with the following limitations:

- **Synthetic Data**: The sample dataset is artificially generated for demonstration purposes
- **Random Locations**: Plant and customer coordinates are randomly distributed and do not reflect real-world geography
- **Single Product**: The model assumes a single homogeneous product
- **Single Period**: Represents a single time period (no multi-period planning)
- **Fixed Costs**: Operational costs are fixed and do not vary with production volume
- **Perfect Information**: Assumes demand and costs are known with certainty

## Future Enhancements

Potential improvements for production use:

- [ ] Multi-product support with product-specific constraints
- [ ] Time-series optimization (multi-period planning with inventory)
- [ ] Real geospatial data integration with actual addresses
- [ ] Capacity expansion scenarios and investment analysis
- [ ] Inventory holding costs and storage constraints
- [ ] Risk and uncertainty modeling (stochastic programming)
- [ ] Route optimization with real transportation networks
- [ ] Environmental impact metrics (carbon footprint)
- [ ] Export results to Excel/PDF reports
- [ ] User authentication and saved scenarios
- [ ] API endpoint for integration with other systems

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 License - see the [LICENSE](LICENSE) file for details.

## Author

**Ntovoris Eleftherios**

- GitHub: [@moxlos](https://github.com/moxlos)
- LinkedIn:  [Eleftherios Ntovoris](https://www.linkedin.com/in/eleftherios-ntovoris-731439169/)

---

**Portfolio Note**: This project demonstrates skills in:

- Operations Research & Optimization (Linear Programming, MILP)
- Python Programming (OOP, data structures, algorithms)
- Data Visualization (Plotly, interactive dashboards)
- Web Development (Streamlit framework)
- Software Engineering (clean code, documentation, testing)
- Mathematical Modeling (constraint formulation, objective functions)

*This is an educational/portfolio project. The data and scenarios are for demonstration purposes only.*
