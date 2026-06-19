# Fleet Document Knowledge Base

A field-by-field reference for 12 core US trucking documents.
**Ingestion · Entity Resolution · RAG — Buildathon Reference**

---

## How to use this reference

Each form below follows the same layout: an **At a glance** box (purpose, issuer, frequency, primary link key), a **field-extraction table** of what your ingestion pipeline should pull, why the document matters to the system, the **realistic messiness** to bake into synthetic samples, and the **operator questions** it answers.

**Link key** is the most important concept: it is the identifier your entity-resolution layer uses to attach a document to the correct truck, driver, or trailer. When the link key is a VIN or card number rather than a unit number, resolving "truck 84" to that document is the core engineering challenge.

### The four query types to support

1. **Pure DB query** — e.g. "which registrations expire in 60 days?" (structured fields only)
2. **Pure document retrieval** — e.g. "find the signed POD for load 4821" (fetch the right file)
3. **Both at once** — e.g. "what do I need to renew truck 84 and how much have I spent on it?"
4. **Cross-document reconciliation** — e.g. "does my IFTA match my fuel receipts?"

---

## 1. IRS Form 2290 — Heavy Highway Vehicle Use Tax

> **At a glance**
> - **Purpose:** Federal tax proving a truck (55,000+ lbs) is paid up to use public highways. The stamped Schedule 1 is the real artifact — you cannot register a truck without it.
> - **Issued by:** IRS (federal)
> - **Frequency:** Annual — tax period runs July 1 to June 30, due by Aug 31
> - **Primary link key:** VIN (rarely a unit number)

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| EIN | Employer Identification Number — the business tax ID (never an SSN). |
| Business name & address | Registered owner of record. |
| VIN | Full 17-character vehicle ID for each truck. **This is the link key.** |
| Weight category | Letter A–V. Category A = 55,000 lbs and rises from there; determines tax owed. |
| Tax amount | Roughly $100–$550 per truck per year by weight category. |
| Logging vehicle? | Yes/No — logging trucks pay a reduced rate. |
| Stamped Schedule 1 | Proof-of-payment page listing every VIN with an IRS e-file stamp + date. |

### Why it matters for the system

- The link is by VIN, not unit number. "Find the 2290 for truck 84" forces: Truck 84 → resolve VIN → locate the 2290 row.
- Required prerequisite for vehicle registration renewal — connects directly to the Registration document.

### Realistic messiness

- Usually one filing covers the whole fleet — 10+ VINs on a single Schedule 1. "The 2290 for truck 84" is one row inside a shared PDF, not a standalone file.
- VIN may be the only identifier present — no unit number anywhere on the page.
- Often a clean digital PDF, but scanned copies with the IRS watermark are common.

**Sample operator questions**
- "Where's the tax form for truck 84?"
- "Is my 2290 current for the whole fleet?"
- "How much heavy-use tax did I pay this year?"

---

## 2. Vehicle Registration (Cab Card)

> **At a glance**
> - **Purpose:** State proof the truck is legally registered to a plate. The cab card lives in the truck. Drives all renewal questions.
> - **Issued by:** State DMV / DOT
> - **Frequency:** Annual renewal
> - **Primary link key:** VIN + Plate number

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Plate number | License plate tied to the truck. |
| VIN | 17-char vehicle ID — reliable link key. |
| Unit number | Sometimes present, often missing. |
| Year / Make / Model | e.g. 2021 Peterbilt 579. Soft signal for "the red Kenworth" type queries. |
| Registered owner | Business name + address. |
| Registered gross weight | Max weight the truck is registered to haul. |
| Effective & expiration dates | Critical — these drive renewal alerts. |
| Registration fee | Amount paid for the registration period. |
| State / jurisdiction list | Base state, or for IRP a full table of states + apportioned fees. |

### Why it matters for the system

- The core document behind "what do I need to renew these plates?" Expiration date powers renewal alerts.
- Renewal typically requires a current 2290 Schedule 1 + proof of insurance, so it links to multiple other docs.
- Two flavors: base-state registration vs. IRP apportioned (interstate) registration with a per-state table.

### Realistic messiness

- Unit number frequently absent — must resolve via VIN or plate.
- Dates appear in many formats across states (MM/DD/YY, Month DD YYYY, etc.).
- IRP version is a dense multi-state table that naive parsers mangle.

**Sample operator questions**
- "What documents do I need to renew these plates?"
- "Which registrations expire in the next 60 days?"
- "What's the plate number for the 2021 Peterbilt?"

---

## 3. Repair Invoice / Shop Work Order

> **At a glance**
> - **Purpose:** A bill from a shop or dealer for work on a truck. Highest-volume, messiest doc type. Behind every parts/labor spend question.
> - **Issued by:** Dealer service dept (Peterbilt/Kenworth/Freightliner), chains (TA/Petro, Speedco), or independent shops
> - **Frequency:** Ad hoc — high volume
> - **Primary link key:** Unit # / VIN / plate (often fuzzy or handwritten)

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Invoice # & date | Unique invoice identifier and service date. |
| Shop name & address | Who performed the work. |
| Truck identifier | The messy part — unit #, VIN, plate, or handwritten "Trk 84". |
| Odometer / mileage | Reading at time of service. |
| Parts line items | Part #, description, qty, unit price. |
| Labor line items | Description, hours, hourly rate. |
| Subtotals | Parts total, labor total, shop supplies, tax. |
| Grand total | Full amount due. |
| 3 C's | Complaint / Cause / Correction — describes the problem and fix. |

### Why it matters for the system

- The parts-vs-labor split lives here. "How much did I spend on parts?" means summing **only** parts line items, not labor or grand total.
- Linking each invoice to the right truck (fuzzy unit # / VIN) enables per-truck cost and profitability.

### Realistic messiness

- Truck referenced inconsistently: "Unit 84", "#84", "84", "VIN …841".
- Handwritten independent-shop receipts — an OCR nightmare.
- One invoice can cover **multiple trucks** — line items must be split per truck.
- Parts and labor sometimes lumped into one undifferentiated list.
- Truck number missing entirely — infer from date + driver or shop history.
- Faded thermal paper, photographed at an angle.

**Sample operator questions**
- "How much did I spend on parts last month?"
- "What's the total repair cost for truck 84 this year?"
- "Which truck has the highest maintenance spend?"

---

## 4. Fuel Receipt

> **At a glance**
> - **Purpose:** Per-fill-up record of diesel purchased. Very high volume; central to cost-per-mile and profitability math.
> - **Issued by:** Truck stops (Pilot, Flying J, Love's, TA) or fuel card providers (EFS, Comdata)
> - **Frequency:** Multiple per truck per week
> - **Primary link key:** Truck # / card # / driver (often weak)

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Date & time | When the fuel was purchased. |
| Location | Station name, city, state. Often blank or abbreviated. |
| Gallons | Volume purchased. |
| Price per gallon | Unit fuel price. |
| Total amount | Fuel cost (sometimes bundled with DEF, oil, snacks). |
| Fuel card / unit # | Fleet card number or unit number — main link key. |
| Driver name | Who fueled — sometimes the only identifier. |
| Odometer | Sometimes entered at the pump for MPG tracking. |
| State | Critical for IFTA — fuel must be attributed to the state of purchase. |

### Why it matters for the system

- Gallons-by-state feeds the IFTA Quarterly Return directly — links to that document.
- Fuel is the single largest variable cost; per-truck fuel spend is core to "which trucks are profitable?"

### Realistic messiness

- Thermal printouts, faded, photographed sideways — OCR-hostile.
- Location or state field often blank — must infer from station chain or nearby records.
- Total may bundle non-fuel items (DEF, oil, food) that must be excluded from fuel cost.
- Fuel-card Excel exports have inconsistent column headers month to month.
- Truck linked only by card number — needs a card→truck mapping table.

**Sample operator questions**
- "How much did I spend on fuel for truck 12 last month?"
- "What was my average price per gallon in Q2?"
- "How many gallons did truck 84 buy in Texas?"

---

## 5. IFTA Quarterly Return

> **At a glance**
> - **Purpose:** Quarterly fuel-tax reconciliation across states. You report miles driven and fuel bought per state; IFTA settles who you owe.
> - **Issued by:** Base-state DOT (filed by carrier)
> - **Frequency:** Quarterly (Q1–Q4)
> - **Primary link key:** Carrier (fleet-level) + per-truck breakdown

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Carrier name & IFTA # | The filing entity. |
| Quarter & year | Reporting period. |
| Miles by jurisdiction | Total miles driven in each state/province. |
| Gallons by jurisdiction | Fuel purchased in each state. |
| Fleet MPG | Computed average used to allocate tax. |
| Tax due / credit per state | Net owed or refunded by jurisdiction. |
| Total balance | Net tax due for the quarter. |

### Why it matters for the system

- A fleet-level aggregate doc that's built **from** fuel receipts + mileage (ELD) — natural cross-document question.
- "Does my IFTA filing match my fuel receipts?" needs both DB aggregation and document retrieval in one answer.

### Realistic messiness

- Aggregated at carrier level — per-truck attribution must be reconstructed from underlying fuel + mileage.
- State abbreviations vs. full names vs. codes used inconsistently.
- Filing may be a spreadsheet, a portal screenshot, or a PDF.

**Sample operator questions**
- "What did I owe for IFTA in Q2?"
- "Which states cost me the most fuel tax?"
- "Does my Q2 IFTA match my fuel receipts?"

---

## 6. Annual DOT Inspection Report

> **At a glance**
> - **Purpose:** Federally required annual safety inspection. Every truck and trailer must pass once a year and keep the report on file.
> - **Issued by:** Certified inspector / shop
> - **Frequency:** Annual, per vehicle
> - **Primary link key:** Unit # + VIN

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Vehicle ID | Unit # and/or VIN of inspected vehicle. |
| Inspection date | When performed — drives the next-due date. |
| Inspector name & cert # | Who certified the inspection. |
| Pass / fail result | Overall outcome. |
| Component checklist | Brakes, tires, lights, steering, coupling, etc., each marked OK/defect. |
| Defects noted | Items needing repair. |
| Next due date | Inspection expires in 12 months. |

### Why it matters for the system

- Compliance-deadline document — "which trucks are due for inspection?" is a date-driven DB query.
- Failed inspections link to Repair Invoices (the fix) — a cross-document chain.

### Realistic messiness

- Checkbox-heavy form — OCR struggles with marks and handwriting.
- Defect notes are free text needing interpretation.
- Truck vs. trailer inspections look similar but must be linked to the right asset.

**Sample operator questions**
- "Which trucks are due for inspection this quarter?"
- "Did truck 84 pass its last DOT inspection?"
- "Show me all failed inspections this year."

---

## 7. Bill of Lading (BOL)

> **At a glance**
> - **Purpose:** The legal contract + receipt for a single freight load. Lists shipper, consignee, and cargo. Required for every load.
> - **Issued by:** Shipper (issued at pickup)
> - **Frequency:** Per load
> - **Primary link key:** Load/PRO # + truck + driver + trailer

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| BOL / PRO number | Unique load identifier. |
| Shipper | Origin company + address. |
| Consignee | Destination company + address. |
| Carrier & truck/trailer | Who hauled it and on what equipment. |
| Commodity description | What was shipped. |
| Weight & piece count | Cargo weight and number of units/pallets. |
| Pickup & delivery dates | Load timeline. |
| Freight charge terms | Prepaid / collect / third-party. |

### Why it matters for the system

- Ties a load to a specific truck/driver/trailer — backbone of revenue-per-truck and utilization.
- Pairs with the Rate Confirmation (what you were paid) and POD (proof it was delivered).

### Realistic messiness

- Truck/trailer fields often handwritten or blank.
- Cargo weight on BOL may differ from the scale ticket.
- Multi-stop loads list several consignees on one BOL.

**Sample operator questions**
- "What did truck 84 haul last week?"
- "Find the BOL for load 4821."
- "How many loads did each truck run in May?"

---

## 8. Rate Confirmation (Rate Con)

> **At a glance**
> - **Purpose:** Broker's written agreement of what the carrier will be paid for a load. The revenue side of every trip.
> - **Issued by:** Freight broker (Coyote, Echo, CH Robinson, etc.)
> - **Frequency:** Per load
> - **Primary link key:** Load # (matches the BOL) + truck/driver

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Rate confirmation # | Broker's load reference. |
| Broker name & MC # | The paying party. |
| Origin & destination | Lane for the load. |
| Pickup / delivery dates | Schedule and appointment times. |
| Agreed rate | Total linehaul pay + any accessorials (detention, fuel surcharge). |
| Equipment type | Van, reefer, flatbed, etc. |
| Assigned truck / driver | Who was dispatched. |

### Why it matters for the system

- The revenue number for profitability. Revenue (rate con) minus cost (fuel + repairs + tolls) = per-load and per-truck margin.
- Matches to the BOL by load number to confirm the load was both booked and moved.

### Realistic messiness

- Rate may be split across linehaul + accessorials that must be summed.
- Assigned truck sometimes changes after booking (re-dispatch) and isn't updated on the doc.
- Broker formats vary wildly — every broker's template is different.

**Sample operator questions**
- "What was the rate on load 4821?"
- "Which trucks are most profitable?"
- "What's my revenue per mile this month?"

---

## 9. Proof of Delivery (POD)

> **At a glance**
> - **Purpose:** Signed receipt confirming the consignee received the freight. Required to invoice the broker and get paid.
> - **Issued by:** Consignee (signed at delivery)
> - **Frequency:** Per load
> - **Primary link key:** Load/BOL # + delivery date

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| BOL / load number | Ties POD back to the load. |
| Delivery date & time | When it was received. |
| Receiver name & signature | Who signed for it. |
| Condition notes / OS&D | Over, Short & Damaged exceptions noted at delivery. |
| Piece / pallet count received | Confirms full delivery. |
| Stamp / seal | Receiver's stamp if applicable. |

### Why it matters for the system

- Closes the load loop: Rate Con (booked) → BOL (picked up) → POD (delivered = invoiceable).
- "Which loads are delivered but not yet invoiced?" is a cross-document gap question.

### Realistic messiness

- Often just a signed, re-scanned copy of the BOL — hard to tell BOL from POD.
- Signatures and stamps are illegible; handwritten exception notes.
- Photographed on a phone, skewed and low-contrast.

**Sample operator questions**
- "Was load 4821 delivered?"
- "Which loads are delivered but not invoiced?"
- "Find the signed POD for the Dallas delivery on May 3."

---

## 10. DOT Medical Certificate (Med Card)

> **At a glance**
> - **Purpose:** Proof a driver passed the federal DOT physical and is medically cleared to drive. Tied to the driver, not the truck.
> - **Issued by:** Certified medical examiner
> - **Frequency:** Expires every 24 months (or less)
> - **Primary link key:** Driver (name / license #)

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Driver name | Who was examined. |
| Exam date | When the physical was done. |
| Expiration date | When recertification is required — the key field. |
| Examiner name & National Registry # | Certifying medical examiner. |
| Restrictions | e.g. corrective lenses required. |
| CDL / license # | Links to the driver record. |

### Why it matters for the system

- Driver-compliance deadline doc — "which drivers' med cards expire soon?" is a date query on the driver entity.
- Resolving "J. Martinez" vs "Juan Martinez" vs "juan martinez" is the driver entity-resolution challenge.

### Realistic messiness

- Driver name appears in many forms across docs — needs entity resolution.
- Expiration date easy to confuse with exam date.
- Often a small card scanned at low resolution.

**Sample operator questions**
- "Which drivers' medical cards expire in the next 90 days?"
- "Is Juan's med card current?"
- "When does driver Martinez need to recertify?"

---

## 11. ELD / HOS Log

> **At a glance**
> - **Purpose:** Electronic logging device record of a driver's Hours of Service — drive time, on-duty, off-duty, sleeper. Also the source of mileage.
> - **Issued by:** ELD provider (Motive/KeepTruckin, Samsara, etc.)
> - **Frequency:** Daily / continuous
> - **Primary link key:** Driver + truck + date

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Driver | Whose log this is. |
| Truck / unit | Tractor associated with the log. |
| Date | Log day. |
| Duty status segments | Driving / On-duty / Off-duty / Sleeper, with times. |
| Total drive hours | Hours driven that day (HOS limit checks). |
| Miles driven | Daily mileage — feeds IFTA per-state miles. |
| Violations | Any HOS limit exceedances flagged. |

### Why it matters for the system

- Mileage source for IFTA per-state miles and for cost-per-mile — links to IFTA and fuel data.
- HOS-violation questions are compliance queries on the driver+date entity.

### Realistic messiness

- Exported as CSV/Excel with provider-specific schemas that differ across vendors.
- Driver may drive multiple trucks in a day; truck-of-record can be ambiguous.
- Edits/annotations to logs complicate the "true" record.

**Sample operator questions**
- "How many miles did truck 84 run in May?"
- "Did any driver have an HOS violation last week?"
- "How many hours did Juan drive on May 3?"

---

## 12. Roadside Inspection Report

> **At a glance**
> - **Purpose:** Record of a DOT roadside stop — a clean pass or a list of violations. Affects the carrier's CSA safety score.
> - **Issued by:** DOT / state enforcement officer
> - **Frequency:** Ad hoc (whenever stopped)
> - **Primary link key:** Unit # / VIN + driver + date

### Key fields to extract

| Field | What it is / why it matters |
|---|---|
| Inspection date & location | When and where the stop occurred. |
| Inspection level | Level I–VI (depth of the inspection). |
| Vehicle ID | Unit # / VIN of the truck (and trailer) inspected. |
| Driver | Driver involved. |
| Violations | Coded violations (vehicle and/or driver). |
| Out-of-service? | Whether the truck or driver was placed OOS. |
| Officer & report # | Issuing officer and DOT report number. |

### Why it matters for the system

- Safety/compliance history per truck and driver — feeds CSA score questions.
- Violations often trigger Repair Invoices (vehicle) — cross-document chain to the fix.

### Realistic messiness

- Violations are terse numeric codes needing a lookup to be human-readable.
- Both truck and trailer may be listed — link each violation to the right asset.
- Scanned officer copies, variable state formats.

**Sample operator questions**
- "Has truck 84 had any roadside violations this year?"
- "Were any of my trucks put out of service?"
- "Which driver has the most roadside violations?"

---

## Appendix A — Link-key quick map

How each document attaches to the fleet graph. Mismatched or missing keys are where entity resolution earns its keep.

| Document | Primary link key | Resolution risk |
|---|---|---|
| 2290 Form | VIN | No unit #; buried in fleet-wide Schedule 1 |
| Vehicle Registration | VIN + Plate | Unit # often missing |
| Repair Invoice | Unit # / VIN (fuzzy) | Handwritten, multi-truck, or absent |
| Fuel Receipt | Card # / Unit # | Card→truck map needed; state often blank |
| IFTA Return | Carrier (fleet) | Per-truck must be reconstructed |
| DOT Inspection | Unit # + VIN | Truck vs trailer ambiguity |
| Bill of Lading | Load # + truck | Truck/trailer field blank/handwritten |
| Rate Confirmation | Load # | Re-dispatch changes assigned truck |
| Proof of Delivery | Load / BOL # | Hard to distinguish from BOL |
| Medical Certificate | Driver | Name variants need resolution |
| ELD / HOS Log | Driver + truck + date | Driver uses multiple trucks/day |
| Roadside Inspection | Unit # / VIN + driver | Truck + trailer both listed |

---

## Appendix B — Cross-document chains

The questions judges love are the ones that force several documents to connect. Pre-build these chains:

- **Profitability per truck:** Rate Confirmation (revenue) − Fuel Receipts − Repair Invoices − Tolls = margin, grouped by truck.
- **Renew this truck's plates:** Registration (expiry + requirements) + current 2290 (prerequisite) + Insurance COI.
- **Load lifecycle / unbilled loads:** Rate Con (booked) → BOL (picked up) → POD (delivered) → flag delivered-but-not-invoiced.
- **IFTA reconciliation:** ELD miles per state + Fuel Receipts gallons per state → compare to filed IFTA Return.
- **Inspection → repair trail:** Failed DOT/Roadside inspection → matching Repair Invoice that fixed the defect.
- **Driver compliance:** Medical Certificate expiry + CDL + HOS violations, resolved across driver name variants.

---

## Design note: VIN is your spine

Most messiness resolves if every document can be traced back to a VIN, and the unit number is just a friendly alias layered on top. If you build your entity graph VIN-first, the "find the 2290 for truck 84" resolution falls out naturally.
