"""
Master generator for FleetIQ synthetic documents.

  python data/generate_docs.py

Produces in data/docs/:
  - clean PDFs for most documents
  - messy scanned-style PNGs for a realistic subset (heavy degradation)
  - manifest.json : ground truth (which truck/driver/load each doc belongs to,
    doc_type, format, messiness) — the eval harness grades against this.

Frequency is realistic: fuel receipts & ELD logs are frequent; 2290, titles,
medical certs, annual inspections are rare (annual). That imbalance is part of
the realism and a retrieval challenge.
"""
import os, json, random, io
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as _canvas

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fleet_backbone import build_fleet, build_loads, CARRIER
import renderers as R
from messify import messify, HAND_FONT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "docs")
os.makedirs(OUT, exist_ok=True)

# register handwriting font for the POD signature
try:
    pdfmetrics.registerFont(TTFont("Caveat", HAND_FONT)); HF = "Caveat"
except Exception:
    HF = "Helvetica-Oblique"

# realistic counts — scaled for a ~25-truck carrier, ~2 months of paper (1000+ docs)
# Volume docs (randomly distributed across the fleet). The annual per-truck
# official docs (title, 2290, registration) are emitted separately, one per truck.
FREQ = {
    "fuel_receipt": 250, "eld_log": 200, "rate_confirmation": 110,
    "bill_of_lading": 110, "proof_of_delivery": 100, "repair_invoice": 80,
    "roadside_inspection": 36, "ifta_return": 28,
    "dot_inspection": 25, "medical_cert": 25,
}
# which types get messy scan treatment (the field-collected ones)
MESSY_TYPES = {"fuel_receipt","proof_of_delivery","repair_invoice",
               "roadside_inspection","bill_of_lading","dot_inspection"}

HANDNOTES = {
    "fuel_receipt": ["DEF added", "reefer fuel", "cash tip $5", "rcpt for IFTA"],
    "repair_invoice": ["paid by card", "warranty?", "call shop re: brakes", "approved -JL"],
    "proof_of_delivery": ["2 pallets short!", "left at dock", "see notes", "rec'd 0830"],
    "roadside_inspection": ["contest this", "fixed lamp 4/2", "OOS cleared"],
    "bill_of_lading": ["detention 2hr", "lumper $150", "seal #4471"],
    "dot_inspection": ["recheck brakes", "passed reinsp", "minor - fixed"],
}

def render_pdf_bytes(draw_fn, *args):
    buf = io.BytesIO()
    c = _canvas.Canvas(buf, pagesize=letter)
    draw_fn(c, *args)
    c.showPage(); c.save()
    return buf.getvalue()

def main():
    # clear old
    for f in os.listdir(OUT):
        if f.endswith((".pdf",".png")): os.remove(os.path.join(OUT, f))

    trucks, drivers, trailers = build_fleet(25)
    loads = build_loads(trucks, 90)
    trucks_by_id = {t["truck_id"]: t for t in trucks}
    manifest = []
    idx = 0

    def emit(doc_type, draw_fn, draw_args, entity_tags, allow_messy=True):
        nonlocal idx
        idx += 1
        pdf = render_pdf_bytes(draw_fn, *draw_args)
        make_messy = allow_messy and doc_type in MESSY_TYPES and random.random() < 0.45
        level = "heavy" if make_messy else None
        base = f"doc_{idx:04d}_{doc_type}"
        if make_messy:
            pages = convert_from_bytes(pdf, dpi=130)
            notes = random.sample(HANDNOTES.get(doc_type, ["see file"]), k=random.randint(1,2))
            img = messify(pages[0], "heavy", notes=notes)
            fname = base + ".png"
            img.save(os.path.join(OUT, fname), "PNG")
            fmt = "scanned_image"
        else:
            fname = base + ".pdf"
            with open(os.path.join(OUT, fname), "wb") as fh: fh.write(pdf)
            fmt = "pdf"
        manifest.append({"file": fname, "doc_type": doc_type, "format": fmt,
                         "messy": bool(make_messy), **entity_tags})

    # volume truck-scoped docs (randomly distributed across the fleet)
    for dt, fn in [("repair_invoice", R.repair_invoice), ("fuel_receipt", R.fuel_receipt),
                   ("ifta_return", R.ifta_return), ("dot_inspection", R.dot_inspection)]:
        for _ in range(FREQ[dt]):
            t = random.choice(trucks)
            emit(dt, fn, (CARRIER, t), {"truck_id": t["truck_id"], "unit": t["unit"]})

    # annual per-truck official docs — every truck has exactly one of each on file
    for t in trucks:
        tag = {"truck_id": t["truck_id"], "unit": t["unit"]}
        emit("vehicle_title", R.vehicle_title, (CARRIER, t), tag)
        emit("form_2290", R.form_2290, (CARRIER, t), tag)
        emit("vehicle_registration", R.vehicle_registration, (CARRIER, t), tag)

    # load-scoped docs
    for _ in range(FREQ["bill_of_lading"]):
        l = random.choice(loads); emit("bill_of_lading", R.bill_of_lading, (CARRIER, l, trucks_by_id),
            {"truck_id": l["truck_id"], "load_id": l["load_id"]})
    for _ in range(FREQ["rate_confirmation"]):
        l = random.choice(loads); emit("rate_confirmation", R.rate_confirmation, (CARRIER, l),
            {"truck_id": l["truck_id"], "load_id": l["load_id"]})
    for _ in range(FREQ["proof_of_delivery"]):
        l = random.choice(loads); emit("proof_of_delivery", R.proof_of_delivery, (CARRIER, l, HF),
            {"truck_id": l["truck_id"], "load_id": l["load_id"]})

    # driver-scoped docs
    for _ in range(FREQ["medical_cert"]):
        d = random.choice(drivers); emit("medical_cert", R.medical_cert, (CARRIER, d),
            {"driver_id": d["driver_id"], "driver_name": d["name"]})
    for _ in range(FREQ["eld_log"]):
        d = random.choice(drivers); t = trucks[d["driver_id"]-1]
        emit("eld_log", R.eld_log, (CARRIER, t, d),
            {"truck_id": t["truck_id"], "driver_id": d["driver_id"]})
    for _ in range(FREQ["roadside_inspection"]):
        d = random.choice(drivers); t = trucks[d["driver_id"]-1]
        emit("roadside_inspection", R.roadside_inspection, (CARRIER, t, d),
            {"truck_id": t["truck_id"], "driver_id": d["driver_id"]})

    with open(os.path.join(ROOT, "data", "manifest.json"), "w") as f:
        json.dump({"carrier": CARRIER, "n_trucks": len(trucks), "documents": manifest}, f, indent=2, default=str)

    # also persist the structured backbone for the SQL side
    with open(os.path.join(ROOT, "data", "fleet_structured.json"), "w") as f:
        json.dump({"trucks": trucks, "drivers": drivers, "trailers": trailers, "loads": loads}, f, indent=2, default=str)

    n_messy = sum(1 for m in manifest if m["messy"])
    print(f"Generated {len(manifest)} documents ({n_messy} messy scans, {len(manifest)-n_messy} clean PDFs)")
    by = {}
    for m in manifest: by[m["doc_type"]] = by.get(m["doc_type"],0)+1
    for k,v in sorted(by.items(), key=lambda x:-x[1]): print(f"  {k:24s} {v}")

if __name__ == "__main__":
    main()
