import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Green H2 Digital Twin", layout="wide")
st.title("🌱 Green Hydrogen: Solar-to-Stack Digital Twin")

# --- SIDEBAR: ALL PARAMETERS ---
st.sidebar.header("1. Cell Physics")
temp = st.sidebar.slider("Operating Temperature (°C)", 20, 90, 60)
mem_thickness = st.sidebar.slider("Membrane Thickness (μm)", 50, 200, 125) / 1e4 

st.sidebar.header("2. Plant Scale")
solar_capacity = st.sidebar.number_input("Solar Array Capacity (kW)", value=100)
stack_size = st.sidebar.number_input("Stack Size (Number of Cells)", value=50)

st.sidebar.header("3. Economics")
elec_price = st.sidebar.slider("Electricity Price ($/kWh)", 0.01, 0.15, 0.05)
capex_kw = st.sidebar.slider("System CAPEX ($/kW)", 500, 2500, 1000)

# --- THE PHYSICS ENGINE ---
def simulate_system(T_c, thickness, solar_kw, cells):
    T = T_c + 273.15
    F, R = 96485, 8.314
    
    # Voltage calculation (Physics from your screenshot)
    V_rev = 1.229 - 0.0009 * (T - 298.15) 
    i_range = np.linspace(0.01, 2.0, 50)
    eta_act = (R * T / (0.5 * 2 * F)) * np.log(i_range / 1e-3)
    conductivity = (0.005139 * (T/303) - 0.00326) * 10
    eta_ohm = i_range * (thickness / conductivity)
    v_total = V_rev + eta_act + eta_ohm
    
    # Solar Cycle (24 Hours)
    hours = np.linspace(0, 24, 96)
    solar_profile = np.maximum(0, solar_kw * np.sin(np.pi * (hours - 6) / 12))
    
    # H2 Production (Faraday's Law)
    v_op = 1.85 # Average operating voltage
    total_current = (solar_profile * 1000) / (v_op * cells)
    h2_grams_hr = (total_current * 2.016) / (2 * 96485) * 3600
    
    return i_range, v_total, hours, solar_profile, h2_grams_hr

# Run simulation
i, v, hrs, sun, h2 = simulate_system(temp, mem_thickness, solar_capacity, stack_size)

# --- VISUALIZATION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Physics: Polarization Curve")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=i, y=v, name="Voltage Profile", line=dict(color='red')))
    fig1.update_layout(xaxis_title="Current Density (A/cm²)", yaxis_title="Voltage (V)")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Integration: 24hr Solar vs H2")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hrs, y=sun, name="Solar Power (kW)", fill='tozeroy'))
    fig2.add_trace(go.Scatter(x=hrs, y=h2, name="H2 Production (g/hr)", yaxis="y2"))
    fig2.update_layout(yaxis=dict(title="Solar (kW)"), yaxis2=dict(title="H2 (g/hr)", overlaying='y', side='right'))
    st.plotly_chart(fig2, use_container_width=True)

# --- ECONOMICS SECTION ---
st.markdown("---")
daily_h2_kg = np.trapezoid(h2, x=hrs) / 1000
annual_h2 = daily_h2_kg * 365
annual_op_cost = (solar_capacity * 2000) * elec_price
total_capex = solar_capacity * capex_kw
lcoh = (total_capex + (annual_op_cost * 10)) / (annual_h2 * 10)

m1, m2, m3 = st.columns(3)
m1.metric("Daily Production", f"{daily_h2_kg:.2f} kg/day")
m2.metric("System Efficiency", f"{(1.25 / np.interp(1.0, i, v))*100:.1f}%")
m3.metric("LCOH (Cost of H2)", f"${lcoh:.2f} /kg", delta_color="inverse")