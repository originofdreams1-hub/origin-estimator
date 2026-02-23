import io
import zipfile
from datetime import datetime, date

import pandas as pd
import streamlit as st

# PDF tools
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Origin Estimator", layout="centered")

# ----------------------------
# CONFIG (edit anytime)
# ----------------------------
LEAD_RATE = 75.0
HELPER_RATE = 30.0
DEFAULT_MARGIN = 0.30

COMPANY_NAME = "Origin of Dreams Construction LLC"
PHONE = "469-793-4345"
EMAIL = "originofdreams1@gmail.com"
WEBSITE = "www.originofdreams-construction.com"

LOGO_PATH = "logo.png"  # must exist in repo root


# ----------------------------
# SESSION STORAGE
# ----------------------------
if "estimates" not in st.session_state:
    st.session_state.estimates = []  # list of dicts (saved estimates)

if "uploads" not in st.session_state:
    st.session_state.uploads = {
        "photos": [],    # list of {"name":..., "bytes":...}
        "receipts": []   # list of {"name":..., "bytes":..., "vendor":..., "date":..., "total":...}
    }


# ----------------------------
# HELPERS
# ----------------------------
def money(x: float) -> str:
    return f"${x:,.2f}"


def build_pdf_bytes(
    logo_bytes: bytes | None,
    project_name: str,
    client_name: str,
    project_notes: str,
    items: list[dict],
    labor_total: float,
    materials_total: float,
    travel_total: float,
    subtotal: float,
    margin: float,
    final_price: float,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    w, h = LETTER

    # Header
    top_y = h - 0.75 * inch

    # Logo (optional)
    if logo_bytes:
        try:
            img = ImageReader(io.BytesIO(logo_bytes))
            c.drawImage(img, 0.75 * inch, h - 1.35 * inch, width=1.0 * inch, height=1.0 * inch, mask="auto")
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.9 * inch, top_y, "Estimate")

    c.setFont("Helvetica", 10)
    c.drawString(1.9 * inch, top_y - 14, COMPANY_NAME)
    c.drawString(1.9 * inch, top_y - 28, f"{PHONE}  |  {EMAIL}")
    c.drawString(1.9 * inch, top_y - 42, WEBSITE)

    c.setFont("Helvetica", 10)
    right_x = 5.2 * inch
    c.drawString(right_x, top_y, f"Date: {date.today().isoformat()}")
    c.drawString(right_x, top_y - 14, f"Client: {client_name or '-'}")
    c.drawString(right_x, top_y - 28, f"Project: {project_name or '-'}")

    # Notes
    y = top_y - 70
    c.setFont("Helvetica-Bold", 11)
    c.drawString(0.75 * inch, y, "Project Notes")
    y -= 14
    c.setFont("Helvetica", 10)
    note = (project_notes or "").strip()
    if not note:
        note = "-"
    # basic wrap
    max_chars = 105
    lines = [note[i:i+max_chars] for i in range(0, len(note), max_chars)]
    for line in lines[:4]:
        c.drawString(0.75 * inch, y, line)
        y -= 12

    # Items Table Header
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(0.75 * inch, y, "Line Items")
    y -= 14

    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.75 * inch, y, "Item")
    c.drawString(3.65 * inch, y, "Qty")
    c.drawString(4.05 * inch, y, "Labor")
    c.drawString(4.85 * inch, y, "Mat")
    c.drawString(5.50 * inch, y, "Travel")
    c.drawString(6.25 * inch, y, "Line Total")
    y -= 10
    c.line(0.75 * inch, y, 7.75 * inch, y)
    y -= 12

    # Items
    c.setFont("Helvetica", 9)
    for it in items:
        qty = float(it["qty"])
        line_labor = qty * (it["lead_hours"] * LEAD_RATE + it["helper_hours"] * HELPER_RATE)
        line_mat = qty * it["materials"]
        line_travel = qty * it["travel"]
        line_total = line_labor + line_mat + line_travel

        name = (it["name"] or "").strip() or "Item"
        # trim long names
        if len(name) > 45:
            name = name[:42] + "..."

        c.drawString(0.75 * inch, y, name)
        c.drawRightString(3.90 * inch, y, f"{int(it['qty'])}")
        c.drawRightString(4.75 * inch, y, money(line_labor))
        c.drawRightString(5.40 * inch, y, money(line_mat))
        c.drawRightString(6.10 * inch, y, money(line_travel))
        c.drawRightString(7.75 * inch, y, money(line_total))
        y -= 12

        if y < 1.6 * inch:
            c.showPage()
            y = h - 0.9 * inch
            c.setFont("Helvetica-Bold", 11)
            c.drawString(0.75 * inch, y, "Line Items (cont.)")
            y -= 20
            c.setFont("Helvetica", 9)

    # Totals box
    y -= 10
    if y < 2.2 * inch:
        c.showPage()
        y = h - 1.0 * inch

    c.setFont("Helvetica-Bold", 11)
    c.drawString(0.75 * inch, y, "Totals")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(0.75 * inch, y, f"Labor: {money(labor_total)}"); y -= 12
    c.drawString(0.75 * inch, y, f"Materials: {money(materials_total)}"); y -= 12
    c.drawString(0.75 * inch, y, f"Travel/Tolls: {money(travel_total)}"); y -= 12
    c.drawString(0.75 * inch, y, f"Subtotal: {money(subtotal)}"); y -= 12
    c.drawString(0.75 * inch, y, f"Margin: {margin*100:.0f}%"); y -= 14

    c.setFont("Helvetica-Bold", 13)
    c.drawString(0.75 * inch, y, f"Estimated Total: {money(final_price)}")

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(0.75 * inch, 0.75 * inch, "Estimate is a budgetary quote. Final pricing may change with scope changes or site conditions.")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


def get_logo_bytes() -> bytes | None:
    try:
        with open(LOGO_PATH, "rb") as f:
            return f.read()
    except Exception:
        return None


def make_zip_bytes(photos, receipts) -> bytes:
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in photos:
            z.writestr(f"photos/{p['name']}", p["bytes"])
        for r in receipts:
            # store receipt file
            z.writestr(f"receipts/{r['name']}", r["bytes"])
        # also store a CSV summary for receipts
        if receipts:
            df = pd.DataFrame([{
                "filename": r["name"],
                "vendor": r.get("vendor", ""),
                "date": r.get("date", ""),
                "total": r.get("total", 0.0),
            } for r in receipts])
            z.writestr("receipts/receipt_log.csv", df.to_csv(index=False))
    zbuf.seek(0)
    return zbuf.read()


# ----------------------------
# UI
# ----------------------------
st.image(LOGO_PATH, width=110)
st.title("Origin of Dreams Estimator")

st.caption(f"Rates locked: Lead {money(LEAD_RATE)}/hr | Helper {money(HELPER_RATE)}/hr")

st.subheader("Project Info")
c1, c2 = st.columns(2)
with c1:
    client_name = st.text_input("Client name")
with c2:
    project_name = st.text_input("Project name")
project_notes = st.text_area("Notes (optional)", height=90)

st.divider()

st.subheader("Line Items (Multiple Parts)")
num_items = st.number_input("How many items?", min_value=1, value=3, step=1)

items = []
for i in range(int(num_items)):
    st.markdown(f"### Item {i+1}")
    a, b = st.columns([3, 1])
    with a:
        name = st.text_input("Item name", key=f"name_{i}", placeholder="e.g., Cabinet carcass / Doors / Drawer boxes / Shelves / Install")
    with b:
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
        materials = st.number_input("Materials ($)", min_value=0.0, value=0.0, step=5.0, key=f"mat_{i}")
    with m2:
        travel = st.number_input("Travel/Tolls ($)", min_value=0.0, value=0.0, step=5.0, key=f"trav_{i}")

    items.append({
        "name": name.strip() if name else f"Item {i+1}",
        "qty": int(qty),
        "w": float(width),
        "h": float(height),
        "d": float(depth),
        "lead_hours": float(lead_hours),
        "helper_hours": float(helper_hours),
        "materials": float(materials),
        "travel": float(travel),
    })

st.divider()

st.subheader("Totals")
margin = st.slider("Margin (%)", min_value=0, max_value=60, value=int(DEFAULT_MARGIN * 100), step=1) / 100.0

labor_total = 0.0
materials_total = 0.0
travel_total = 0.0

for it in items:
    qty = float(it["qty"])
    labor_total += qty * (it["lead_hours"] * LEAD_RATE + it["helper_hours"] * HELPER_RATE)
    materials_total += qty * it["materials"]
    travel_total += qty * it["travel"]

subtotal = labor_total + materials_total + travel_total
final_price = subtotal / (1 - margin) if subtotal > 0 else 0.0

t1, t2, t3, t4 = st.columns(4)
t1.metric("Labor", money(labor_total))
t2.metric("Materials", money(materials_total))
t3.metric("Travel/Tolls", money(travel_total))
t4.metric("Final Price", money(final_price))

with st.expander("Show breakdown table"):
    rows = []
    for it in items:
        qty = float(it["qty"])
        line_labor = qty * (it["lead_hours"] * LEAD_RATE + it["helper_hours"] * HELPER_RATE)
        line_mat = qty * it["materials"]
        line_travel = qty * it["travel"]
        rows.append({
            "Item": it["name"],
            "Qty": it["qty"],
            "W(in)": it["w"],
            "H(in)": it["h"],
            "D(in)": it["d"],
            "Lead hrs": it["lead_hours"],
            "Helper hrs": it["helper_hours"],
            "Materials($)": it["materials"],
            "Travel($)": it["travel"],
            "Line Total($)": round(line_labor + line_mat + line_travel, 2),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.divider()

# ----------------------------
# Uploads: Photos + Receipts
# ----------------------------
st.subheader("Client Photos & Receipts")

up1, up2 = st.columns(2)

with up1:
    st.markdown("**Upload Photos**")
    photo_files = st.file_uploader(
        "Add photos (optional)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="photos_uploader"
    )
    if photo_files:
        for f in photo_files:
            st.session_state.uploads["photos"].append({"name": f.name, "bytes": f.getvalue()})
        st.success(f"Added {len(photo_files)} photo(s).")

with up2:
    st.markdown("**Upload Receipts**")
    receipt_files = st.file_uploader(
        "Add receipts (image or PDF)",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True,
        key="receipts_uploader"
    )
    if receipt_files:
        for f in receipt_files:
            st.session_state.uploads["receipts"].append({
                "name": f.name,
                "bytes": f.getvalue(),
                "vendor": "",
                "date": "",
                "total": 0.0,
            })
        st.success(f"Added {len(receipt_files)} receipt(s).")

# Receipt metadata editor
if st.session_state.uploads["receipts"]:
    st.markdown("### Receipt Log (Vendor / Date / Total)")
    for idx, r in enumerate(st.session_state.uploads["receipts"]):
        cA, cB, cC, cD = st.columns([2, 1, 1, 1])
        with cA:
            r["vendor"] = st.text_input("Vendor", value=r.get("vendor", ""), key=f"vendor_{idx}")
        with cB:
            r["date"] = st.text_input("Date", value=r.get("date", ""), key=f"date_{idx}", placeholder="YYYY-MM-DD")
        with cC:
            r["total"] = st.number_input("Total ($)", min_value=0.0, value=float(r.get("total", 0.0)), step=1.0, key=f"total_{idx}")
        with cD:
            st.write(" ")
            if st.button("Remove", key=f"remove_receipt_{idx}"):
                st.session_state.uploads["receipts"].pop(idx)
                st.rerun()

st.divider()

# ----------------------------
# Save / Export
# ----------------------------
st.subheader("Save & Export")

btn1, btn2, btn3 = st.columns(3)

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

estimate_record = {
    "timestamp": now,
    "client_name": client_name,
    "project_name": project_name,
    "margin_pct": round(margin * 100, 0),
    "labor": round(labor_total, 2),
    "materials": round(materials_total, 2),
    "travel": round(travel_total, 2),
    "subtotal": round(subtotal, 2),
    "final_price": round(final_price, 2),
}

with btn1:
    if st.button("Save estimate to history"):
        st.session_state.estimates.append(estimate_record)
        st.success("Saved to history (this session).")

with btn2:
    # PDF for current estimate
    logo_bytes = get_logo_bytes()
    pdf_bytes = build_pdf_bytes(
        logo_bytes=logo_bytes,
        project_name=project_name,
        client_name=client_name,
        project_notes=project_notes,
        items=items,
        labor_total=labor_total,
        materials_total=materials_total,
        travel_total=travel_total,
        subtotal=subtotal,
        margin=margin,
        final_price=final_price,
    )
    st.download_button(
        "Download PDF estimate",
        data=pdf_bytes,
        file_name=f"Estimate_{client_name or 'Client'}_{project_name or 'Project'}.pdf".replace(" ", "_"),
        mime="application/pdf",
    )

with btn3:
    # ZIP of uploads
    zip_bytes = make_zip_bytes(st.session_state.uploads["photos"], st.session_state.uploads["receipts"])
    st.download_button(
        "Download photos+receipts ZIP",
        data=zip_bytes,
        file_name=f"Uploads_{client_name or 'Client'}_{project_name or 'Project'}.zip".replace(" ", "_"),
        mime="application/zip",
    )

# History + CSV export
if st.session_state.estimates:
    st.markdown("## Estimate History (this session)")
    hist_df = pd.DataFrame(st.session_state.estimates)
    st.dataframe(hist_df, use_container_width=True)

    st.download_button(
        "Download ledger CSV",
        data=hist_df.to_csv(index=False).encode("utf-8"),
        file_name="origin_estimate_ledger.csv",
        mime="text/csv"
    )
else:
    st.caption("No saved estimates yet. Click **Save estimate to history** to start your ledger.")
