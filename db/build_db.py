"""
Build the structured fleet database from data/fleet_structured.json.

Creates db/fleet.db with tables:
  trucks, drivers, trailers, loads, expenses, registrations
Expenses are derived from the documents (fuel receipts, repair invoices) so the
SQL side and the document side describe the SAME fleet — consistency that lets
hybrid questions join across both.

Run:  python db/build_db.py
"""
import os, json, sqlite3, random
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "fleet.db")
STRUCT = os.path.join(ROOT, "data", "fleet_structured.json")
MANIFEST = os.path.join(ROOT, "data", "manifest.json")

random.seed(7)

def build():
    with open(STRUCT) as f:
        s = json.load(f)
    trucks, drivers, trailers, loads = s["trucks"], s["drivers"], s["trailers"], s["loads"]

    if os.path.exists(DB): os.remove(DB)
    con = sqlite3.connect(DB); c = con.cursor()
    c.executescript("""
    CREATE TABLE trucks (truck_id INTEGER PRIMARY KEY, unit TEXT, make TEXT, model TEXT,
        year INTEGER, vin TEXT, plate TEXT, state TEXT, driver_id INTEGER, trailer_id TEXT,
        status TEXT, odometer INTEGER, reg_expires TEXT, gvw INTEGER, fuel TEXT,
        color TEXT, lienholder TEXT);
    CREATE TABLE drivers (driver_id INTEGER PRIMARY KEY, name TEXT, cdl TEXT, cdl_state TEXT,
        phone TEXT, dob TEXT, med_cert_expires TEXT, hire_date TEXT);
    CREATE TABLE trailers (trailer_id TEXT PRIMARY KEY, type TEXT, plate TEXT, vin TEXT, year INTEGER);
    CREATE TABLE loads (load_id TEXT PRIMARY KEY, truck_id INTEGER, driver_name TEXT,
        origin TEXT, dest TEXT, miles INTEGER, rate REAL, broker TEXT, commodity TEXT,
        weight INTEGER, ship_date TEXT);
    CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, truck_id INTEGER,
        category TEXT, vendor TEXT, amount REAL, date TEXT, source_doc TEXT);
    CREATE TABLE registrations (truck_id INTEGER, plate TEXT, expires TEXT, state TEXT);
    """)

    for t in trucks:
        c.execute("""INSERT INTO trucks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (t["truck_id"], t["unit"], t["make"], t["model"], t["year"], t["vin"], t["plate"],
             t["state"], t["driver_id"], t["trailer_id"], t["status"], t["odometer"],
             str(t["reg_expires"]), t["gvw"], t["fuel"], t["color"], t["lienholder"]))
        c.execute("INSERT INTO registrations VALUES (?,?,?,?)",
            (t["truck_id"], t["plate"], str(t["reg_expires"]), t["state"]))
    for d in drivers:
        c.execute("INSERT INTO drivers VALUES (?,?,?,?,?,?,?,?)",
            (d["driver_id"], d["name"], d["cdl"], d["cdl_state"], d["phone"],
             str(d["dob"]), str(d["med_cert_expires"]), str(d["hire_date"])))
    for tr in trailers:
        c.execute("INSERT INTO trailers VALUES (?,?,?,?,?)",
            (tr["trailer_id"], tr["type"], tr["plate"], tr["vin"], tr["year"]))
    for l in loads:
        c.execute("INSERT INTO loads VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (l["load_id"], l["truck_id"], l["driver_name"], l["origin"], l["dest"],
             l["miles"], l["rate"], l["broker"], l["commodity"], l["weight"], str(l["ship_date"])))

    # Derive expenses from the documents so DB <-> docs agree.
    with open(MANIFEST) as f:
        docs = json.load(f)["documents"]
    cat_map = {"fuel_receipt": "fuel", "repair_invoice": ("parts" , "maintenance")}
    for d in docs:
        tid = d.get("truck_id")
        if tid in (None, -1): continue
        if d["doc_type"] == "fuel_receipt":
            amt = round(random.uniform(180, 720), 2)
            c.execute("INSERT INTO expenses (truck_id,category,vendor,amount,date,source_doc) VALUES (?,?,?,?,?,?)",
                (tid, "fuel", "Fuel vendor", amt,
                 (datetime.now()-timedelta(days=random.randint(0,90))).strftime("%Y-%m-%d"), d["file"]))
        elif d["doc_type"] == "repair_invoice":
            amt = round(random.uniform(300, 2800), 2)
            cat = random.choice(["parts", "maintenance", "tires"])
            c.execute("INSERT INTO expenses (truck_id,category,vendor,amount,date,source_doc) VALUES (?,?,?,?,?,?)",
                (tid, cat, "Repair shop", amt,
                 (datetime.now()-timedelta(days=random.randint(0,120))).strftime("%Y-%m-%d"), d["file"]))
        elif d["doc_type"] == "roadside_inspection":
            if random.random() < 0.3:
                c.execute("INSERT INTO expenses (truck_id,category,vendor,amount,date,source_doc) VALUES (?,?,?,?,?,?)",
                    (tid, "fines", "DOT", round(random.uniform(150, 900), 2),
                     (datetime.now()-timedelta(days=random.randint(0,150))).strftime("%Y-%m-%d"), d["file"]))

    con.commit()
    # quick stats
    stats = {tbl: c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
             for tbl in ["trucks","drivers","trailers","loads","expenses","registrations"]}
    con.close()
    print("Built", DB)
    for k,v in stats.items(): print(f"  {k:14s} {v}")

if __name__ == "__main__":
    build()
