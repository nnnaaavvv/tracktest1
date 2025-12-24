import numpy as np
import pandas as pd
import streamlit as st

import app_functions as appf
import calculation_functions as cf

###############################################################################
# Initial Page Config
st.set_page_config(
    page_title="Race Time Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

###############################################################################
# Sidebar

st.sidebar.header("Race Time Calculator")

# File upload
help_input_csv = "Please upload a CSV File with the required parameters"
uploaded_file = st.sidebar.file_uploader(
    label="Upload Race Time Data",
    help=help_input_csv,
    type=["csv"],
)

# Inputs
car_mass = st.sidebar.number_input(
    label="Car Mass (grams)",
    min_value=0.0,
    help="The Car Mass should be the weight of the car in grams",
)

friction_u = st.sidebar.number_input(
    label="Friction Coefficient",
    min_value=0.0,
    help="The friction coefficient should be kinetic",
)

generate = st.sidebar.button("Generate")

###############################################################################
# Main body – Introduction

introduction = st.empty()
with introduction.container():
    st.title("Roosevelt Racer's Race Time Calculator")

    st.header("Quick Start")
    st.write(
        """
        To use this calculator you must upload a CSV file containing:
        **Time (s), Force (N), CO2 Mass (Mco2), Drag (FD)**.
        """
    )

    st.download_button(
        label="Download Example CSV",
        data=appf.example_csv(),
        file_name="RTC_example_data.csv",
        mime="text/csv",
    )

    st.header("Purpose")
    st.write(
        """
        This calculator helps evaluate whether a dragster model is worth manufacturing
        by predicting its race time using empirical thrust, friction, mass, and drag data.
        """
    )

    st.graphviz_chart(
        """
        digraph {
            FrictionData -> RaceTimeCalculator
            ThrustData -> RaceTimeCalculator
            MassData -> RaceTimeCalculator
            DragData -> RaceTimeCalculator
            RaceTimeCalculator -> RaceTimePrediction
        }
        """
    )

###############################################################################
# Calculations (ONLY after clicking Generate)

if generate:
    # ---- Input validation ----
    if uploaded_file is None:
        st.sidebar.error("Please upload a CSV file")
        st.stop()

    if car_mass <= 0:
        st.sidebar.error("Please enter a valid car mass")
        st.stop()

    if friction_u <= 0:
        st.sidebar.error("Please enter a valid friction coefficient")
        st.stop()

    # ---- Safe to proceed ----
    introduction.empty()
    st.title("Calculations")

    dataframe = pd.read_csv(uploaded_file)

    # Convert to DVA
    dva_dataframe = cf.dataframe_to_dva(dataframe, car_mass, friction_u)

    # Acceleration
    dva_dataframe["Acceleration (a)"] = (
        dva_dataframe["Fnet"] / dva_dataframe["Total Mass"]
    ) * 1000

    # Motion calculations
    dva_dataframe = cf.find_continuous_time(dva_dataframe)
    dva_dataframe = cf.cal_speed_change(dva_dataframe)
    dva_dataframe = cf.cal_speed(dva_dataframe)
    dva_dataframe = cf.cal_distance_change(dva_dataframe)
    dva_dataframe = cf.cal_distance(dva_dataframe)

    # Keep required columns
    dva_dataframe = dva_dataframe[
        ["Continuous Time", "Acceleration (a)", "Speed (v)", "Distance (d)"]
    ]

    dva_dataframe = dva_dataframe[dva_dataframe["Distance (d)"] <= 20]

    # Metrics
    top_speed = dva_dataframe["Speed (v)"].max() * (18 / 5)
    end_time = dva_dataframe["Continuous Time"].iloc[-1]

    col1, col2 = st.columns(2)
    col1.metric("Top Speed (km/hr)", round(top_speed, 4))
    col2.metric("End Time (sec)", round(end_time, 4))

    # Acceleration plot
    st.header("Acceleration Over Time")
    acc_df = dva_dataframe[["Continuous Time", "Acceleration (a)"]]
    st.line_chart(acc_df.rename(columns={"Continuous Time": "index"}).set_index("index"))

    # Velocity plot
    st.header("Velocity Over Time")
    vel_df = dva_dataframe[["Continuous Time", "Speed (v)"]]
    st.line_chart(vel_df.rename(columns={"Continuous Time": "index"}).set_index("index"))

    # Distance plot
    st.header("Distance Over Time")
    dist_df = dva_dataframe[["Continuous Time", "Distance (d)"]]
    st.line_chart(dist_df.rename(columns={"Continuous Time": "index"}).set_index("index"))

    # Show table
    st.subheader("DVA Data")
    st.dataframe(dva_dataframe)

    # Download
    st.download_button(
        label="Download DVA data as CSV",
        data=dva_dataframe.to_csv(index=False).encode("utf-8"),
        file_name="dva_data.csv",
        mime="text/csv",
    )
