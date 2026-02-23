import streamlit as st

st.set_page_config(page_title="Origin Estimator", layout="centered")

# --- Simple brand styling ---
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; max-width: 900px;}
      .brandbar {
        display:flex; align-items:center; gap:14px;
        padding: 14px 16px; border-radius: 14px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 18px;
      }
      .brandtitle {font-size: 28px; font-weight: 800; margin: 0;}
      .brandsub {opacity: 0.8; margin: 0; font-size: 14px;}
      .totals {
        padding: 14px 16px; border-radius: 14px;
        background: rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.10);
      }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
colA, colB = st.columns([1, 4], vertical_alignment="center")
with colA:
    st.image("logo.png", width=90)
with colB:
    st.markdown(
        """
        <div class="brandbar">
          <div>
            <p class="brandtitle">Origin of Dreams Estimator</p>
            <p class="brandsub">Fast, itemized estimates — Labor + Materials + Travel + Margin</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Project info ---
st.subheader("Project Info")
project_name = st.text_input("Project name / client")
notes = st.text_area("Notes (optional)", height=80)

# --- Rates (locked in) ---
LEAD_RATE = 75.0
HELPER_RATE = 30.0

with st.expander("Rates (locked)", expanded=False):
    st.write(f"Lead rate: **${LEAD_RATE:.2f}/hr**")
    st.write(f"Helper rate: **${HELPER_RATE:.2f}/hr**")

# --- Line items (multiple parts) ---
st.subheader("Line Items (Parts)")

num_items = st.number_input("How many parts/items are you estimating?", min_value=1, value=3, step=1)

items = []
for i in range(int(num_items)):
    st.markdown(f"### Item {i+1}")
    c1, c2 = st.columns([2, 1])
    with c1:
        item_name = st.text_input("Item name", key=f"name_{i}", placeholder="e.g., Base cabinet carcass / Door set / Shelves / Trim run")
    with c2:
        qty = st.number_input("Qty", min_value=1, value=1, step=1, key=f"qty_{i}")

    d1, d2, d3 = st.columns(3)
    with d1:
        width = st.number_input("Width (in)", min_value=0.0, value=0.0, step=0.25, key=f"w_{i}")
    with d2:
        height = st.number_input("Height (in)", min_value=0.0, value=0.0, step=0.25, key=f"h_{i}")
    with d3:
        depth = st.number_input("Depth (in)", min_value=0.0, value=0.0, step=0.25, key=f"d_{i}")

    l1, l2 = st.columns(2)
    with l1:
        lead_hours = st.number_input("Lead hours", min_value=0.0, value=0.0, step=0.25, key=f"lead_{i}")
    with l2:
        helper_hours = st.number_input("Helper hours", min_value=0.0, value=0.0, step=0.25, key=f"help_{i}")

    m1, m2 = st.columns(2)
    with m1:
        materials_cost = st.number_input("Materials cost ($)", min_value=0.0, value=0.0, step=5.0, key=f"mat_{i}")
    with m2:
        travel_cost = st.number_input("Travel/tolls cost ($)", min_value=0.0, value=0.0, step=5.0, key=f"trav_{i}")

    items.append(
        {
            "name": item_name.strip() or f"Item {i+1}",
            "qty": qty,
            "w": width,
            "h": height,
            "d": depth,
            "lead_hours": lead_hours,
            "helper_hours": helper_hours,
            "materials": materials_cost,
            "travel": travel_cost,
        }
    )

# --- Margin & totals ---
st.subheader("Totals")
margin = st.slider("Margin (%)", min_value=0, max_value=60, value=30, step=1) / 100.0

labor_total = 0.0
materials_total = 0.0
travel_total = 0.0

for it in items:
    qty = float(it["qty"])
    labor = qty * (it["lead_hours"] * LEAD_RATE + it["helper_hours"] * HELPER_RATE)
    labor_total += labor
    materials_total += qty * it["materials"]
    travel_total += qty * it["travel"]

subtotal = labor_total + materials_total + travel_total
final_price = subtotal / (1 - margin) if subtotal > 0 else 0.0

st.markdown(
    f"""
    <div class="totals">
      <p><b>Labor:</b> ${labor_total:,.2f}</p>
      <p><b>Materials:</b> ${materials_total:,.2f}</p>
      <p><b>Travel/Tolls:</b> ${travel_total:,.2f}</p>
      <hr/>
      <p><b>Subtotal:</b> ${subtotal:,.2f}</p>
      <p><b>Margin:</b> {margin*100:.0f}%</p>
      <p style="font-size:20px;"><b>Final Price:</b> ${final_price:,.2f}</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Optional: show a simple breakdown table ---
with st.expander("Show item breakdown"):
    rows = []
    for it in items:
        qty = float(it["qty"])
        row_labor = qty * (it["lead_hours"] * LEAD_RATE + it["helper_hours"] * HELPER_RATE)
        row_total = row_labor + qty * it["materials"] + qty * it["travel"]
        rows.append(
            {
                "Item": it["name"],
                "Qty": it["qty"],
                "W(in)": it["w"],
                "H(in)": it["h"],
                "D(in)": it["d"],
                "Lead hrs": it["lead_hours"],
                "Helper hrs": it["helper_hours"],
                "Materials($)": it["materials"],
                "Travel($)": it["travel"],
                "Line Total($)": round(row_total, 2),
            }
        )
    st.dataframe(rows, use_container_width=True)
