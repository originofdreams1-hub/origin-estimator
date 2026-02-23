import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import io
from datetime import datetime

# -----------------------------
# COMPANY INFO
# -----------------------------
COMPANY_NAME = "Origin of Dreams Construction LLC"
COMPANY_ADDRESS_DEFAULT = "Lewisville, TX"
COMPANY_PHONE = "469-793-4345"
COMPANY_EMAIL = "originofdreams1@gmail.com"

LOGO_PATH = "logo.png"  # must be exactly this filename in your GitHub repo


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Origin Estimator", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
def money(x: float) -> str:
    try:
        return f"${x:,.2f}"
    except Exception:
        return "$0.00"


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def calc_line_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'Cubic In' and 'Line Materials $' placeholder column for future use.
    Right now it just computes size metrics; you can later tie material calc to volume/area.
    """
    out = df.copy()

    for col in ["Qty", "Width (in)", "Height (in)", "Depth (in)"]:
        if col not in out.columns:
            out[col] = 0

    out["Qty"] = out["Qty"].apply(safe_float)
    out["Width (in)"] = out["Width (in)"].apply(safe_float)
    out["Height (in)"] = out["Height (in)"].apply(safe_float)
    out["Depth (in)"] = out["Depth (in)"].apply(safe_float)

    out["Cubic In"] = (out["Qty"] * out["Width (in)"] * out["Height (in)"] * out["Depth (in)"]).round(2)
    return out


def create_pdf(payload: dict) -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    page_w, page_h = letter

    # Layout helpers
    left = 40
    right = page_w - 40
    y = page_h - 40

    # Logo
    try:
        c.drawImage(LOGO_PATH, left, y - 80, width=90, preserveAspectRatio=True, mask="auto")
    except Exception:
        pass

    # Company header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left + 110, y - 10, COMPANY_NAME)

    c.setFont("Helvetica", 10)
    c.drawString(left + 110, y - 26, payload.get("company_address", COMPANY_ADDRESS_DEFAULT))
    c.drawString(left + 110, y - 40, COMPANY_PHONE)
    c.drawString(left + 110, y - 54, COMPANY_EMAIL)

    y -= 105
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left, y, "Estimate")
    c.setFont("Helvetica", 10)
    c.drawString(right - 200, y, f"Date: {payload.get('date_str','')}")
    y -= 18

    # Client
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Client")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(left, y, payload.get("client_name", ""))
    y -= 14
    c.drawString(left, y, payload.get("client_address", ""))
    y -= 22

    # Project
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Project")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(left, y, payload.get("project_name", ""))
    y -= 22

    # Summary
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Summary")
    y -= 16
    c.setFont("Helvetica", 10)

    summary_lines = [
        ("Labor", money(payload.get("labor_cost", 0.0))),
        ("Materials", money(payload.get("materials_cost", 0.0))),
        ("Travel", money(payload.get("travel_cost", 0.0))),
        ("Subtotal", money(payload.get("subtotal", 0.0))),
        (f"Margin ({int(payload.get('margin',0.30)*100)}%)", money(payload.get("margin_amount", 0.0))),
        ("Total Price", money(payload.get("total_price", 0.0))),
    ]
    for label, val in summary_lines:
        c.drawString(left, y, f"{label}:")
        c.drawRightString(right, y, val)
        y -= 14

    y -= 10

    # Line items table
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Line Items")
    y -= 16

    # Table headers
    c.setFont("Helvetica-Bold", 9)
    headers = ["Item", "Qty", "W", "H", "D", "Notes"]
    col_x = [left, left + 210, left + 245, left + 285, left + 325, left + 365]
    for i, h in enumerate(headers):
        c.drawString(col_x[i], y, h)
    y -= 10
    c.line(left, y, right, y)
    y -= 12

    c.setFont("Helvetica", 9)
    items = payload.get("items", [])
    for row in items:
        # New page if needed
        if y < 80:
            c.showPage()
            y = page_h - 50
            c.setFont("Helvetica-Bold", 11)
            c.drawString(left, y, "Line Items (cont.)")
            y -= 20
            c.setFont("Helvetica", 9)

        c.drawString(col_x[0], y, str(row.get("Item", ""))[:34])
        c.drawString(col_x[1], y, str(row.get("Qty", "")))
        c.drawString(col_x[2], y, str(row.get("Width (in)", "")))
        c.drawString(col_x[3], y, str(row.get("Height (in)", "")))
        c.drawString(col_x[4], y, str(row.get("Depth (in)", "")))
        c.drawString(col_x[5], y, str(row.get("Notes", ""))[:40])
        y -= 12

    # Footer
    y = 40
    c.setFont("Helvetica", 8)
    c.drawString(left, y, "Estimate is based on provided details and may change after site verification / final design approval.")
    c.save()

    buffer.seek(0)
    return buffer


# -----------------------------
# HEADER BAR (Logo + Title)
# -----------------------------
top_left, top_right = st.columns([1, 3], vertical_alignment="center")

with top_left:
    try:
        logo = Image.open(LOGO_PATH)
        st.image(logo, width=170)
    except Exception:
        pass

with top_right:
    st.markdown(
        """
        <div style="padding-top:8px;">
            <h1 style="margin-bottom:0;">Origin Estimator</h1>
            <div style="opacity:0.75; font-size:16px;">Fast pricing, travel, and PDF estimate generator</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# -----------------------------
# INIT LINE ITEMS
# -----------------------------
if "items_df" not in st.session_state:
    st.session_state.items_df = pd.DataFrame(
        [
            {"Item": "Cabinet", "Qty": 1, "Width (in)": 48, "Height (in)": 34.5, "Depth (in)": 24, "Notes": ""},
            {"Item": "Door", "Qty": 2, "Width (in)": 18, "Height (in)": 30, "Depth (in)": 0.75, "Notes": "Shaker"},
        ]
    )

# -----------------------------
# INPUTS LAYOUT
# -----------------------------
left_col, right_col = st.columns([2, 1], gap="large")

with left_col:
    st.subheader("Client & Project")

    a1, a2, a3 = st.columns([1.2, 1, 1])
    with a1:
        project_name = st.text_input("Project name", value="")
    with a2:
        client_name = st.text_input("Client name", value="")
    with a3:
        date_str = st.text_input("Date", value=datetime.now().strftime("%Y-%m-%d"))

    b1, b2 = st.columns([1, 1])
    with b1:
        client_address = st.text_input("Client address", value="")
    with b2:
        company_address = st.text_input("Your shop address", value=COMPANY_ADDRESS_DEFAULT)

    st.subheader("Line Items (multiple parts per project)")
    st.caption("Add as many items as you want — cabinets, doors, shelves, rails, etc.")

    edited = st.data_editor(
        st.session_state.items_df,
        num_rows="dynamic",
        use_container_width=True,
        key="items_editor",
        column_config={
            "Item": st.column_config.TextColumn(width="medium"),
            "Qty": st.column_config.NumberColumn(min_value=0, step=1),
            "Width (in)": st.column_config.NumberColumn(min_value=0.0, step=0.25),
            "Height (in)": st.column_config.NumberColumn(min_value=0.0, step=0.25),
            "Depth (in)": st.column_config.NumberColumn(min_value=0.0, step=0.25),
            "Notes": st.column_config.TextColumn(width="large"),
        },
    )
    st.session_state.items_df = edited

    st.subheader("Labor / Materials / Travel / Margin")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        lead_hours = st.number_input("Lead hours", min_value=0.0, value=0.0, step=0.5)
    with c2:
        lead_rate = st.number_input("Lead rate ($/hr)", min_value=0.0, value=85.0, step=1.0)
    with c3:
        helper_hours = st.number_input("Helper hours", min_value=0.0, value=0.0, step=0.5)
    with c4:
        helper_rate = st.number_input("Helper rate ($/hr)", min_value=0.0, value=45.0, step=1.0)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        materials_cost = st.number_input("Materials cost ($)", min_value=0.0, value=0.0, step=25.0)
    with d2:
        distance_miles = st.number_input("Travel distance (miles)", min_value=0.0, value=0.0, step=1.0)
    with d3:
        travel_rate = st.number_input("Travel rate ($/mile)", min_value=0.0, value=0.75, step=0.05)
    with d4:
        margin = st.slider("Margin (%)", min_value=0, max_value=60, value=30, step=1) / 100.0


# -----------------------------
# CALCULATIONS
# -----------------------------
travel_cost = distance_miles * travel_rate
labor_cost = lead_hours * lead_rate + helper_hours * helper_rate
subtotal = labor_cost + materials_cost + travel_cost
total_price = subtotal / (1 - margin) if subtotal > 0 and margin < 1 else 0.0
margin_amount = total_price - subtotal if total_price > 0 else 0.0

items_df_calc = calc_line_totals(st.session_state.items_df)

# -----------------------------
# RIGHT PANEL (TOP ESTIMATOR)
# -----------------------------
with right_col:
    st.subheader("Estimator (Top Summary)")

    # This keeps the estimate visible immediately (what you asked for)
    st.metric("Total Price", money(total_price))
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Subtotal", money(subtotal))
        st.metric("Labor", money(labor_cost))
    with m2:
        st.metric("Margin", money(margin_amount))
        st.metric("Travel", money(travel_cost))

    st.divider()

    st.caption("Quick check on your line items:")
    st.dataframe(
        items_df_calc[["Item", "Qty", "Width (in)", "Height (in)", "Depth (in)", "Cubic In"]],
        use_container_width=True,
        height=220
    )

    st.divider()

    # PDF button
    payload = {
        "project_name": project_name,
        "client_name": client_name,
        "client_address": client_address,
        "company_address": company_address,
        "date_str": date_str,
        "labor_cost": labor_cost,
        "materials_cost": materials_cost,
        "travel_cost": travel_cost,
        "subtotal": subtotal,
        "margin": margin,
        "margin_amount": margin_amount,
        "total_price": total_price,
        "items": items_df_calc.rename(columns={"Item": "Item"}).to_dict(orient="records"),
    }

    pdf = create_pdf(payload)
    st.download_button(
        "Download Estimate PDF",
        data=pdf,
        file_name=f"estimate_{project_name.strip().replace(' ','_') or 'project'}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.divider()
st.caption("Tip: Make sure the logo file in your repo is named exactly **logo.png** (lowercase).")
