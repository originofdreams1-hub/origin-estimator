import io
import math
from datetime import date, datetime

import streamlit as st
import pandas as pd

from PIL import Image
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Origin of Dreams Estimator",
    page_icon="🧰",
    layout="wide",
)

# ----------------------------
# ONE-TIME STATE RESET (prevents widget/key conflicts after edits)
# ----------------------------
APP_VERSION = 3
if st.session_state.get("app_version") != APP_VERSION:
    st.session_state.clear()
    st.session_state["app_version"] = APP_VERSION

# ----------------------------
# CONSTANTS (edit these)
# ----------------------------
DEFAULT_YOUR_ADDRESS = "Lewisville, TX"
DEFAULT_LEAD_RATE = 75.0
DEFAULT_HELPER_RATE = 30.0
DEFAULT_MARGIN = 0.30

LOGO_FILE = "logo.png"  # upload a file named EXACTLY logo.png to your repo (same folder as app.py)


# ----------------------------
# HELPERS
# ----------------------------
def money(x: float) -> str:
    try:
        return f"${x:,.2f}"
    except Exception:
        return "$0.00"


def safe_float(x, default=0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def ensure_items_df():
    if "items" not in st.session_state:
        st.session_state["items"] = pd.DataFrame(
            [
                {
                    "Qty": 1,
                    "Item": "Example: Cabinet door replacement",
                    "Width (in)": 0.0,
                    "Height (in)": 0.0,
                    "Depth (in)": 0.0,
                    "Material $": 0.0,
                    "Labor hrs": 0.0,
                    "Notes": "",
                }
            ]
        )


def reset_current_estimate():
    st.session_state["est_date"] = date.today()
    st.session_state["project_name"] = ""
    st.session_state["client_name"] = ""
    st.session_state["client_address"] = ""
    st.session_state["your_address"] = DEFAULT_YOUR_ADDRESS

    st.session_state["lead_hours"] = 0.0
    st.session_state["helper_hours"] = 0.0
    st.session_state["lead_rate"] = DEFAULT_LEAD_RATE
    st.session_state["helper_rate"] = DEFAULT_HELPER_RATE

    st.session_state["materials_cost"] = 0.0
    st.session_state["subcontract_cost"] = 0.0
    st.session_state["misc_cost"] = 0.0

    # travel options
    st.session_state["travel_mode"] = "Manual travel cost"
    st.session_state["roundtrip_miles"] = 0.0
    st.session_state["mileage_rate"] = 0.75  # dollars per mile (edit if you want)
    st.session_state["manual_travel_cost"] = 0.0

    st.session_state["margin"] = DEFAULT_MARGIN

    # items
    ensure_items_df()


def init_history():
    if "history" not in st.session_state:
        st.session_state["history"] = []


def calc_items_totals(df: pd.DataFrame, lead_rate: float, helper_rate: float):
    df2 = df.copy()
    # make sure numeric
    for col in ["Qty", "Width (in)", "Height (in)", "Depth (in)", "Material $", "Labor hrs"]:
        if col in df2.columns:
            df2[col] = pd.to_numeric(df2[col], errors="coerce").fillna(0.0)

    df2["Qty"] = df2["Qty"].clip(lower=0)
    df2["Line Material $"] = df2["Qty"] * df2["Material $"]
    # labor hrs here are assumed LEAD hours (simple)
    df2["Line Labor $"] = df2["Qty"] * df2["Labor hrs"] * lead_rate
    df2["Line Total $"] = df2["Line Material $"] + df2["Line Labor $"]

    items_material = float(df2["Line Material $"].sum())
    items_labor = float(df2["Line Labor $"].sum())
    items_total = float(df2["Line Total $"].sum())
    return df2, items_material, items_labor, items_total


def travel_cost(mode: str, miles: float, mileage_rate: float, manual: float) -> float:
    if mode == "Mileage (round-trip miles × rate)":
        return max(0.0, miles) * max(0.0, mileage_rate)
    return max(0.0, manual)


def make_pdf(estimate: dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    w, h = LETTER

    left = 0.75 * inch
    top = h - 0.75 * inch
    y = top

    # Logo (optional)
    try:
        img = Image.open(LOGO_FILE)
        # draw a bigger logo
        logo_w = 1.6 * inch
        aspect = img.height / img.width
        logo_h = logo_w * aspect
        c.drawImage(LOGO_FILE, left, y - logo_h, width=logo_w, height=logo_h, mask="auto")
        x_title = left + logo_w + 0.35 * inch
    except Exception:
        x_title = left

    c.setFont("Helvetica-Bold", 18)
    c.drawString(x_title, y - 0.15 * inch, "Origin of Dreams Estimator")
    c.setFont("Helvetica", 10)
    c.drawString(x_title, y - 0.45 * inch, f"Date: {estimate['date']}")
    c.drawString(x_title, y - 0.65 * inch, f"Project: {estimate['project_name']}")
    c.drawString(x_title, y - 0.85 * inch, f"Client: {estimate['client_name']}")

    y -= 1.2 * inch

    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Addresses")
    y -= 0.2 * inch
    c.setFont("Helvetica", 10)
    c.drawString(left, y, f"Your address: {estimate['your_address']}")
    y -= 0.2 * inch
    c.drawString(left, y, f"Client address: {estimate['client_address']}")
    y -= 0.35 * inch

    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Summary")
    y -= 0.25 * inch
    c.setFont("Helvetica", 10)

    summary_lines = [
        ("Items (material)", money(estimate["items_material"])),
        ("Items (labor)", money(estimate["items_labor"])),
        ("Labor (lead/helper)", money(estimate["labor_cost"])),
        ("Materials (extra)", money(estimate["materials_cost"])),
        ("Subcontract", money(estimate["subcontract_cost"])),
        ("Misc", money(estimate["misc_cost"])),
        ("Travel", money(estimate["travel_cost"])),
        ("Subtotal", money(estimate["subtotal"])),
        (f"Margin ({int(estimate['margin']*100)}%)", money(estimate["margin_amount"])),
        ("Final Total", money(estimate["final_total"])),
    ]

    for label, val in summary_lines:
        c.drawString(left, y, f"{label}:")
        c.drawRightString(w - left, y, val)
        y -= 0.2 * inch

    y -= 0.2 * inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y, "Line Items")
    y -= 0.25 * inch
    c.setFont("Helvetica", 9)

    # table header
    headers = ["Qty", "Item", "W", "H", "D", "Mat $", "Hrs", "Line Total $"]
    cols = [left, left + 0.5*inch, left + 3.4*inch, left + 3.85*inch, left + 4.3*inch, left + 4.75*inch, left + 5.55*inch, left + 6.1*inch]
    for i, head in enumerate(headers):
        c.drawString(cols[i], y, head)
    y -= 0.18 * inch
    c.line(left, y, w - left, y)
    y -= 0.12 * inch

    for row in estimate["items_rows"]:
        if y < 1.1 * inch:
            c.showPage()
            y = h - 0.75 * inch
            c.setFont("Helvetica-Bold", 11)
            c.drawString(left, y, "Line Items (continued)")
            y -= 0.3 * inch
            c.setFont("Helvetica", 9)

        c.drawString(cols[0], y, str(int(row.get("Qty", 0))))
        c.drawString(cols[1], y, str(row.get("Item", ""))[:40])
        c.drawString(cols[2], y, f"{safe_float(row.get('Width (in)', 0)):g}")
        c.drawString(cols[3], y, f"{safe_float(row.get('Height (in)', 0)):g}")
        c.drawString(cols[4], y, f"{safe_float(row.get('Depth (in)', 0)):g}")
        c.drawString(cols[5], y, money(safe_float(row.get("Material $", 0))))
        c.drawString(cols[6], y, f"{safe_float(row.get('Labor hrs', 0)):g}")
        c.drawRightString(w - left, y, money(safe_float(row.get("Line Total $", 0))))
        y -= 0.18 * inch

    y -= 0.25 * inch
    c.setFont("Helvetica", 8)
    c.drawString(left, y, "Note: This is a budgetary estimate. Final pricing may change after site verification / scope confirmation.")
    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ----------------------------
# INIT
# ----------------------------
init_history()
if "project_name" not in st.session_state:
    reset_current_estimate()

ensure_items_df()

# ----------------------------
# HEADER (logo + title)
# ----------------------------
col_logo, col_title, col_btn = st.columns([1.2, 4.5, 1.3], vertical_alignment="center")

with col_logo:
    try:
        st.image(LOGO_FILE, use_container_width=True)
    except Exception:
        st.warning("Upload your logo as **logo.png** to the repo (same folder as app.py).")

with col_title:
    st.title("Origin of Dreams Estimator")
    st.caption("Build multi-line estimates, add travel, save history, and export to PDF.")

with col_btn:
    if st.button("➕ New Estimate", use_container_width=True):
        reset_current_estimate()
        st.rerun()

st.divider()

# ----------------------------
# MAIN LAYOUT
# ----------------------------
left, right = st.columns([2.2, 1.1], gap="large")

with left:
    st.subheader("Project Details")

    a, b, c = st.columns(3)
    with a:
        st.session_state["est_date"] = st.date_input("Date", value=st.session_state["est_date"])
    with b:
        st.session_state["project_name"] = st.text_input("Project", value=st.session_state["project_name"])
    with c:
        st.session_state["client_name"] = st.text_input("Client", value=st.session_state["client_name"])

    st.session_state["your_address"] = st.text_input("Your address", value=st.session_state["your_address"])
    st.session_state["client_address"] = st.text_input("Client address", value=st.session_state["client_address"])

    st.divider()
    st.subheader("Items (add as many as you want)")

    st.caption("Tip: Use Qty + dimensions for each line item. Labor hrs here are per item (lead hours).")

    edited = st.data_editor(
        st.session_state["items"],
        num_rows="dynamic",
        use_container_width=True,
        key="items_editor",
    )

    # persist edits back to session
    st.session_state["items"] = edited

    st.divider()
    st.subheader("Labor (overall)")

    l1, l2, l3, l4 = st.columns(4)
    with l1:
        st.session_state["lead_hours"] = st.number_input("Lead hours", min_value=0.0, value=float(st.session_state["lead_hours"]), step=0.5)
    with l2:
        st.session_state["lead_rate"] = st.number_input("Lead rate ($/hr)", min_value=0.0, value=float(st.session_state["lead_rate"]), step=1.0)
    with l3:
        st.session_state["helper_hours"] = st.number_input("Helper hours", min_value=0.0, value=float(st.session_state["helper_hours"]), step=0.5)
    with l4:
        st.session_state["helper_rate"] = st.number_input("Helper rate ($/hr)", min_value=0.0, value=float(st.session_state["helper_rate"]), step=1.0)

    st.divider()
    st.subheader("Costs")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state["materials_cost"] = st.number_input("Materials (extra) $", min_value=0.0, value=float(st.session_state["materials_cost"]), step=10.0)
    with c2:
        st.session_state["subcontract_cost"] = st.number_input("Subcontract $", min_value=0.0, value=float(st.session_state["subcontract_cost"]), step=10.0)
    with c3:
        st.session_state["misc_cost"] = st.number_input("Misc $", min_value=0.0, value=float(st.session_state["misc_cost"]), step=10.0)

    st.divider()
    st.subheader("Travel")

    st.session_state["travel_mode"] = st.selectbox(
        "How do you want to calculate travel?",
        ["Manual travel cost", "Mileage (round-trip miles × rate)"],
        index=0 if st.session_state["travel_mode"] == "Manual travel cost" else 1,
    )

    t1, t2, t3 = st.columns(3)
    with t1:
        st.session_state["roundtrip_miles"] = st.number_input("Round-trip miles", min_value=0.0, value=float(st.session_state["roundtrip_miles"]), step=1.0)
    with t2:
        st.session_state["mileage_rate"] = st.number_input("Mileage rate ($/mile)", min_value=0.0, value=float(st.session_state["mileage_rate"]), step=0.05)
    with t3:
        st.session_state["manual_travel_cost"] = st.number_input("Manual travel cost $", min_value=0.0, value=float(st.session_state["manual_travel_cost"]), step=5.0)

    st.divider()
    st.subheader("Margin")

    st.session_state["margin"] = st.slider("Margin", min_value=0.0, max_value=0.60, value=float(st.session_state["margin"]), step=0.01)


with right:
    st.subheader("Estimate Summary")

    # compute totals
    df_lines, items_material, items_labor, items_total = calc_items_totals(
        st.session_state["items"],
        lead_rate=float(st.session_state["lead_rate"]),
        helper_rate=float(st.session_state["helper_rate"]),
    )

    labor_cost = (
        float(st.session_state["lead_hours"]) * float(st.session_state["lead_rate"])
        + float(st.session_state["helper_hours"]) * float(st.session_state["helper_rate"])
    )

    t_cost = travel_cost(
        st.session_state["travel_mode"],
        float(st.session_state["roundtrip_miles"]),
        float(st.session_state["mileage_rate"]),
        float(st.session_state["manual_travel_cost"]),
    )

    subtotal = (
        items_total
        + labor_cost
        + float(st.session_state["materials_cost"])
        + float(st.session_state["subcontract_cost"])
        + float(st.session_state["misc_cost"])
        + t_cost
    )

    margin = float(st.session_state["margin"])
    margin_amount = subtotal * margin
    final_total = subtotal + margin_amount

    st.metric("Subtotal", money(subtotal))
    st.metric(f"Margin ({int(margin*100)}%)", money(margin_amount))
    st.metric("Final Total", money(final_total))

    with st.expander("Breakdown", expanded=True):
        st.write(f"**Items (material):** {money(items_material)}")
        st.write(f"**Items (labor):** {money(items_labor)}")
        st.write(f"**Labor (lead/helper):** {money(labor_cost)}")
        st.write(f"**Materials (extra):** {money(float(st.session_state['materials_cost']))}")
        st.write(f"**Subcontract:** {money(float(st.session_state['subcontract_cost']))}")
        st.write(f"**Misc:** {money(float(st.session_state['misc_cost']))}")
        st.write(f"**Travel:** {money(t_cost)}")

    st.divider()

    # build estimate dict for saving/pdf
    estimate = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "date": str(st.session_state["est_date"]),
        "project_name": st.session_state["project_name"],
        "client_name": st.session_state["client_name"],
        "your_address": st.session_state["your_address"],
        "client_address": st.session_state["client_address"],
        "items_rows": df_lines.to_dict(orient="records"),
        "items_material": items_material,
        "items_labor": items_labor,
        "labor_cost": labor_cost,
        "materials_cost": float(st.session_state["materials_cost"]),
        "subcontract_cost": float(st.session_state["subcontract_cost"]),
        "misc_cost": float(st.session_state["misc_cost"]),
        "travel_cost": t_cost,
        "subtotal": subtotal,
        "margin": margin,
        "margin_amount": margin_amount,
        "final_total": final_total,
    }

    # Buttons
    save_col, pdf_col = st.columns(2)

    with save_col:
        if st.button("💾 Save to History", use_container_width=True):
            st.session_state["history"].insert(0, estimate)
            st.success("Saved to history.")
            st.rerun()

    with pdf_col:
        pdf_bytes = make_pdf(estimate)
        st.download_button(
            "📄 Download PDF",
            data=pdf_bytes,
            file_name=f"Estimate_{st.session_state['client_name'] or 'Client'}_{st.session_state['project_name'] or 'Project'}.pdf".replace(" ", "_"),
            mime="application/pdf",
            use_container_width=True,
        )

    st.divider()
    st.subheader("History")

    if len(st.session_state["history"]) == 0:
        st.caption("No saved estimates yet. Click **Save to History** to store one.")
    else:
        for i, e in enumerate(st.session_state["history"][:10]):  # show latest 10
            title = f"{e['date']} — {e['client_name'] or 'Client'} — {e['project_name'] or 'Project'} — {money(e['final_total'])}"
            with st.expander(title, expanded=False):
                st.write(f"**Saved:** {e['timestamp']}")
                st.write(f"**Your address:** {e['your_address']}")
                st.write(f"**Client address:** {e['client_address']}")
                st.write(f"**Final total:** {money(e['final_total'])}")

                # quick load
                if st.button(f"Load this estimate #{i+1}", key=f"load_{i}"):
                    # load into current state
                    st.session_state["est_date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    st.session_state["project_name"] = e["project_name"]
                    st.session_state["client_name"] = e["client_name"]
                    st.session_state["your_address"] = e["your_address"]
                    st.session_state["client_address"] = e["client_address"]

                    st.session_state["materials_cost"] = e["materials_cost"]
                    st.session_state["subcontract_cost"] = e["subcontract_cost"]
                    st.session_state["misc_cost"] = e["misc_cost"]
                    st.session_state["margin"] = e["margin"]

                    # reset labor inputs (kept simple here)
                    st.session_state["lead_hours"] = 0.0
                    st.session_state["helper_hours"] = 0.0

                    # restore items
                    st.session_state["items"] = pd.DataFrame(e["items_rows"]).drop(columns=["Line Material $", "Line Labor $", "Line Total $"], errors="ignore")

                    st.success("Loaded.")
                    st.rerun()
