# FleetIQ Synthetic Dataset (Authentic Layouts)

**1,014 documents** across 12 real carrier document types, each rendered to mirror
the structure of the genuine form (Form 2290, IFTA-100, standard BOL, J.J. Keller
ELD log, MCSA-5876 medical cert, DVIR, etc.). Internally consistent: VINs, unit
numbers, EINs, trailer IDs, and load IDs match across all related documents.

Carrier: **Lone Star Freight LLC** — 25 trucks / 25 drivers / 25 trailers / 90 loads.
Registration states span TX, CA, FL, IL, GA (matching the real reg/title templates).

## Contents (`data/docs/`)
- **~734 clean PDFs** — born-digital forms with authentic field layouts
- **~280 messy scanned PNGs** — field-collected docs degraded with skew, coffee
  stains, ink stamps, hole punches, and handwritten margin notes (heavy realism)

## Document types & frequency (realistic mix)
fuel_receipt 250 · eld_log 200 · bill_of_lading 110 · rate_confirmation 110 ·
proof_of_delivery 100 · repair_invoice 80 · roadside_inspection 36 ·
form_2290 25 · vehicle_registration 25 · dot_inspection 25 · medical_cert 25 · ifta_return 28

## Each type mirrors its real form
- **Form 2290** — OMB 1545-0143, Part I tax lines, Schedule 1 VIN + Category V
- **IFTA return** — multi-jurisdiction table, real per-state rates, net tax due
- **Bill of Lading** — Ship From/To, SCAC, trailer/seal/pro numbers, NMFC class
- **ELD log** — 24-hour status grid (Off/SB/Driving/On), HOS compliance check
- **Medical cert** — MCSA-5876 sections, examiner registry number, expiry
- **DVIR / Annual DOT** — 49 CFR 396.17 component checklist, pass/fail
- ...and registration (IRP cab card), rate con, POD, fuel receipt, roadside

## Ground truth
- `data/manifest.json` — every doc tagged to truck/driver/load + doc_type + format + messy flag
- `data/fleet_structured.json` — trucks/drivers/trailers/loads backbone for the SQL side

## Regenerate
```
python data/generate_docs.py
```
