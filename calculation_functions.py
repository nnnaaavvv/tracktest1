import numpy as np
import pandas as pd
import streamlit as st

###############################################################################
# Streamlit cache (modern + safe)
###############################################################################

def cache(func):
    return st.cache_data(func, show_spinner=False)

###############################################################################
# Physics helpers
###############################################################################

@cache
def friction_f(total_mass, friction_u):
    # total_mass in grams → kg
    return (total_mass / 1000) * 9.81 * friction_u


@cache
def force_net(force, friction_force, drag_force):
    return force - friction_force - drag_force

###############################################################################
# Dataframe → DVA
###############################################################################

@st.cache_data(show_spinner=False)
def dataframe_to_dva(dataframe, car_mass, friction_u):
    df = dataframe.copy()

    # Total mass
    df["Total Mass"] = df["CO2 Mass (Mco2)"] + car_mass

    # Friction
    df["Friction Force (Ff)"] = friction_f(df["Total Mass"], friction_u)

    # Net force
    df["Fnet"] = force_net(df["Force (N)"], df["Friction Force (Ff)"], df["Drag (FD)"])

    dva = df[["Time (s)", "Total Mass", "Fnet"]].copy()
    dva[dva < 0] = 0

    # Start when force becomes positive
    first_idx = dva[dva["Fnet"] > 0].index.min()
    if pd.notna(first_idx):
        dva = dva.loc[first_idx:].reset_index(drop=True)

    return dva

###############################################################################
# Continuous time
###############################################################################

@st.cache_data(show_spinner=False)
def find_continuous_time(dva_dataframe):
    df = dva_dataframe.copy()

    # delta t
    df["Δt"] = df["Time (s)"].diff().fillna(0)

    # continuous time
    df["Continuous Time"] = df["Δt"].cumsum()

    return df

###############################################################################
# Speed change (delta v)
###############################################################################

@st.cache_data(show_spinner=False)
def cal_speed_change(dva_dataframe):
    df = dva_dataframe.copy()

    df["Speed Change (delta v)"] = (
        df["Acceleration (a)"].shift(1).fillna(0)
        + df["Acceleration (a)"]
    ) / 2 * df["Δt"]

    return df

###############################################################################
# Speed
###############################################################################

@st.cache_data(show_spinner=False)
def cal_speed(dva_dataframe):
    df = dva_dataframe.copy()
    df["Speed (v)"] = df["Speed Change (delta v)"].cumsum()
    return df

###############################################################################
# Distance change (delta d)
###############################################################################

@st.cache_data(show_spinner=False)
def cal_distance_change(dva_dataframe):
    df = dva_dataframe.copy()

    df["Distance Change (delta d)"] = (
        df["Speed (v)"].shift(1).fillna(0)
        + df["Speed (v)"]
    ) / 2 * df["Δt"]

    return df

###############################################################################
# Distance
###############################################################################

@st.cache_data(show_spinner=False)
def cal_distance(dva_dataframe):
    df = dva_dataframe.copy()
    df["Distance (d)"] = df["Distance Change (delta d)"].cumsum()
    return df
