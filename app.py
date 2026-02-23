import io
from datetime import datetime

import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Origin Estimator", layout="centered")

# =========================
# LOGO
# =========================
logo_path = "logo.png"
try:
    logo = Image.open(logo_path)
    st.image(logo, width=260)
except:
    st.warning("Logo not found")

# =========================
# BUSINESS INFO
# =========================
BUSINESS_NAME = "Origin of Dreams Construction LLC"
BUSINESS_ADDRESS = "Lewisville, TX"
BUSINESS_PHONE = "469-793-4345"
BUSINESS_EMAIL = "originofdreams1@gmail.com"

# =========================
# CLIENT INFO
# =========================
st.header("Client Information")

client_name = st.text_input("Client name")
client_address = st.text_input("Client address")

st.header("Project")

project_name = st.text_input("Project name")
width = st.number_input("Width (inches)", min_value=0.0)
height = st.number_input("Height (inches)", min_value=0.0)
depth = st.number_input("Depth (inches)", min_value=0.0)

st.header("Labor")

lead_hours = st.number_input("Lead hours", min_value=0.0)
lead_rate = st.number_input("Lead hourly rate ($)", value=85.0)

helper_hours = st.number_input("Helper hours", min_value=0.0)
helper_rate = st.number_input("Helper hourly rate ($)", value=35.0)

st.header("Costs")

materials = st.number_input("Materials cost ($)", min_value=0.0)
travel_cost = st.number_input("Travel cost ($)", min_value=0.0)
other_cost = st.number_input("Other cost ($)", min_value=0.0)

margin = st.slider("Margin %", 0, 50, 30)

# =========================
# CALCULATIONS
# =========================
labor_cost = lead_hours * lead_rate + helper_hours * helper_rate
subtotal = labor_cost + materials + travel_cost + other_cost
price = subtotal / (1 - margin / 100) if subtotal > 0 else 0

st.header("Estimate Summary")

st.write(f"Labor: ${labor_cost:,.2f}")
st.write(f"Materials: ${materials:,.2f}")
st.write(f"Travel: ${travel_cost:,.2f}")
st.write(f"Other: ${other_cost:,.2f}")
st.write(f"Subtotal: ${subtotal:,.2f}")

st.success(f"ESTIMATE PRICE: ${price:,.2f}")

# =========================
# PDF GENERATION
# =========================
def generate_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width_page, height_page = letter

    # Logo
    try:
        img = ImageReader(logo_path)
        c.drawImage(img, 40, height_page - 120, width=140, preserveAspectRatio=True, mask='auto')
    except:
        pass

    y = height_page - 150

    # Business
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, BUSINESS_NAME)
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(40, y, BUSINESS_ADDRESS)
    y -= 14
    c.drawString(40, y, BUSINESS_PHONE)
    y -= 14
    c.drawString(40, y, BUSINESS_EMAIL)

    # Client
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Client:")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(40, y, client_name)
    y -= 14
    c.drawString(40, y, client_address)

    # Project
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Project:")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(40, y, project_name)
    y -= 14
    c.drawString(40, y, f"Dimensions: {width} x {height} x {depth} inches")

    # Costs
    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Costs:")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Labor: ${labor_cost:,.2f}")
    y -= 14
    c.drawString(40, y, f"Materials: ${materials:,.2f}")
    y -= 14
    c.drawString(40, y, f"Travel: ${travel_cost:,.2f}")
    y -= 14
    c.drawString(40, y, f"Other: ${other_cost:,.2f}")
    y -= 14
    c.drawString(40, y, f"Subtotal: ${subtotal:,.2f}")

    # Final price
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Estimate: ${price:,.2f}")

    # Date
    y -= 30
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Generated: {datetime.now().strftime('%Y-%m-%d')}")

    c.save()
    buffer.seek(0)
    return buffer

# =========================
# PDF BUTTON
# =========================
if st.button("Generate PDF"):
    pdf = generate_pdf()
    st.download_button(
        "Download Estimate PDF",
        data=pdf,
        file_name="Origin_Estimate.pdf",
        mime="application/pdf"
    )
