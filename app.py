import streamlit as st

st.set_page_config(page_title="Origin Estimator", layout="centered")

st.title("Origin of Dreams Estimator")

st.header("Project Details")

project_name = st.text_input("Project name")
width = st.number_input("Width (inches)", min_value=0.0)
height = st.number_input("Height (inches)", min_value=0.0)
depth = st.number_input("Depth (inches)", min_value=0.0)

st.header("Labor")

lead_hours = st.number_input("Lead hours", min_value=0.0)
helper_hours = st.number_input("Helper hours", min_value=0.0)

lead_rate = 75
helper_rate = 30

labor_cost = lead_hours * lead_rate + helper_hours * helper_rate

st.header("Materials")

materials_cost = st.number_input("Materials cost ($)", min_value=0.0)

st.header("Travel")

travel_cost = st.number_input("Travel cost ($)", min_value=0.0)

subtotal = labor_cost + materials_cost + travel_cost
margin = 0.30
price = subtotal / (1 - margin) if subtotal > 0 else 0

st.header("Estimate")

st.write(f"Subtotal: ${subtotal:,.2f}")
st.write(f"Final Price (30% margin): ${price:,.2f}")

if st.button("Generate Estimate"):
    st.success(f"Estimated Price: ${price:,.2f}")