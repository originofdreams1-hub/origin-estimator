import os
import io
from datetime import datetime

import streamlit as st
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch


# ---------------------------
# Config
# ---------------------------
st.set_page_config(
    page_title="Origin of Dreams Estimator",
    layout="wide",
)

COMPANY_NAME = "Origin of Dreams Construction LLC"
COMPANY_EMAIL = "originofdreams1@gmail.com"
COMPANY_PHONE = "469-793-4345"
COMPANY_WEBSITE = "www.originofdreams-construction.com"

LOGO_PATHS_TO_TRY = [
    "logo.png",
    "Logo.png",
    "assets/logo.png",
    "images/logo.png",
]


def find_logo_path():
    for p in LOGO_PATHS_TO_TRY:
        if os.path.exists(p):
            return p
    return None


def money(x: float) -> str:
    try:
        return f"${x:,.2f}"
    except Exception:
        return "$0.00"


def safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


# ---------------------------
# PDF Builder
# ---------------------------
def build_pdf(
    logo_path: str | None,
    client_name: str,
    project_name: str,
    your_address: str,
    client_address: str,
    notes: str,
    parts_df: pd.DataFrame,
    lead_hours: float,
    helper_hours: float,
    lead_rate: float,
    helper_rate: float,
    materials_cost: float,
    travel_miles: float,
    rate_per_mile: float,
    travel_fixed: float,
    margin: float,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    left = 0.75 * inch
    right = width - 0.75 * inch
    y = height - 0.75 * inch

    # Logo + Header
    if logo_path:
        try:
            img = ImageReader(logo_path)
            # Bigger logo
            logo_w = 2.1 * inch
