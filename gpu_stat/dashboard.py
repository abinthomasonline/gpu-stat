"""
Streamlit dashboard for GPU-Stat visualization.
"""

import argparse
import glob
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st


def load_gpu_stats(data_dir: str) -> dict:
    """
    Load GPU statistics from CSV files in the data directory.

    Args:
        data_dir: Base directory containing server data

    Returns:
        Dictionary mapping server names to their GPU stats DataFrames
    """
    server_data = {}

    # Get all server directories
    server_dirs = [
        d for d in glob.glob(os.path.join(data_dir, "*")) if os.path.isdir(d)
    ]

    for server_dir in server_dirs:
        server_name = os.path.basename(server_dir)

        # Get all gpu_stats CSV files for this server
        stats_files = glob.glob(os.path.join(server_dir, "gpu_stats_*.csv"))

        if not stats_files:
            continue

        # Read and concatenate all stats files
        dfs = []
        for file in stats_files:
            try:
                df = pd.read_csv(file)
                dfs.append(df)
            except Exception as e:
                st.warning(f"Error reading {file}: {str(e)}")

        if dfs:
            server_data[server_name] = pd.concat(dfs, ignore_index=True)
            server_data[server_name]["timestamp"] = pd.to_datetime(
                server_data[server_name]["timestamp"]
            )

    return server_data


def create_gpu_plots(df: pd.DataFrame, server_name: str, time_range: str):
    """
    Create line plots for GPU metrics.

    Args:
        df: DataFrame containing GPU stats
        server_name: Name of the server
    """
    if time_range == "Last Hour":
        x_left = datetime.now() - timedelta(hours=1)
        x_right = datetime.now()
        df = df[df["timestamp"] >= x_left]
    elif time_range == "Last 6 Hours":
        x_left = datetime.now() - timedelta(hours=6)
        x_right = datetime.now()
        df = df[df["timestamp"] >= x_left]
    elif time_range == "Last 24 Hours":
        x_left = datetime.now() - timedelta(hours=24)
        x_right = datetime.now()
        df = df[df["timestamp"] >= x_left]
    else:
        x_left = df["timestamp"].min()
        x_right = df["timestamp"].max()

    # Create tabs for different metrics
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Utilization", "Memory", "Temperature", "Power", "Raw Data"]
    )

    with tab1:
        st.subheader("GPU Utilization")
        fig = px.line(
            df,
            x="timestamp",
            y=["utilization_gpu", "utilization_memory"],
            title=f"GPU Utilization - {server_name}",
            labels={"value": "Utilization (%)", "timestamp": "Time"},
            range_x=[x_left, x_right],
        )
        fig.update_traces(mode="lines+markers")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Memory Usage")
        fig = px.line(
            df,
            x="timestamp",
            y=["memory_used", "memory_free"],
            title=f"Memory Usage - {server_name}",
            labels={"value": "Memory (MB)", "timestamp": "Time"},
            range_x=[x_left, x_right],
        )
        fig.update_traces(mode="lines+markers")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Temperature")
        fig = px.line(
            df,
            x="timestamp",
            y="temperature",
            title=f"GPU Temperature - {server_name}",
            labels={"value": "Temperature (°C)", "timestamp": "Time"},
            range_x=[x_left, x_right],
        )
        fig.update_traces(mode="lines+markers")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Power Usage")
        fig = px.line(
            df,
            x="timestamp",
            y=["power_draw", "power_limit"],
            title=f"Power Usage - {server_name}",
            labels={"value": "Power (W)", "timestamp": "Time"},
            range_x=[x_left, x_right],
        )
        fig.update_traces(mode="lines+markers")
        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.subheader("Raw Data")
        st.dataframe(
            df.sort_values(by="timestamp", ascending=False), use_container_width=True
        )


def run_dashboard(data_dir: str = "./data"):
    st.set_page_config(page_title="GPU-Stat Dashboard", layout="wide")
    st.title("GPU-Stat Dashboard")

    st.button("Refresh Data")

    # Load data
    server_data = load_gpu_stats(data_dir)

    if not server_data:
        st.error(
            "No GPU statistics data found. Please ensure the data directory contains server data."
        )
        return

    # Server selection
    col1, col2 = st.columns(2)
    with col1:
        selected_server = st.selectbox("Select Server", list(server_data.keys()))
    with col2:
        time_range = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours", "All Time"],
            index=2,
        )

    if selected_server:
        df = server_data[selected_server]

        # Display current stats
        latest_stats = df.iloc[-1]

        col3, col4 = st.columns(2)
        with col3:
            st.metric(
                "Current GPU Utilization", f"{latest_stats['utilization_gpu']:.1f}%"
            )
        with col4:
            st.metric(
                "Current Memory Usage",
                f"{latest_stats['memory_used']:.0f}MB / {latest_stats['memory_total']:.0f}MB",
            )
        col5, col6 = st.columns(2)
        with col5:
            st.metric("Current Temperature", f"{latest_stats['temperature']:.1f}°C")
        with col6:
            st.metric("Current Power Draw", f"{latest_stats['power_draw']:.1f}W")

        # Create plots
        create_gpu_plots(df, selected_server, time_range)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GPU-Stat Dashboard")
    parser.add_argument(
        "--data-dir", type=str, default="./data", help="Path to the data directory"
    )
    args = parser.parse_args()
    run_dashboard(args.data_dir)
