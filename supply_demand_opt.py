#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Supply Chain Network Optimization using Linear Programming.

This module implements a mixed-integer linear programming (MILP) model to optimize
supply chain networks by minimizing total costs (transportation + operational) while
satisfying supply and demand constraints.

The optimization determines:
- Which plants to operate (binary decision)
- How to allocate product flow from plants to customers (continuous flow)

Classes:
    SupplyDemand: Main optimization class for supply-demand network problems

Example:
    >>> import numpy as np
    >>> transportation_costs = np.array([[10, 20], [15, 25]])
    >>> demand = np.array([100, 150])
    >>> supply_capacity = np.array([120, 130])
    >>> operational_costs = np.array([5000, 6000])
    >>> optimizer = SupplyDemand(transportation_costs, demand, supply_capacity, operational_costs)
    >>> report = optimizer.get_report()
    >>> print(report)

Author: Ntovoris Eleftherios (lefteris)
Subject: Supply-demand optimization class
"""

import os
import pandas as pd
import numpy as np
import pulp


class SupplyDemand:
    """Mixed-Integer Linear Programming model for supply chain network optimization.

    This class formulates and solves a facility location and distribution problem,
    determining which plants to operate and how to allocate product flow from plants
    to customers to minimize total costs.

    The model uses:
    - Binary variables (y) to decide which plants to operate
    - Continuous variables (x) to determine product flow amounts

    Attributes:
        transportation_costs (np.ndarray): NxM cost matrix for shipping from plants to customers
        demand (np.ndarray): Demand quantity required at each customer location (length M)
        supply_capacity (np.ndarray): Maximum supply capacity at each plant (length N)
        operational_costs (np.ndarray): Fixed operational cost for running each plant (length N)
        nVar (int): Number of plants (decision variables for plant operation)
        mVar (int): Number of customers (demand nodes)

    Example:
        >>> optimizer = SupplyDemand(transportation_costs, demand, supply_capacity, operational_costs)
        >>> report = optimizer.get_report()
        >>> print(f"Total cost: {report['transport_cost'].sum() + report['operate_cost'].sum()}")
    """

    def __init__(self, transportation_costs, demand, supply_capacity, operational_costs):
        """Initialize the supply-demand optimization model.

        Args:
            transportation_costs (np.ndarray): NxM matrix of transportation costs
                where N=number of plants, M=number of customers
            demand (np.ndarray): Array of length M with demand at each customer
            supply_capacity (np.ndarray): Array of length N with capacity at each plant
            operational_costs (np.ndarray): Array of length N with operational cost per plant

        Raises:
            ValueError: If array dimensions are inconsistent or contain invalid values
        """
        # Input validation - check types
        if not isinstance(transportation_costs, np.ndarray) or transportation_costs.ndim != 2:
            raise ValueError("transportation_costs must be a 2D numpy array")

        if not isinstance(demand, np.ndarray) or demand.ndim != 1:
            raise ValueError("demand must be a 1D numpy array")

        if not isinstance(supply_capacity, np.ndarray) or supply_capacity.ndim != 1:
            raise ValueError("supply_capacity must be a 1D numpy array")

        if not isinstance(operational_costs, np.ndarray) or operational_costs.ndim != 1:
            raise ValueError("operational_costs must be a 1D numpy array")

        # Validate array dimensions are compatible
        if transportation_costs.shape[0] != supply_capacity.shape[0]:
            raise ValueError(
                f"transportation_costs rows ({transportation_costs.shape[0]}) "
                f"must match supply_capacity length ({supply_capacity.shape[0]})"
            )

        if transportation_costs.shape[1] != demand.shape[0]:
            raise ValueError(
                f"transportation_costs columns ({transportation_costs.shape[1]}) "
                f"must match demand length ({demand.shape[0]})"
            )

        if transportation_costs.shape[0] != operational_costs.shape[0]:
            raise ValueError(
                f"transportation_costs rows ({transportation_costs.shape[0]}) "
                f"must match operational_costs length ({operational_costs.shape[0]})"
            )

        # Validate no negative values
        if np.any(transportation_costs < 0):
            raise ValueError("transportation_costs cannot contain negative values")

        if np.any(demand < 0):
            raise ValueError("demand cannot contain negative values")

        if np.any(supply_capacity < 0):
            raise ValueError("supply_capacity cannot contain negative values")

        if np.any(operational_costs < 0):
            raise ValueError("operational_costs cannot contain negative values")

        # Store parameters with descriptive names
        self.transportation_costs = transportation_costs
        self.demand = demand
        self.supply_capacity = supply_capacity
        self.operational_costs = operational_costs
        self.nVar = operational_costs.shape[0]  # Number of plants
        self.mVar = demand.shape[0]  # Number of customers

    def get_variables(self):
        """Create decision variables for the optimization problem.

        Creates:
        - x[i,j]: Continuous variable for product flow from plant i to customer j
        - y[i]: Binary variable indicating if plant i is operational

        Returns:
            tuple: (x, y) where x is a dict of continuous variables and y is a dict of binary variables
        """
        xshape = (range(self.nVar), range(self.mVar))
        x = pulp.LpVariable.dicts("X", xshape, lowBound=0)
        y = pulp.LpVariable.dicts("Y", range(self.nVar), cat='Binary')
        return x, y

    def write_logs(self, prob, x, y):
        """Write optimization results and problem formulation to log files.

        Creates two files in data/opt_log/:
        - pulp_problem.lp: Linear programming formulation
        - optimization_results.txt: Solution summary with status and optimal values

        Args:
            prob: PuLP problem object with solved optimization
            x: Decision variables for product flow
            y: Binary variables for plant operation status

        Raises:
            IOError: If log directory cannot be created or files cannot be written
        """
        log_dir = "data/opt_log"

        # Create log directory if it doesn't exist
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            raise IOError(f"Failed to create log directory '{log_dir}': {e}")

        # Write LP problem formulation
        lp_file = os.path.join(log_dir, "pulp_problem.lp")
        try:
            prob.writeLP(lp_file)
        except Exception as e:
            raise IOError(f"Failed to write LP file to '{lp_file}': {e}")

        # Write optimization results
        results_file = os.path.join(log_dir, "optimization_results.txt")
        try:
            with open(results_file, "w") as file:
                file.write(f"Status: {pulp.LpStatus[prob.status]}\n")

                sols = [(w, w.varValue) for w in prob.variables()]
                file.write(f"Optimal value of all: {sols}\n")

                file.write(f"Number of Variables: {self.nVar * self.mVar + self.nVar}\n")
                file.write(f"Number of Constraints: {self.nVar + self.mVar}\n")
                file.write(f"Optimal objective value: {pulp.value(prob.objective)}\n")
        except IOError as e:
            raise IOError(f"Failed to write results to '{results_file}': {e}")

    def get_solution(self):
        """Formulate and solve the optimization problem.

        Formulates a mixed-integer linear program (MILP) with:
        - Objective: Minimize total transportation costs + operational costs
        - Supply constraints: Flow from each plant <= capacity * plant_status
        - Demand constraints: Flow to each customer = demand (must be satisfied exactly)

        Returns:
            pulp.LpProblem: Solved optimization problem object
        """
        x, y = self.get_variables()

        prob = pulp.LpProblem("distribution_opt", pulp.LpMinimize)

        # Objective function: Minimize total transportation + operational costs
        objective_function = pulp.lpSum([
            self.transportation_costs[n_idx, m_idx] * x[n_idx][m_idx]
            for n_idx in range(self.nVar)
            for m_idx in range(self.mVar)
        ]) + pulp.lpSum([
            self.operational_costs[n_idx] * y[n_idx]
            for n_idx in range(self.nVar)
        ])

        prob += objective_function, "Objective_Function"

        # Supply constraints: Total outflow from each plant <= capacity * plant_status
        for n_idx in range(self.nVar):
            prob += (
                sum(x[n_idx][m_idx] for m_idx in range(self.mVar))
                <= self.supply_capacity[n_idx] * y[n_idx],
                f"Supply_ctr_{n_idx}"
            )

        # Demand constraints: Total inflow to each customer = demand (exact match)
        for m_idx in range(self.mVar):
            prob += (
                sum(x[n_idx][m_idx] for n_idx in range(self.nVar))
                == self.demand[m_idx],
                f"Demand_ctr_{m_idx}"
            )

        # Solve using GLPK solver
        prob.solve(pulp.GLPK_CMD())

        self.write_logs(prob, x, y)

        return prob

    def get_network(self):
        """Solve optimization and extract network flow solution.

        Returns:
            tuple: (prob, Xfilt, Y, cost_matrix) where:
                - prob: Solved optimization problem
                - Xfilt: DataFrame of non-zero flows with columns (pl_id, wr_id, value)
                - Y: DataFrame of plant status with columns (pl_id, value)
                - cost_matrix: NxM matrix of actual transportation costs incurred
        """
        prob = self.get_solution()
        x_mat = np.zeros((self.nVar, self.mVar))
        y_mat = np.zeros(self.nVar)
        X = {'pl_id': [], 'wr_id': [], 'value': []}
        Y = {'pl_id': [], 'value': []}

        for v in prob.variables():
            ids = v.name[2:].split("_")
            if v.name[0] == 'X':
                X['pl_id'].append(int(ids[0]))
                X['wr_id'].append(int(ids[1]))
                X['value'].append(v.varValue)
                x_mat[int(ids[0]), int(ids[1])] = v.varValue
            else:
                Y['pl_id'].append(int(ids[0]))
                Y['value'].append(v.varValue)
                y_mat[int(ids[0])] = v.varValue

        print("Objective calculation:",
              np.sum(self.transportation_costs * x_mat) + np.dot(self.operational_costs, y_mat))

        X = pd.DataFrame(X)
        Y = pd.DataFrame(Y)
        Xfilt = X.loc[X['value'] > 0].reset_index(drop=True)

        return prob, Xfilt, Y, self.transportation_costs * x_mat

    def get_report(self):
        """Generate comprehensive report of optimization results.

        Combines optimization solution with input data to create a detailed report
        showing supply flows, costs, capacities, and demands.

        Returns:
            pd.DataFrame: Report with columns:
                - pl_id: Plant identifier
                - wr_id: Customer identifier
                - supply: Quantity of product shipped
                - transport_cost: Cost of this shipment
                - limit_supply: Plant capacity
                - demand: Customer demand
                - operate_cost: Plant operational cost
        """
        prob, X, Y, cost_matrix = self.get_network()

        X = X.rename(columns={'value': 'supply'})

        # Create transportation cost dataframe
        C_df = pd.DataFrame(cost_matrix)
        C_df['pl_id'] = range(self.transportation_costs.shape[0])
        C_df = pd.melt(C_df, id_vars=['pl_id'])
        C_df = C_df.rename(columns={'variable': 'wr_id', 'value': 'transport_cost'})
        C_df['wr_id'] = C_df['wr_id'].astype('int')

        # Create demand dataframe
        D_df = pd.DataFrame({
            'wr_id': range(self.demand.shape[0]),
            'demand': self.demand
        })

        # Create supply capacity dataframe
        S_df = pd.DataFrame({
            'pl_id': range(self.supply_capacity.shape[0]),
            'limit_supply': self.supply_capacity
        })

        # Create operational cost dataframe
        c_df = pd.DataFrame({
            'pl_id': range(self.operational_costs.shape[0]),
            'operate_cost': self.operational_costs
        })

        # Merge all dataframes to create comprehensive report
        report = X.merge(C_df, left_on=['pl_id', 'wr_id'], right_on=['pl_id', 'wr_id'])
        report = report.merge(S_df, left_on='pl_id', right_on='pl_id')
        report = report.merge(D_df, left_on='wr_id', right_on='wr_id')
        report = report.merge(c_df, left_on='pl_id', right_on='pl_id')

        return report


if __name__ == "__main__":
    # Read CSV with European format (comma as decimal separator)
    df = pd.read_csv("data/demand.csv", sep='\t')

    # Convert to numpy arrays with float type
    transportation_costs = np.array(df.iloc[:-1, 1:-2].astype(float))
    demand = np.array(df.iloc[-1, 1:-2].astype(float))
    supply_capacity = np.array(df.iloc[:-1, -2].astype(float))
    operational_costs = np.array(df.iloc[:-1, -1].astype(float))

    optimizer = SupplyDemand(transportation_costs, demand, supply_capacity, operational_costs)
    prob, X, Y, C_cost = optimizer.get_network()

    print(prob)
    print(X)
    print(f"Total transportation cost: {C_cost.sum():.2f}")
