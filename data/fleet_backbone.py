"""
Fleet backbone — the single source of truth every document draws from.
Generating docs from shared entities means truck 4's VIN on its title MATCHES
truck 4's VIN on its 2290 form. That internal consistency is what lets the
agent cross-reference, and what makes the data credible to judges.
"""
import random, json, os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("en_US")
random.seed(7); Faker.seed(7)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CARRIER = {
    "name": "Lone Star Freight LLC",
    "dot": f"{random.randint(1000000, 3999999)}",
    "mc": f"MC-{random.randint(100000, 999999)}",
    "address": "4400 Sovereign Row, Dallas, TX 75247",
    "ein": f"{random.randint(10,99)}-{random.randint(1000000,9999999)}",
}

MAKES = [("Freightliner", "Cascadia"), ("Peterbilt", "579"), ("Kenworth", "T680"),
         ("Volvo", "VNL 760"), ("International", "LT625"), ("Mack", "Anthem")]
STATES = ["TX", "OK", "AR", "LA", "NM"]

def _vin():
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    return "1" + "".join(random.choice(chars) for _ in range(16))

def _plate(state):
    return f"{state}-{random.choice('ABCDEFGHJKLMNP')}{random.randint(10,99)}{random.randint(1000,9999)}"

REG_STATES = ["TX", "CA", "FL", "IL", "GA"]  # states we have real reg/title forms for

def build_fleet(n_trucks=12):
    trucks, drivers, trailers = [], [], []
    for i in range(1, n_trucks + 1):
        mk, md = random.choice(MAKES)
        st = random.choice(REG_STATES)
        year = random.randint(2017, 2024)
        dob = fake.date_of_birth(minimum_age=25, maximum_age=63)
        drv = {
            "driver_id": i,
            "name": fake.name(),
            "first": fake.first_name(), "last": fake.last_name(),
            "cdl": f"{random.choice('TX CA FL IL GA'.split())}{random.randint(10000000,99999999)}",
            "cdl_state": st,
            "phone": fake.phone_number(),
            "dob": dob,
            "address": fake.street_address(), "city": fake.city(), "state": st, "zip": fake.zipcode(),
            "med_cert_expires": (datetime.now() + timedelta(days=random.randint(-40, 400))),
            "med_exam_date": None,  # set below
            "med_examiner": f"Dr. {fake.last_name()}",
            "med_reg_num": random.randint(100000, 9999999),
            "restrictions": random.choice(["None","Corrective lenses","Wear hearing aid","None","None"]),
            "hire_date": fake.date_between("-6y", "-2m"),
        }
        drv["med_exam_date"] = drv["med_cert_expires"] - timedelta(days=random.choice([365,730]))
        trl = {
            "trailer_id": f"TRL-{200+i}",
            "type": random.choice(["Dry Van 53'","Reefer 53'","Flatbed 48'","Step Deck"]),
            "plate": _plate(st), "vin": _vin(), "year": random.randint(2015, 2024),
        }
        truck = {
            "truck_id": i, "unit": f"{random.randint(100,899)}",
            "make": mk, "model": md, "year": year,
            "vin": _vin(), "plate": _plate(st), "state": st,
            "driver_id": i, "driver_name": drv["name"],
            "trailer_id": trl["trailer_id"],
            "status": random.choice(["active","active","active","active","maintenance","idle"]),
            "odometer": random.randint(120_000, 780_000),
            "reg_expires": (datetime.now() + timedelta(days=random.randint(-25, 330))),
            "gvw": random.choice([80000, 80000, 80000, 76000]),
            "gross_wt_cat": "V",
            "fuel": "Diesel",
            "color": random.choice(["White","Red","Blue","Black","Silver"]),
            "lienholder": random.choice(["NONE","First Capital Bank","Daimler Truck Financial","NONE","Ryder Lease"]),
        }
        trucks.append(truck); drivers.append(drv); trailers.append(trl)
    return trucks, drivers, trailers

def build_loads(trucks, n=40):
    """Loads tie BOL / Rate Con / POD together — same load_id across the 3 docs."""
    cities = [("Dallas","TX"),("Houston","TX"),("Memphis","TN"),("Atlanta","GA"),
              ("Oklahoma City","OK"),("Little Rock","AR"),("Phoenix","AZ"),
              ("Kansas City","MO"),("Laredo","TX"),("El Paso","TX")]
    loads = []
    for i in range(1, n + 1):
        o = random.choice(cities); d = random.choice([c for c in cities if c != o])
        miles = random.randint(180, 1400)
        rate = round(miles * random.uniform(1.8, 3.4), 2)
        tk = random.choice(trucks)
        loads.append({
            "load_id": f"LSF-{10000 + i}",
            "truck_id": tk["truck_id"], "driver_name": tk["driver_name"],
            "origin": f"{o[0]}, {o[1]}", "dest": f"{d[0]}, {d[1]}",
            "miles": miles, "rate": rate,
            "broker": random.choice(["TQL","Coyote","Echo Global","RXO","Arrive Logistics"]),
            "commodity": random.choice(["Palletized dry goods","Frozen poultry","Auto parts",
                                        "Building materials","Packaged food","Electronics"]),
            "weight": random.randint(8000, 44000),
            "ship_date": fake.date_between("-90d", "-1d"),
        })
    return loads

if __name__ == "__main__":
    trucks, drivers, trailers = build_fleet()
    loads = build_loads(trucks)
    print(f"Carrier: {CARRIER['name']}  DOT {CARRIER['dot']}  EIN {CARRIER['ein']}")
    print(f"Trucks: {len(trucks)} | Drivers: {len(drivers)} | Trailers: {len(trailers)} | Loads: {len(loads)}")
    print(f"Sample truck: unit {trucks[0]['unit']} {trucks[0]['year']} {trucks[0]['make']} VIN {trucks[0]['vin']} reg {trucks[0]['state']}")
