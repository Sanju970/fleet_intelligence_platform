"""
Authentic-layout PDF renderers — each mirrors the structure of the REAL form
template provided (Form 2290, IFTA-100, BOL, ELD log grid, MCSA medical, DVIR).
Draw from the shared backbone for internal consistency.
"""
import random
from datetime import datetime, timedelta
from reportlab.lib.units import inch
from reportlab.lib import colors

DATE_FMTS = ["%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y", "%d-%b-%y", "%m-%d-%y"]
def fdate(dt, jitter=True):
    if isinstance(dt, str): return dt
    return dt.strftime(random.choice(DATE_FMTS) if jitter else "%m/%d/%Y")

def _box(c, x, y, w, h): c.rect(x*inch, y*inch, w*inch, h*inch, stroke=1, fill=0)
def _t(c, x, y, s, size=8, bold=False, gray=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    if gray: c.setFillColor(colors.grey)
    c.drawString(x*inch, y*inch, str(s))
    if gray: c.setFillColor(colors.black)
def _lv(c, x, y, label, val):
    c.setFont("Helvetica", 6); c.setFillColor(colors.grey)
    c.drawString(x*inch, (y+0.12)*inch, label); c.setFillColor(colors.black)
    c.setFont("Helvetica", 9); c.drawString(x*inch, y*inch, str(val))

def form_2290(c, carrier, truck):
    _t(c,1,10.5,"Form 2290 (Rev. July 2026)",13,bold=True)
    _t(c,1,10.3,"Heavy Highway Vehicle Use Tax Return",9)
    _t(c,5.6,10.5,"OMB No. 1545-0143",8)
    _t(c,1,10.05,"Department of the Treasury - Internal Revenue Service",7,gray=True)
    _t(c,1,9.85,"For the period July 1, 2026, through June 30, 2027",8)
    c.line(1*inch,9.75*inch,7.5*inch,9.75*inch)
    _lv(c,1,9.4,"Name",carrier["name"]); _lv(c,5,9.4,"Employer ID Number (EIN)",carrier["ein"])
    _lv(c,1,9.05,"Number, street, room/suite",carrier["address"])
    _t(c,1,8.7,"Part I  Figuring the Tax",9,bold=True)
    _lv(c,1,8.35,"1  Month of first use (YYYYMM)","202607")
    _lv(c,1,8.0,"2  Tax (from page 2, col. 4)","550.00")
    _lv(c,1,7.65,"4  Total tax","550.00")
    _lv(c,1,7.3,"6  Balance due (paid via EFTPS)","550.00")
    _t(c,1,6.8,"Schedule 1 - Vehicles Reported (VIN / Category)",9,bold=True)
    _box(c,1,6.3,6.5,0.4); _t(c,1.1,6.45,f"1.  VIN: {truck['vin']}",9)
    _t(c,5.6,6.45,f"Category: {truck['gross_wt_cat']} (over 75,000 lbs)",8)
    _t(c,1,6.0,f"Unit #: {truck['unit']}    Taxable gross weight: {truck['gvw']:,} lbs",8)
    _t(c,1,5.7,"STATUS: PAID - Schedule 1 stamped (proof of payment for registration)",8,bold=True)
    _t(c,1,1.0,"For Privacy Act and Paperwork Reduction Act Notice, see instructions. Cat. No. 11250O",6,gray=True)

def vehicle_registration(c, carrier, truck):
    titles={"TX":"TEXAS","CA":"CALIFORNIA","FL":"FLORIDA","IL":"ILLINOIS","GA":"GEORGIA"}
    _t(c,1,10.5,f"STATE OF {titles.get(truck['state'],'TEXAS')}",14,bold=True)
    _t(c,1,10.28,"Apportioned Cab Card - IRP Registration (Commercial)",9)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    _lv(c,1,9.8,"Registrant",carrier["name"]); _lv(c,5.2,9.8,"Account No.",f"{truck['state']}{random.randint(100000,999999)}")
    _lv(c,1,9.45,"Plate Number",truck["plate"]); _lv(c,3,9.45,"Unit Number",truck["unit"]); _lv(c,5.2,9.45,"VIN",truck["vin"])
    _lv(c,1,9.1,"Make / Model",f"{truck['make']} {truck['model']}"); _lv(c,3,9.1,"Year",truck["year"]); _lv(c,5.2,9.1,"Color",truck["color"])
    _lv(c,1,8.75,"Registered Gross Weight",f"{truck['gvw']:,} lbs"); _lv(c,3,8.75,"Fuel",truck["fuel"])
    _lv(c,1,8.4,"Effective",fdate(datetime.now()-timedelta(days=random.randint(30,300)))); _lv(c,3,8.4,"Expires",fdate(truck["reg_expires"]))
    _lv(c,1,8.05,"Apportioned Jurisdictions","TX CA FL IL GA OK AR LA NM")
    _t(c,1,7.6,"Carry this cab card in the vehicle at all times.",7,gray=True)

def vehicle_title(c, carrier, truck):
    titles={"TX":"TEXAS","CA":"CALIFORNIA","FL":"FLORIDA","IL":"ILLINOIS","GA":"GEORGIA"}
    has_lien = truck["lienholder"] != "NONE"
    _t(c,1,10.5,f"STATE OF {titles.get(truck['state'],'TEXAS')}",14,bold=True)
    _t(c,1,10.28,"CERTIFICATE OF TITLE - MOTOR VEHICLE",11,bold=True)
    _t(c,5.4,10.5,f"Title No. {truck['state']}{random.randint(10**8,10**9-1)}",8)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    _lv(c,1,9.8,"Vehicle Identification Number (VIN)",truck["vin"]); _lv(c,5.2,9.8,"Year",truck["year"])
    _lv(c,1,9.45,"Make",truck["make"]); _lv(c,3,9.45,"Model",truck["model"]); _lv(c,5.2,9.45,"Body Style","Truck-Tractor")
    _lv(c,1,9.1,"Odometer (mi)",f"{truck['odometer']:,}"); _lv(c,3,9.1,"Gross Weight",f"{truck['gvw']:,} lbs"); _lv(c,5.2,9.1,"Fuel",truck["fuel"])
    _lv(c,1,8.75,"License Plate",truck["plate"]); _lv(c,3,8.75,"Unit #",truck["unit"]); _lv(c,5.2,8.75,"Color",truck["color"])
    c.line(1*inch,8.55*inch,7.5*inch,8.55*inch)
    _t(c,1,8.35,"REGISTERED OWNER",9,bold=True)
    _lv(c,1,8.0,"Owner",carrier["name"]); _lv(c,1,7.65,"Address",carrier["address"])
    c.line(1*inch,7.45*inch,7.5*inch,7.45*inch)
    _t(c,1,7.25,"LIENHOLDER / SECURED PARTY",9,bold=True)
    if has_lien:
        _lv(c,1,6.9,"Lienholder",truck["lienholder"]); _lv(c,5.2,6.9,"Lien Date",fdate(datetime.now()-timedelta(days=random.randint(200,1400))))
        _t(c,1,6.55,"STATUS: LIEN ON RECORD - title held by secured party until released.",8,bold=True)
    else:
        _lv(c,1,6.9,"Lienholder","NONE - NO LIEN ON RECORD")
        _t(c,1,6.55,"STATUS: CLEAR TITLE - owned free and clear, no secured party.",8,bold=True)
    _t(c,1,1.0,"This certifies title to the vehicle described above. Reproductions are not valid.",6,gray=True)

def repair_invoice(c, carrier, truck):
    shop=random.choice(["Rush Truck Center","TA Truck Service","Bob's Diesel & Truck Repair","Midwest Fleet Service","Lone Star Diesel Repair"])
    _t(c,1,10.5,shop,15,bold=True)
    _t(c,1,10.28,f"{random.choice(['1450 Industrial Blvd','88 Frontage Rd','I-35 Service Rd'])}, {truck['state']}",8,gray=True)
    _t(c,5.6,10.5,"TRUCK REPAIR INVOICE",11,bold=True)
    c.line(1*inch,10.1*inch,7.5*inch,10.1*inch)
    inv=f"INV-{random.randint(40000,99999)}"
    _lv(c,1,9.7,"Invoice #",inv); _lv(c,3,9.7,"Date",fdate(datetime.now()-timedelta(days=random.randint(1,200)))); _lv(c,5,9.7,"P.O. #",random.randint(1000,9999))
    _lv(c,1,9.3,"Unit #",truck["unit"]); _lv(c,3,9.3,"VIN",truck["vin"]); _lv(c,5,9.3,"Odometer",f"{truck['odometer']+random.randint(0,9000):,}")
    _lv(c,1,8.95,"Plate",truck["plate"]); _lv(c,3,8.95,"Customer",carrier["name"])
    c.line(1*inch,8.7*inch,7.5*inch,8.7*inch)
    _t(c,1,8.55,"DESCRIPTION",8,bold=True); _t(c,5.0,8.55,"QTY",8,bold=True); _t(c,5.6,8.55,"RATE",8,bold=True); _t(c,6.7,8.55,"AMOUNT",8,bold=True)
    c.line(1*inch,8.45*inch,7.5*inch,8.45*inch)
    items=random.sample([("Brake pads - drive axle",1,480),("DOT annual inspection labor",1,120),("Oil & filter service",1,310),
        ("Steer tire replacement",2,920),("Air dryer cartridge",1,215),("DPF cleaning",1,640),("Alternator R&R",1,530),
        ("Wheel seal - drive",1,180),("Coolant flush",1,160),("Diagnostic - check engine",1,140)],k=random.randint(2,5))
    y=8.25; sub=0
    for desc,qty,rate in items:
        amt=(rate+random.randint(-30,80))*qty; sub+=amt
        c.setFont("Helvetica",8); c.drawString(1*inch,y*inch,desc); c.drawString(5.0*inch,y*inch,str(qty))
        c.drawString(5.6*inch,y*inch,f"${rate}"); c.drawRightString(7.45*inch,y*inch,f"${amt}.00"); y-=0.26
    tax=round(sub*0.0825); total=sub+tax
    c.line(5*inch,(y-0.05)*inch,7.5*inch,(y-0.05)*inch)
    _t(c,5,y-0.25,"Subtotal",8); c.drawRightString(7.45*inch,(y-0.25)*inch,f"${sub}.00")
    _t(c,5,y-0.45,"Tax (8.25%)",8); c.drawRightString(7.45*inch,(y-0.45)*inch,f"${tax}.00")
    _t(c,5,y-0.7,"TOTAL DUE",11,bold=True); c.setFont("Helvetica-Bold",11); c.drawRightString(7.45*inch,(y-0.7)*inch,f"${total}.00")

def fuel_receipt(c, carrier, truck, driver=None):
    chain=random.choice(["QUICKFUEL DELIVERY CO.","PILOT FLYING J","LOVE'S TRAVEL STOP","TA PETRO"])
    cx=3.75
    def ctr(y,s,size=9,bold=False):
        c.setFont("Courier-Bold" if bold else "Courier",size); c.drawCentredString(cx*inch,y*inch,s)
    ctr(10.4,chain,11,True); ctr(10.15,f"{random.randint(1000,9999)} Depot Ave")
    ctr(9.98,f"{random.choice(['Tulsa, OK','Dallas, TX','Ardmore, OK'])} {random.randint(70000,79999)}")
    ctr(9.81,f"Phone: (555) {random.randint(200,999)}-{random.randint(1000,9999)}"); ctr(9.64,f"DOT#: QF-{random.randint(1000,9999)}")
    ctr(9.4,"*"*38); ctr(9.15,fdate(datetime.now()-timedelta(days=random.randint(0,90)))+f"  {random.randint(0,23):02d}:{random.randint(10,59)}"); ctr(8.9,"*"*38)
    drv=driver["name"] if driver else "R. Collins"
    gal=random.randint(45,168); ppg=round(random.uniform(3.39,4.69),3)
    c.setFont("Courier",9)
    c.drawString(1.3*inch,8.55*inch,f"Customer: {carrier['name'][:18]}")
    c.drawString(1.3*inch,8.38*inch,f"Receipt #: FD-{random.randint(100000,999999)}")
    c.drawString(1.3*inch,8.21*inch,f"Unit: {truck['unit']}   Driver: {drv[:16]}")
    ctr(7.95,"*"*38)
    c.drawString(1.3*inch,7.7*inch,f"{gal}x Diesel (gal)"); c.drawRightString(6.2*inch,7.7*inch,f"${round(gal*ppg)}")
    c.drawString(1.3*inch,7.53*inch,"Pump Fee"); c.drawRightString(6.2*inch,7.53*inch,"$25")
    ctr(7.3,"*"*38); total=round(gal*ppg)+25
    c.drawString(2.6*inch,7.05*inch,"Subtotal:"); c.drawRightString(6.2*inch,7.05*inch,f"${total-25}")
    c.drawString(2.6*inch,6.88*inch,"Tax:"); c.drawRightString(6.2*inch,6.88*inch,"$0")
    c.setFont("Courier-Bold",10); c.drawString(2.6*inch,6.68*inch,"Total:"); c.drawRightString(6.2*inch,6.68*inch,f"${total}")
    ctr(6.4,"*"*38); c.setFont("Courier",9)
    c.drawString(1.3*inch,6.15*inch,f"Card:   ************{random.randint(1000,9999)}")
    c.drawString(1.3*inch,5.98*inch,"Type:   VISA   Entry: CONTACTLESS")
    c.drawString(1.3*inch,5.81*inch,"Status: APPROVED")
    ctr(5.5,"Keep away from heat and open flame."); ctr(5.35,"Thank you for your business.")

def ifta_return(c, carrier, truck):
    forms={"TX":"Form 56-101 (Texas)","CA":"IFTA-100-MN (California)","FL":"HSMV 85921 (Florida)","IL":"MFUT-15 (Illinois)","GA":"IFTA-100 (Georgia)"}
    q=random.choice(["Q1","Q2","Q3","Q4"]); yr=random.choice([2024,2025])
    _t(c,1,10.5,"IFTA Quarterly Fuel Use Tax Return",13,bold=True); _t(c,1,10.28,forms.get(truck["state"],"IFTA-100"),9); _t(c,5.6,10.5,f"{q} {yr}",11,bold=True)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    _lv(c,1,9.8,"Licensee",carrier["name"]); _lv(c,5,9.8,"IFTA Account No.",f"{truck['state']}{random.randint(1000000,9999999)}")
    _lv(c,1,9.45,"FEI / EIN",carrier["ein"]); _lv(c,5,9.45,"Fuel Type","Diesel")
    avg=round(random.uniform(5.8,7.2),2)
    _lv(c,1,9.1,"Total Miles (all juris.)",f"{random.randint(18000,52000):,}"); _lv(c,3,9.1,"Total Gallons",f"{random.randint(3000,8000):,}"); _lv(c,5,9.1,"Avg Fleet MPG",avg)
    c.line(1*inch,8.85*inch,7.5*inch,8.85*inch)
    for i,h in enumerate(["Juris","Total Miles","Taxable Gal","Tax-Paid Gal","Net Gal","Rate","Tax Due"]): _t(c,1+i*0.92,8.7,h,7,bold=True)
    c.line(1*inch,8.6*inch,7.5*inch,8.6*inch)
    y=8.42; net=0; rates={"TX":.20,"CA":.445,"FL":.3307,"IL":.43,"GA":.184,"OK":.13,"AR":.225,"LA":.20,"NM":.21}
    for j in random.sample(list(rates),6):
        mi=random.randint(1500,12000); tg=round(mi/avg); tp=round(tg*random.uniform(.6,1.1)); ng=tg-tp; tax=round(ng*rates[j],2); net+=tax
        c.setFont("Helvetica",7)
        for k,v in enumerate([j,f"{mi:,}",tg,tp,ng,rates[j],f"${tax}"]): c.drawString((1+k*0.92)*inch,y*inch,str(v))
        y-=0.22
    c.line(1*inch,(y-0.05)*inch,7.5*inch,(y-0.05)*inch)
    _t(c,1,y-0.3,f"NET TAX DUE (Col. Q total): ${round(net,2)}",10,bold=True)
    _t(c,1,y-0.6,"Penalty: $50.00 or 10% of delinquent tax, whichever is greater, if filed late.",7,gray=True)

def dot_inspection(c, carrier, truck):
    _t(c,1,10.5,"Annual Vehicle Inspection Report",13,bold=True); _t(c,1,10.28,"Periodic Inspection per 49 CFR 396.17",8)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    _lv(c,1,9.8,"Carrier",carrier["name"]); _lv(c,5,9.8,"DOT #",carrier["dot"])
    _lv(c,1,9.45,"Unit / Tractor No.",truck["unit"]); _lv(c,3,9.45,"VIN",truck["vin"]); _lv(c,5,9.45,"Plate",truck["plate"])
    _lv(c,1,9.1,"Inspection Date",fdate(datetime.now()-timedelta(days=random.randint(5,360)))); _lv(c,3,9.1,"Inspector",random.choice(["J. Hale","M. Cruz","D. Webb"])); _lv(c,5,9.1,"Cert #",random.randint(1000,9999))
    _t(c,1,8.7,"Vehicle Components Inspected  (OK / NEEDS REPAIR / NA)",9,bold=True)
    comps=["1. Brake System","2. Coupling Devices","3. Exhaust System","4. Fuel System","5. Lighting Devices","6. Safe Loading","7. Steering Mechanism","8. Suspension","9. Frame","10. Tires","11. Wheels and Rims","12. Windshield Glazing","13. Windshield Wipers"]
    passed=random.random()>0.18; y=8.45
    for i,comp in enumerate(comps):
        col=1+(i%2)*3.5; mark="OK" if (passed or random.random()>0.3) else "NEEDS REPAIR"
        c.setFont("Helvetica",8); c.drawString(col*inch,y*inch,comp); c.drawString((col+2.6)*inch,y*inch,mark)
        if i%2==1: y-=0.26
    if len(comps)%2==1: y-=0.26
    c.setFont("Helvetica-Bold",11); c.setFillColor(colors.black if passed else colors.red)
    c.drawString(1*inch,(y-0.2)*inch,"CERTIFICATION: PASS - meets all inspection items" if passed else "RESULT: FAIL - defects must be corrected")
    c.setFillColor(colors.black)

def bill_of_lading(c, carrier, load, trucks_by_id):
    _t(c,3.0,10.5,"BILL OF LADING",15,bold=True); _t(c,5.8,10.5,"Date: "+fdate(load["ship_date"],False),9); _t(c,5.8,10.32,f"BOL No: {load['load_id']}",9,bold=True)
    c.line(1*inch,10.1*inch,7.5*inch,10.1*inch)
    _t(c,1,9.85,"SHIP FROM",8,bold=True); _t(c,1,9.68,load["origin"],9); _t(c,1,9.5,f"SID #: {random.randint(10000,99999)}",7,gray=True)
    _t(c,4.2,9.85,"SHIP TO",8,bold=True); _t(c,4.2,9.68,load["dest"],9); _t(c,4.2,9.5,f"CID #: {random.randint(10000,99999)}",7,gray=True)
    c.line(1*inch,9.4*inch,7.5*inch,9.4*inch)
    _lv(c,1,9.05,"Carrier Name",carrier["name"]); _lv(c,4.2,9.05,"SCAC",random.choice(["LSFR","TQLA","RXOL"]))
    _lv(c,1,8.7,"Trailer No.",trucks_by_id[load["truck_id"]]["trailer_id"]); _lv(c,3,8.7,"Seal No(s).",random.randint(4000,4999)); _lv(c,4.2,8.7,"Pro No.",load["load_id"]); _lv(c,6,8.7,"Freight Terms","Prepaid")
    c.line(1*inch,8.45*inch,7.5*inch,8.45*inch)
    _t(c,1,8.25,"CARRIER INFORMATION",8,bold=True)
    _t(c,1,8.05,"Handling Unit | Package | Weight | H.M. | Commodity Description",7,bold=True)
    c.line(1*inch,7.95*inch,7.5*inch,7.95*inch)
    _t(c,1,7.75,f"{random.randint(8,26)} PLT   {random.randint(8,26)} CTN   {load['weight']:,} lbs        {load['commodity']}",8)
    _t(c,1,7.45,f"NMFC Class: {random.choice([50,70,85,100])}",7,gray=True)
    _lv(c,1,7.0,"Unit / Driver",f"{load['truck_id']} / {load['driver_name']}")
    _t(c,1,6.5,"RECEIVED, subject to the classifications and lawfully filed tariffs in effect on the date of issue.",7,gray=True)
    _t(c,1,6.0,"Shipper Signature ____________  Carrier Signature ____________  Driver ____________",7)

def rate_confirmation(c, carrier, load):
    _t(c,1,10.5,f"{load['broker']}",14,bold=True); _t(c,5.4,10.5,"RATE CONFIRMATION",12,bold=True); _t(c,5.4,10.3,f"RC #: {load['load_id']}",9)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    _lv(c,1,9.8,"Load #",load["load_id"]); _lv(c,3,9.8,"Date",fdate(load["ship_date"],False)); _lv(c,5,9.8,"Terms","Net 30 Days")
    _lv(c,1,9.45,"Carrier",carrier["name"]); _lv(c,5,9.45,"MC #",carrier["mc"])
    _lv(c,1,9.1,"Equipment",random.choice(["Dry Van 53'","Reefer 53'","Flatbed"])); _lv(c,3,9.1,"Driver",load["driver_name"]); _lv(c,5,9.1,"Truck Unit",load["truck_id"])
    c.line(1*inch,8.9*inch,7.5*inch,8.9*inch)
    _t(c,1,8.7,"SHIPPER (Origin)",8,bold=True); _t(c,1,8.52,load["origin"],9); _t(c,1,8.35,"Pickup: "+fdate(load["ship_date"],False),8)
    _t(c,4.2,8.7,"CONSIGNEE (Destination)",8,bold=True); _t(c,4.2,8.52,load["dest"],9); _t(c,4.2,8.35,"Delivery: "+fdate(load["ship_date"]+timedelta(days=2),False),8)
    c.line(1*inch,8.15*inch,7.5*inch,8.15*inch)
    _t(c,1,7.9,"Description           Type      Weight (lbs)   Qty   HazMat",7,bold=True)
    _t(c,1,7.7,f"{load['commodity'][:20]:20s}  Palletized  {load['weight']:,}        {random.randint(8,26)}     No",8)
    c.line(1*inch,7.5*inch,7.5*inch,7.5*inch)
    _t(c,1,7.25,"RATE SUMMARY",8,bold=True); _t(c,1,7.05,"Linehaul",9); c.drawRightString(7.45*inch,7.05*inch,f"${load['rate']:,.2f}")
    _t(c,1,6.85,"Miles: "+str(load["miles"]),8,gray=True)
    c.setFont("Helvetica-Bold",12); c.drawString(1*inch,6.5*inch,"TOTAL TO CARRIER"); c.drawRightString(7.45*inch,6.5*inch,f"${load['rate']:,.2f}")
    _t(c,1,6.0,"Detention $50/hr after 2 hrs. Accessorials require prior authorization code.",7,gray=True)
    _t(c,1,5.6,"Carrier Signature ____________________   Date ____________",8)

def proof_of_delivery(c, carrier, load, hf):
    _t(c,3.1,10.5,"Proof of Delivery",16,bold=True); c.line(1*inch,10.2*inch,7.5*inch,10.2*inch)
    _lv(c,1,9.85,"Company Name",carrier["name"]); _lv(c,5,9.85,"Date",fdate(load["ship_date"]+timedelta(days=random.randint(1,3)),False))
    _lv(c,1,9.5,"Phone Number",f"(214) {random.randint(200,999)}-{random.randint(1000,9999)}"); _lv(c,5,9.5,"Order Number",load["load_id"])
    _lv(c,1,9.15,"Address",carrier["address"])
    c.line(1*inch,8.95*inch,7.5*inch,8.95*inch)
    _t(c,1,8.7,"Delivered to:",9,bold=True); _t(c,4.2,8.7,"Billing Details:",9,bold=True)
    _t(c,1,8.5,"Name: "+load["dest"].split(",")[0]+" Distribution",8); _t(c,4.2,8.5,"Name: "+load["broker"],8)
    _t(c,1,8.3,"Address: "+load["dest"],8)
    c.line(1*inch,8.1*inch,7.5*inch,8.1*inch)
    _t(c,1,7.85,"Order Details:",9,bold=True); _t(c,1,7.6,"Description                          Qty Ordered   Qty Delivered   Price",7,bold=True)
    c.line(1*inch,7.5*inch,7.5*inch,7.5*inch)
    qo=random.randint(10,26); qd=qo-random.choice([0,0,0,2])
    _t(c,1,7.3,f"{load['commodity'][:28]:28s}   {qo}              {qd}             ${load['rate']:,.0f}",8)
    c.line(1*inch,6.9*inch,7.5*inch,6.9*inch)
    _t(c,1,6.6,"I acknowledge receipt of the above items in good condition.",8)
    _t(c,1,6.2,"Recipient's Signature:",9,bold=True)
    try: c.setFont(hf,20)
    except Exception: c.setFont("Helvetica-Oblique",15)
    c.drawString(2.7*inch,6.18*inch,random.choice(["R. Martinez","T. Owens","J. Lee","K. Patel"]))
    _t(c,1,5.8,"Date & Time:",9,bold=True); _t(c,2.7,5.8,fdate(load["ship_date"]+timedelta(days=2),False)+f"  {random.randint(7,18)}:{random.randint(10,59)}",9)
    _t(c,1,5.4,"Driver: "+load["driver_name"],8,gray=True)

def medical_cert(c, carrier, driver):
    _t(c,1,10.5,"Medical Examiner's Certificate",13,bold=True); _t(c,1,10.3,"Form MCSA-5876 - FMCSA, 49 CFR 391.43",8); _t(c,5.4,10.5,"OMB No. 2126-0006",8)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    _t(c,1,9.85,"SECTION 1. Driver Information",9,bold=True)
    _lv(c,1,9.5,"Last Name",driver["last"]); _lv(c,3,9.5,"First Name",driver["first"]); _lv(c,5,9.5,"DOB",fdate(driver["dob"],False))
    _lv(c,1,9.15,"Driver's License No.",driver["cdl"]); _lv(c,3.5,9.15,"Issuing State",driver["cdl_state"]); _lv(c,5,9.15,"CLP/CDL Holder","Yes")
    _lv(c,1,8.8,"Address",f"{driver['address']}, {driver['city']}, {driver['state']} {driver['zip']}")
    c.line(1*inch,8.6*inch,7.5*inch,8.6*inch)
    _t(c,1,8.35,"SECTION 2. Certification (medical examiner)",9,bold=True)
    _lv(c,1,8.0,"Exam Date",fdate(driver["med_exam_date"],False)); _lv(c,3,8.0,"Expiration Date",fdate(driver["med_cert_expires"],False))
    _lv(c,1,7.65,"Medical Examiner",driver["med_examiner"]); _lv(c,3.5,7.65,"National Registry No.",driver["med_reg_num"])
    _lv(c,1,7.3,"Restrictions",driver["restrictions"])
    _t(c,1,6.9,"The driver is medically certified to operate a commercial motor vehicle.",8)
    _t(c,1,6.5,"Driver must carry this certificate while operating a CMV. Sensitive - for official use only.",7,gray=True)

def eld_log(c, carrier, truck, driver):
    _t(c,1,10.5,"Driver's Daily Log (24 Hours)",13,bold=True); _t(c,1,10.3,"Electronic Logging Device - Hours of Service, 49 CFR 395",8)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    day=datetime.now()-timedelta(days=random.randint(1,40))
    _lv(c,1,9.8,"Driver",driver["name"]); _lv(c,3.5,9.8,"Date",fdate(day,False)); _lv(c,5.5,9.8,"Co-Driver","None")
    _lv(c,1,9.45,"Tractor/Unit",truck["unit"]); _lv(c,3.5,9.45,"Plate",truck["plate"]); _lv(c,5.5,9.45,"Trailer",truck["trailer_id"])
    drive=random.randint(7,11); on=random.randint(1,3); sb=random.randint(0,2); off=24-drive-on-sb
    sodo=truck["odometer"]; eodo=sodo+random.randint(280,620)
    _lv(c,1,9.1,"Start Odometer",f"{sodo:,}"); _lv(c,3.5,9.1,"End Odometer",f"{eodo:,}"); _lv(c,5.5,9.1,"Distance",f"{eodo-sodo} mi")
    c.line(1*inch,8.85*inch,7.5*inch,8.85*inch)
    rows=[("1. Off Duty",off),("2. Sleeper Berth",sb),("3. Driving",drive),("4. On Duty (not driving)",on)]; y=8.65
    for label,hrs in rows:
        c.setFont("Helvetica",8); c.drawString(1*inch,y*inch,label)
        c.rect(3*inch,(y-0.02)*inch,4.3*inch,0.13*inch,stroke=1,fill=0)
        c.setFillColor(colors.lightgrey); c.rect(3*inch,(y-0.02)*inch,(4.3*(hrs/24.0))*inch,0.13*inch,stroke=0,fill=1); c.setFillColor(colors.black)
        c.drawRightString(7.45*inch,(y+0.18)*inch,f"{hrs} hr"); y-=0.32
    viol=drive>11
    c.setFont("Helvetica-Bold",10); c.setFillColor(colors.red if viol else colors.black)
    c.drawString(1*inch,(y-0.1)*inch,"HOS VIOLATION: 11-hour driving limit exceeded" if viol else "Compliant - no HOS violations"); c.setFillColor(colors.black)
    _t(c,1,y-0.5,f"Cycle: {random.randint(38,70)}/70 hrs (8-day)   Shipping Doc / BOL on file",7,gray=True)
    _t(c,1,y-0.85,"I certify these entries are true and correct: ____________________ (Driver signature)",8)

def roadside_inspection(c, carrier, truck, driver):
    _t(c,1,10.5,"Driver/Vehicle Examination Report",13,bold=True); _t(c,1,10.3,"FMCSA Roadside Inspection - Level "+random.choice(["I","II","III"]),8)
    c.line(1*inch,10.15*inch,7.5*inch,10.15*inch)
    _lv(c,1,9.8,"Report No.",f"{truck['state']}{random.randint(10**8,10**9)}"); _lv(c,4,9.8,"Date",fdate(datetime.now()-timedelta(days=random.randint(2,200)),False))
    _lv(c,1,9.45,"Carrier",carrier["name"]); _lv(c,5,9.45,"DOT #",carrier["dot"])
    _lv(c,1,9.1,"Driver",driver["name"]); _lv(c,4,9.1,"CDL",driver["cdl"])
    _lv(c,1,8.75,"Unit / VIN",f"{truck['unit']} / {truck['vin']}")
    _lv(c,1,8.4,"Location",f"I-{random.choice([20,30,35,40,45])} MM {random.randint(10,400)}, {truck['state']}")
    c.line(1*inch,8.2*inch,7.5*inch,8.2*inch)
    _t(c,1,7.95,"Violations",9,bold=True); has=random.random()>0.5
    if has:
        y=7.7
        for v in random.sample(["393.75 Tire tread depth below minimum","395.8(k) Log not current","393.9 Inoperative required lamp","396.3(a)(1) Brakes out of adjustment","391.41 Medical certificate expired","393.45 Brake hose chafing"],k=random.randint(1,3)):
            c.setFont("Helvetica",8); c.drawString(1.1*inch,y*inch,"- "+v); y-=0.24
        oos=random.random()>0.6
        c.setFont("Helvetica-Bold",10); c.setFillColor(colors.red if oos else colors.black)
        c.drawString(1*inch,(y-0.15)*inch,"OUT-OF-SERVICE ORDER ISSUED" if oos else "Violations noted - vehicle not placed OOS"); c.setFillColor(colors.black)
    else:
        _t(c,1,7.7,"No violations discovered. Clean inspection.",9)
    _t(c,1,1.0,"Inspector signature on file. Carrier must address violations within required timeframe.",7,gray=True)
