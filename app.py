import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import io
from datetime import datetime

# =============================
# COMPANY SETTINGS
# =============================
COMPANY_NAME = "Origin of Dreams Construction LLC"
COMPANY_PHONE = "469-793-4345"
COMPANY_EMAIL = "originofdreams1@gmail.com"
DEFAULT_COMPANY_ADDRESS = "Lewisville, TX"
LOGO_PATH = "logo.png"   # logo file must be in repo root

# =============================
# PAGE
# =============================
st.set_page_config(page_title="Origin Estimator", layout="wide")

# =============================
# HELPERS
# =============================
def money(x):
    try:
        return f"${float(x):,.2f}"
    except:
        return "$0.00"

def safe_float(v):
    try:
        return float(v)
    except:
        return 0.0

def calc_items(df):
    df = df.copy()
    for c in ["Qty", "Width", "Height", "Depth"]:
        df[c] = df[c].apply(safe_float)
    df["CubicIn"] = df["Qty"] * df["Width"] * df["Height"] * df["Depth"]
    return df

def create_pdf(data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    W, H = letter

    left = 40
    right = W - 40
    y = H - 40

    # Logo
    try:
        c.drawImage(LOGO_PATH, left, y - 80, width=90, preserveAspectRatio=True, mask="auto")
    except:
        pass

    # Company
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left + 110, y - 10, COMPANY_NAME)
    c.setFont("Helvetica", 10)
    c.drawString(left + 110, y - 26, data.get("company_address",""))
    c.drawString(left + 110, y - 40, COMPANY_PHONE)
    c.drawString(left + 110, y - 54, COMPANY_EMAIL)

    y -= 100

    # Client
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Client")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(left, y, data.get("client_name",""))
    y -= 14
    c.drawString(left, y, data.get("client_address",""))

    y -= 25

    # Project
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Project")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(left, y, data.get("project",""))
    y -= 14
    c.drawString(left, y, f"Date: {data.get('date','')}")
    y -= 25

    # Summary
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Summary")
    y -= 14
    c.setFont("Helvetica", 10)

    lines = [
        ("Labor", data.get("labor",0.0)),
        ("Materials", data.get("materials",0.0)),
        ("Travel", data.get("travel",0.0)),
        ("Subtotal", data.get("subtotal",0.0)),
        ("Margin", data.get("margin_amt",0.0)),
        ("Total", data.get("total",0.0)),
    ]
    for label, val in lines:
        c.drawString(left, y, f"{label}:")
        c.drawRightString(right, y, money(val))
        y -= 14

    y -= 10

    # Items
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Items")
    y -= 14

    c.setFont("Helvetica-Bold", 9)
    headers = ["Item", "Qty", "W", "H", "D", "Notes"]
    xs = [left, left+210, left+240, left+270, left+300, left+330]
    for i,h in enumerate(headers):
        c.drawString(xs[i], y, h)
    y -= 10

    c.setFont("Helvetica", 9)
    for r in data.get("items", []):
        if y < 80:
            c.showPage()
            y = H - 40
        c.drawString(xs[0], y, str(r.get("Item",""))[:30])
        c.drawString(xs[1], y, str(r.get("Qty","")))
        c.drawString(xs[2], y, str(r.get("Width","")))
        c.drawString(xs[3], y, str(r.get("Height","")))
        c.drawString(xs[4], y, str(r.get("Depth","")))
        c.drawString(xs[5], y, str(r.get("Notes",""))[:40])
        y -= 12

    c.save()
    buffer.seek(0)
    return buffer

def default_items_df():
    return pd.DataFrame([
        {"Item":"Cabinet","Qty":1,"Width":48,"Height":34.5,"Depth":24,"Notes":""},
        {"Item":"Door","Qty":2,"Width":18,"Height":30,"Depth":0.75,"Notes":"Shaker"},
    ])

# =============================
# SESSION STATE INIT
# =============================
if "items" not in st.session_state:
    st.session_state.items = default_items_df()

if "history" not in st.session_state:
    st.session_state.history = []  # list of saved estimates (dicts)

# Input defaults stored in session keys so we can reset them
defaults = {
    "project": "",
    "client": "",
    "date": datetime.now().strftime("%Y-%m-%d"),
    "client_addr": "",
    "company_addr": DEFAULT_COMPANY_ADDRESS,
    "lead_h": 0.0,
    "lead_r": 85.0,
    "help_h": 0.0,
    "help_r": 45.0,
    "mat": 0.0,
    "miles": 0.0,
    "rate": 0.75,
    "margin_pct": 30,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================
# HEADER
# =============================
col1, col2 = st.columns([1,3], vertical_alignment="center")

with col1:
    try:
        st.image(Image.open(LOGO_PATH), width=170)
    except:
        pass

with col2:
    st.markdown("## Origin Estimator")
    st.caption("Multi-item • Travel • Margin • PDF • Save History")

st.divider()

# =============================
# LAYOUT
# =============================
left, right = st.columns([2,1], gap="large")

with left:
    st.subheader("Client / Project")

    a,b,c = st.columns(3)
    with a:
        project = st.text_input("Project", key="project")
    with b:
        client = st.text_input("Client", key="client")
    with c:
        date = st.text_input("Date", key="date")

    a,b = st.columns(2)
    with a:
        client_addr = st.text_input("Client address", key="client_addr")
    with b:
        company_addr = st.text_input("Your address", key="company_addr")

    st.subheader("Items (add as many as you want)")
    edited = st.data_editor(
        st.session_state.items,
        num_rows="dynamic",
        use_container_width=True
    )
    st.session_state.items = edited

    st.subheader("Labor / Materials / Travel")

    a,b,c,d = st.columns(4)
    with a:
        lead_h = st.number_input("Lead hrs", min_value=0.0, max_value=1000.0, step=0.5, key="lead_h")
    with b:
        lead_r = st.number_input("Lead $/hr", min_value=0.0, max_value=500.0, step=1.0, key="lead_r")
    with c:
        help_h = st.number_input("Helper hrs", min_value=0.0, max_value=1000.0, step=0.5, key="help_h")
    with d:
        help_r = st.number_input("Helper $/hr", min_value=0.0, max_value=500.0, step=1.0, key="help_r")

    a,b,c,d = st.columns(4)
    with a:
        mat = st.number_input("Materials $", min_value=0.0, max_value=100000.0, step=25.0, key="mat")
    with b:
        miles = st.number_input("Miles", min_value=0.0, max_value=2000.0, step=1.0, key="miles")
    with c:
        rate = st.number_input("$ per mile", min_value=0.0, max_value=10.0, step=0.05, key="rate")
    with d:
        margin_pct = st.slider("Margin %", min_value=0, max_value=60, value=int(st.session_state["margin_pct"]), step=1, key="margin_pct")

# =============================
# CALC
# =============================
margin = float(margin_pct) / 100.0
travel = safe_float(miles) * safe_float(rate)
labor = safe_float(lead_h) * safe_float(lead_r) + safe_float(help_h) * safe_float(help_r)
subtotal = labor + safe_float(mat) + travel
total = subtotal/(1-margin) if subtotal>0 and margin < 0.95 else 0.0
margin_amt = total - subtotal if total > 0 else 0.0

items_calc = calc_items(st.session_state.items)

# =============================
# RIGHT PANEL SUMMARY + BUTTONS
# =============================
with right:
    st.subheader("Estimator (Top Summary)")

    st.metric("Total", money(total))
    st.metric("Subtotal", money(subtotal))

    a,b = st.columns(2)
    with a:
        st.metric("Labor", money(labor))
        st.metric("Travel", money(travel))
    with b:
        st.metric("Materials", money(mat))
        st.metric("Margin", money(margin_amt))

    st.divider()

    st.caption("Items preview:")
    st.dataframe(items_calc[["Item","Qty","Width","Height","Depth"]], height=200, use_container_width=True)

    st.divider()

    # ---- SAVE + NEW ESTIMATE BUTTONS
    b1, b2 = st.columns(2)
    with b1:
        save_clicked = st.button("Save Estimate", use_container_width=True)
    with b2:
        new_clicked = st.button("New Estimate", use_container_width=True)

    # Build current estimate payload (for PDF + Save)
    estimate_payload = {
        "date": date,
        "project": project,
        "client_name": client,
        "client_address": client_addr,
        "company_address": company_addr,
        "labor": labor,
        "materials": float(mat),
        "travel": travel,
        "subtotal": subtotal,
        "margin_amt": margin_amt,
        "total": total,
        "margin_pct": margin_pct,
        "lead_hours": float(lead_h),
        "lead_rate": float(lead_r),
        "helper_hours": float(help_h),
        "helper_rate": float(help_r),
        "miles": float(miles),
        "rate_per_mile": float(rate),
        "items": items_calc.to_dict("records"),
    }

    # Save estimate to session history
    if save_clicked:
        # minimal validation
        if not project.strip():
            st.warning("Add a Project name before saving.")
        else:
            st.session_state.history.append(estimate_payload)
            st.success("Saved to History (this session). Download CSV to keep it permanently.")

    # New estimate resets fields
    if new_clicked:
        # reset input keys
        for k, v in defaults.items():
            st.session_state[k] = v
        # reset items
        st.session_state.items = default_items_df()
        st.rerun()

    # ---- PDF Download
    pdf = create_pdf(estimate_payload)
    st.download_button(
        "Download PDF",
        data=pdf,
        file_name=f"estimate_{(project.strip().replace(' ','_') or 'project')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# =============================
# HISTORY SECTION
# =============================
st.divider()
st.subheader("Saved Estimates (History)")

if len(st.session_state.history) == 0:
    st.info("No saved estimates yet. Click **Save Estimate** to add one.")
else:
    # show compact table
    hist_rows = []
    for e in st.session_state.history:
        hist_rows.append({
            "Date": e.get("date",""),
            "Client": e.get("client_name",""),
            "Project": e.get("project",""),
            "Total": e.get("total",0.0),
            "Labor": e.get("labor",0.0),
            "Materials": e.get("materials",0.0),
            "Travel": e.get("travel",0.0),
            "Margin %": e.get("margin_pct",0),
        })
    hist_df = pd.DataFrame(hist_rows)
    # format money columns nicely in display
    show_df = hist_df.copy()
    for col in ["Total","Labor","Materials","Travel"]:
        show_df[col] = show_df[col].apply(money)

    st.dataframe(show_df, use_container_width=True)

    # download CSV (permanent)
    csv_df = hist_df.copy()
    csv_df["Total"] = csv_df["Total"].apply(safe_float)
    csv_df["Labor"] = csv_df["Labor"].apply(safe_float)
    csv_df["Materials"] = csv_df["Materials"].apply(safe_float)
    csv_df["Travel"] = csv_df["Travel"].apply(safe_float)

    st.download_button(
        "Download History CSV (Permanent)",
        data=csv_df.to_csv(index=False).encode("utf-8"),
        file_name="origin_estimate_history.csv",
        mime="text/csv",
        use_container_width=True
    )
