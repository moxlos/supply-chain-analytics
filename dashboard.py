#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive Supply Chain Analytics Dashboard.

A Streamlit-based web application for visualizing and analyzing optimized supply chain
networks. The dashboard provides interactive maps, charts, and tables to explore
supply-demand flow, costs, and plant utilization.

Features:
    - Interactive network map showing plants, customers, and product flow
    - Descriptive statistics with charts (Sankey, stacked bar, heatmap)
    - Filterable data tables for detailed analysis
    - Real-time optimization using PuLP solver

Usage:
    Run from command line:
    $ streamlit run dashboard.py

    Then upload a CSV file with supply chain data in the sidebar.

Author: Ntovoris Eleftherios (lefteris)
Created: 2024-08-31
Subject: Supply chain analytics dashboard with streamlit
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from supply_demand_opt import SupplyDemand
from math import sin, cos, sqrt, atan2, radians
from babel.numbers import format_currency


def convert_comma_decimals(df, exclude_first_col=True):
    """Convert comma decimal separators to period (European locale handling).

    Converts numeric values with comma decimal separators (e.g., "6,2") to
    period separators (e.g., "6.2") for proper float conversion.

    Args:
        df (pd.DataFrame): DataFrame with potential comma decimals
        exclude_first_col (bool): If True, skip the first column (usually ID/names)

    Returns:
        pd.DataFrame: DataFrame with comma decimals converted to periods
    """
    df_copy = df.copy()
    start_col = 1 if exclude_first_col else 0

    for col in df_copy.columns[start_col:]:
        # Replace comma with period in all cells of this column
        df_copy[col] = df_copy[col].astype(str).str.replace(',', '.', regex=False)

    return df_copy


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth.

    Uses the Haversine formula to compute the distance between two geographic
    coordinates on Earth's surface.

    Args:
        lat1 (float): Latitude of first point in decimal degrees
        lon1 (float): Longitude of first point in decimal degrees
        lat2 (float): Latitude of second point in decimal degrees
        lon2 (float): Longitude of second point in decimal degrees

    Returns:
        float: Distance in kilometers

    Example:
        >>> distance = calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
        >>> print(f"Distance: {distance:.2f} km")
    """
    R = 6373.0  # Radius of earth in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def format_cur(number):
    """Format a number as Euro currency using German locale.

    Args:
        number (float): Numeric value to format

    Returns:
        str: Formatted currency string (e.g., "1.234,56 €")
    """
    return format_currency(number, 'EUR', locale='de_DE')


def create_location_data(lat, lon, N, M):
    """Generate random plant and customer location coordinates for visualization.

    Creates synthetic geographic coordinates for plants and customers by randomly
    distributing them around a central point. Uses fixed random seed for reproducibility.

    Args:
        lat (float): Center latitude
        lon (float): Center longitude
        N (int): Number of plants
        M (int): Number of customers

    Returns:
        tuple: (plant_loc DataFrame, customer_loc DataFrame) where each DataFrame
               contains location coordinates with columns for ID, longitude, and latitude
    """
    coord_init = [lat, lon]

    np.random.seed(0)
    plant_loc = pd.DataFrame({
        'pl_id': range(N),
        'lon_pl': (-1 + 2 * np.random.random(N)) * 0.1 + coord_init[1],
        'lat_pl': (-1 + 2 * np.random.random(N)) * 0.1 + coord_init[0]
    })
    customer_loc = pd.DataFrame({
        'wr_id': range(M),
        'lon_wr': (-1 + 2 * np.random.random(M)) * 0.1 + coord_init[1],
        'lat_wr': (-1 + 2 * np.random.random(M)) * 0.1 + coord_init[0]
    })

    return plant_loc, customer_loc


# ---------------- Dashboard ----------------------
st.set_page_config(layout="wide")


def main():
    """Main application entry point.

    Handles file upload, data processing, optimization solving, and page routing.
    Uses Streamlit session state for data persistence across page interactions.
    """
    st.title("Supply Chain Analytics")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        # Read the uploaded file to a dataframe
        df = pd.read_csv(uploaded_file, sep='\t')

        # Convert comma decimal separators to periods (e.g., "6,2" -> "6.2")
        df = convert_comma_decimals(df, exclude_first_col=True)

        # Extract data from CSV
        # Use dropna() to exclude any empty cells created by Excel's trailing commas
        demand = np.array(df.iloc[-1, 1:-2].dropna().astype(float))
        supply_capacity = np.array(df.iloc[:-1, -2].dropna().astype(float))
        operational_costs = np.array(df.iloc[:-1, -1].dropna().astype(float))
        coord_init = [39.553464, 21.759884]  # lat, lon (Greece)
        N, M = supply_capacity.shape[0], demand.shape[0]

        # Generate location coordinates for visualization
        plant_loc, customer_loc = create_location_data(coord_init[0], coord_init[1], N, M)

        # Get actual transportation costs from CSV (only valid customer columns, excluding any NaN)
        # Extract up to M columns (number of customers determined from demand)
        transportation_costs = np.array(df.iloc[:-1, 1:M+1].astype(float))

        # Format location IDs as strings
        plant_loc['pl_id'] = plant_loc['pl_id'].apply(lambda x: f"plant_{x}")
        customer_loc['wr_id'] = customer_loc['wr_id'].apply(lambda x: f"customer_{x}")

        # Solve optimization problem
        optimizer = SupplyDemand(transportation_costs, demand, supply_capacity, operational_costs)
        report = optimizer.get_report()

        min_supply, max_supply = report['supply'].min(), report['supply'].max()

        report['pl_id'] = report['pl_id'].apply(lambda x: f"plant_{x}")
        report['wr_id'] = report['wr_id'].apply(lambda x: f"customer_{x}")

        pl_id_list = sorted(df.iloc[:-1, 0])
        pl_id_list = [s.lower() for s in pl_id_list]
        wr_id_list = sorted(report['wr_id'].unique())

        # Store all data in session state for access across pages
        st.session_state.pl_id_list = pl_id_list
        st.session_state.wr_id_list = wr_id_list
        st.session_state.min_supply = min_supply
        st.session_state.max_supply = max_supply
        st.session_state.report = report
        st.session_state.plant_loc = plant_loc
        st.session_state.customer_loc = customer_loc
        st.session_state.coord_init = coord_init
        st.session_state.transportation_costs = transportation_costs
        st.session_state.data_loaded = True

        # Create a sidebar with navigation options
        page = st.sidebar.radio("Select a page", ["Map", "Descriptive", "Tables"])

        # Display content based on the selected page
        if page == "Map":
            map_page()
        elif page == "Descriptive":
            page1()
        elif page == "Tables":
            page2(df)


def create_filters():
    """Create sidebar filters and apply them to the report data.

    Provides interactive filters for:
    - Plant selection (multi-select with ALL option)
    - Customer selection (multi-select with ALL option)
    - Supply volume range (slider)

    Returns:
        tuple: (selected_plants, selected_warehouses, selected_volume,
                pl_id_filt, wr_id_filt, filtered_df) containing filter selections
                and the filtered DataFrame merged with location data
    """
    # Sidebar Filters
    st.sidebar.header('Filters')
    selected_plants = st.sidebar.multiselect(
        'Filter Plant',
        st.session_state.pl_id_list + ['ALL'],
        default='ALL'
    )
    selected_warehouses = st.sidebar.multiselect(
        'Filter Customer',
        st.session_state.wr_id_list + ['ALL'],
        default='ALL'
    )
    selected_volume = st.sidebar.slider(
        'Filter Volume',
        min_value=int(st.session_state.min_supply),
        max_value=int(st.session_state.max_supply),
        value=(int(st.session_state.min_supply), int(st.session_state.max_supply))
    )

    # Filter the data based on selections
    pl_id_filt = (
        st.session_state.pl_id_list
        if ('ALL' in selected_plants or len(selected_plants) == 0)
        else selected_plants
    )
    wr_id_filt = (
        st.session_state.wr_id_list
        if ('ALL' in selected_warehouses or len(selected_warehouses) == 0)
        else selected_warehouses
    )

    filtered_df = st.session_state.report[
        (st.session_state.report['pl_id'].isin(pl_id_filt)) &
        (st.session_state.report['wr_id'].isin(wr_id_filt)) &
        (st.session_state.report['supply'] >= selected_volume[0]) &
        (st.session_state.report['supply'] <= selected_volume[1])
    ].copy()

    filtered_df = filtered_df.merge(
        st.session_state.plant_loc, on='pl_id'
    ).merge(
        st.session_state.customer_loc, on='wr_id'
    )

    return selected_plants, selected_warehouses, selected_volume, pl_id_filt, wr_id_filt, filtered_df


def get_costs(filtered_df):
    """Calculate total transportation, operational costs and supply from filtered data.

    Args:
        filtered_df (pd.DataFrame): Filtered report DataFrame

    Returns:
        tuple: (trp_cost, op_cost, total_supply) with rounded values
    """
    trp_cost = np.round(filtered_df['transport_cost'].sum())
    op_cost = np.round(filtered_df['operate_cost'].sum())
    total_supply = np.round(filtered_df['supply'].sum())
    return trp_cost, op_cost, total_supply


def get_stacked_bar(filtered_df):
    """Create stacked bar chart showing supply distribution by plant to customer.

    Args:
        filtered_df (pd.DataFrame): Filtered report DataFrame

    Returns:
        plotly.graph_objects.Figure: Stacked bar chart
    """
    if filtered_df.shape[0] > 0:
        bar_data = filtered_df.groupby(['wr_id', 'pl_id'])['supply'].sum().unstack(fill_value=0)
    else:
        bar_data = pd.DataFrame()

    fig_stacked_bar = px.bar(
        bar_data,
        x=bar_data.index,
        y=bar_data.columns,
        title='Supply Distribution by Plant to Customer',
        labels={'value': 'Supply Quantity', 'wr_id': 'Customer ID'},
        barmode='stack'
    )

    return fig_stacked_bar


def get_sankey(filtered_df):
    """Create Sankey diagram showing flow from plants to customers.

    Args:
        filtered_df (pd.DataFrame): Filtered report DataFrame

    Returns:
        plotly.graph_objects.Figure: Sankey diagram
    """
    if filtered_df.shape[0] > 0:
        # Get unique plants and customers
        unique_plants = filtered_df['pl_id'].unique().tolist()
        unique_customers = filtered_df['wr_id'].unique().tolist()
        all_nodes = unique_plants + unique_customers

        # Create node indices
        node_dict = {node: idx for idx, node in enumerate(all_nodes)}

        # Prepare source, target, and value for the sankey diagram
        source_indices = [node_dict[plant] for plant in filtered_df['pl_id']]
        target_indices = [node_dict[customer] for customer in filtered_df['wr_id']]
        values = filtered_df['supply'].tolist()

        sankey_data = dict(
            type='sankey',
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color='black', width=0.5),
                label=all_nodes,
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
            )
        )

        fig_sankey = go.Figure(data=[sankey_data])
        fig_sankey.update_layout(
            title_text="Flow of Supply from Plants to Customers",
            font_size=10
        )
    else:
        fig_sankey = go.Figure()

    return fig_sankey


def get_bar_chart(filtered_df, trp_cost, op_cost):
    """Create bar chart comparing transportation and operational costs.

    Args:
        filtered_df (pd.DataFrame): Filtered report DataFrame
        trp_cost (float): Total transportation cost
        op_cost (float): Total operational cost

    Returns:
        plotly.graph_objects.Figure: Bar chart of costs
    """
    # Create a dataframe for transportation and operational costs
    cost_df = pd.DataFrame({
        'Cost Type': ['Transportation', 'Operations'],
        'Cost': [trp_cost, op_cost]
    })

    # Create a bar chart to visualize the costs
    fig_bar_chart = px.bar(
        cost_df,
        x='Cost Type',
        y='Cost',
        title='Total Costs by Type',
        labels={'Cost': 'Cost Value', 'Cost Type': 'Cost Category'},
        text='Cost'
    )

    fig_bar_chart.update_traces(texttemplate='%{text:.2s}', textposition='outside')

    return fig_bar_chart


def get_heatmap(trp_cost_matrix):
    """Create heatmap of transportation costs from plants to customers.

    Args:
        trp_cost_matrix (np.ndarray): Transportation costs matrix

    Returns:
        plotly.graph_objects.Figure: Heatmap visualization
    """
    # Get the list of all plants and customers from session state
    all_plants = st.session_state.pl_id_list
    all_warehouses = st.session_state.wr_id_list

    # Create the heatmap for transportation costs
    fig_heatmap = px.imshow(
        trp_cost_matrix,
        labels=dict(x="Customer", y="Plant", color="Cost per Unit"),
        x=all_warehouses,
        y=all_plants,
        title="Transportation Costs per Unit (Plant to Customer)"
    )

    return fig_heatmap


def get_map(filtered_df):
    """Create interactive map showing supply chain network.

    Displays:
    - Active plants (blue markers)
    - Closed plants (red markers)
    - Customers (black markers)
    - Supply routes (green lines)

    Args:
        filtered_df (pd.DataFrame): Filtered report DataFrame with location data

    Returns:
        plotly.graph_objects.Figure: Interactive map
    """
    mean_lat = np.mean(
        st.session_state.customer_loc['lat_wr'].tolist() +
        st.session_state.plant_loc['lat_pl'].tolist()
    )
    mean_lon = np.mean(
        st.session_state.customer_loc['lon_wr'].tolist() +
        st.session_state.plant_loc['lon_pl'].tolist()
    )

    # Sample data for choropleth base map
    choropleth_data = pd.DataFrame({
        'region': ['Region1', 'Region2', 'Region3'],
        'value': [10, 20, 30],
        'lat': [37.7749, 34.0522, 40.7128],
        'lon': [-122.4194, -118.2437, -74.0060]
    })

    # Create base map
    fig = px.choropleth_mapbox(
        choropleth_data,
        geojson=None,
        locations='region',
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        center={"lat": mean_lat, "lon": mean_lon},
        zoom=10,
        title="Supply Chain Network"
    )

    # Find closed plants (in plant_loc but not in report)
    closed_plants = set(st.session_state.plant_loc['pl_id']) - set(st.session_state.report['pl_id'])
    closed_plants_df = st.session_state.plant_loc[st.session_state.plant_loc['pl_id'].isin(closed_plants)]

    # Add active plants (blue)
    fig.add_scattermapbox(
        lon=filtered_df['lon_pl'],
        lat=filtered_df['lat_pl'],
        mode='markers+text',
        text=filtered_df['pl_id'],
        textposition='top right',
        marker=dict(size=8, symbol='circle', color='blue'),
        textfont=dict(size=12, color='blue')
    )

    # Add closed plants (red)
    fig.add_scattermapbox(
        lon=closed_plants_df['lon_pl'],
        lat=closed_plants_df['lat_pl'],
        mode='markers+text',
        text=closed_plants_df['pl_id'],
        textposition='top right',
        marker=dict(size=8, symbol='circle', color='red'),
        textfont=dict(size=12, color='red')
    )

    # Add customers (black)
    fig.add_scattermapbox(
        lon=filtered_df['lon_wr'],
        lat=filtered_df['lat_wr'],
        mode='markers+text',
        marker=dict(size=8, symbol='circle', color='black'),
        text=filtered_df['wr_id'],
        textposition='top right',
        textfont=dict(size=12, color='black')
    )

    # Add supply routes (green lines)
    for _, record in filtered_df.iterrows():
        fig.add_scattermapbox(
            lon=[record['lon_pl'], record['lon_wr']],
            lat=[record['lat_pl'], record['lat_wr']],
            mode='lines',
            line=dict(width=2, color='green'),
            opacity=0.8,
            showlegend=False,
        )

    # Set the layout of the map
    fig.update_layout(
        title="Supply Chain Network",
        showlegend=False,
        height=800
    )

    return fig


# ------------ Pages -------------------------
def map_page():
    """Display the Map page with network visualization and cost metrics."""
    st.write("Map")
    selected_plants, selected_warehouses, selected_volume, pl_id_filt, wr_id_filt, filtered_df = create_filters()

    # Get costs and map figure
    trp_cost, op_cost, total_supply = get_costs(filtered_df)
    sc_map = get_map(filtered_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Transportation Cost", f"{format_cur(round(trp_cost, 0))}")
    col2.metric("Operations Cost", f"{format_cur(op_cost)}")
    col3.metric("Total Supply", f"{total_supply}")

    # Display the map
    st.plotly_chart(sc_map, use_container_width=True)


def page1():
    """Display the Descriptive Statistics page with charts and visualizations."""
    st.write("Descriptive Statistics")
    selected_plants, selected_warehouses, selected_volume, pl_id_filt, wr_id_filt, filtered_df = create_filters()

    fig_stacked_bar = get_stacked_bar(filtered_df)
    fig_sankey = get_sankey(filtered_df)
    trp_cost, op_cost, total_supply = get_costs(filtered_df)
    fig_costs = get_bar_chart(filtered_df, trp_cost, op_cost)
    fig_heatmap = get_heatmap(st.session_state.transportation_costs)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_stacked_bar, use_container_width=True)
    with col2:
        st.plotly_chart(fig_sankey)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(fig_costs, use_container_width=True)
    with col4:
        st.plotly_chart(fig_heatmap)


def page2(df):
    """Display the Tables page with input data and optimization results side-by-side.

    Args:
        df (pd.DataFrame): Original input data from CSV
    """
    st.write("Data Tables")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Input Data")
        st.dataframe(df)
    with col2:
        st.write("Optimization Results")
        st.dataframe(st.session_state.report)


if __name__ == "__main__":
    main()
