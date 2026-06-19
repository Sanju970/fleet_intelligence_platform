const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";  // 13.3 x 7.5
pres.author = "FleetIQ";
pres.title = "FleetIQ — Grounded Fleet Document Agent";

// ---- palette (matches the dispatch-terminal UI) ----
const BG    = "11151C";   // dark slate
const PANEL = "1C2531";
const LINE  = "2A3543";
const INK   = "E8EDF3";
const MUTED = "8A98A9";
const AMBER = "F5A623";    // accent
const SQL   = "4EA1F5";
const DOC   = "57C98A";
const HYBRID= "C98AE6";
const DANGER= "E5604D";

const SANS = "Calibri";
const SERIF = "Cambria";
const MONO = "Consolas";

const W = 13.3, H = 7.5;

function darkSlide(){ const s = pres.addSlide(); s.background = { color: BG }; return s; }
function shadow(){ return { type:"outer", color:"000000", blur:10, offset:3, angle:90, opacity:0.35 }; }

// kicker label (small mono uppercase)
function kicker(s, text, x, y, color=AMBER){
  s.addText(text, { x, y, w:11.5, h:0.3, fontFace:MONO, fontSize:11, color, charSpacing:3, bold:true, margin:0 });
}

// ============ SLIDE 1 — TITLE ============
(() => {
  const s = darkSlide();
  // subtle panel glow top-right
  s.addShape(pres.shapes.OVAL, { x:9.5, y:-2.5, w:7, h:6, fill:{ color:"1B2433", transparency:35 }, line:{ type:"none" } });
  kicker(s, "BUILDATHON DALLAS 2026  ·  PROBLEM STATEMENT 7", 0.9, 1.5);
  s.addText([
    { text:"Fleet", options:{ color:INK } },
    { text:"IQ", options:{ color:AMBER } },
  ], { x:0.85, y:1.95, w:11, h:1.3, fontFace:SERIF, fontSize:64, bold:true, margin:0 });
  s.addText("A grounded agent that turns a filing cabinet of trucking paperwork into answers — no hallucinations.",
    { x:0.9, y:3.35, w:10.5, h:0.9, fontFace:SANS, fontSize:20, color:MUTED, margin:0 });

  // three quick stat chips
  const chips = [
    ["1,014", "documents ingested"],
    ["12", "real form types"],
    ["3", "retrieval routes"],
  ];
  chips.forEach(([n,l],i) => {
    const x = 0.9 + i*3.0;
    s.addText(n, { x, y:4.6, w:2.7, h:0.8, fontFace:SERIF, fontSize:40, bold:true, color:AMBER, margin:0 });
    s.addText(l, { x, y:5.45, w:2.7, h:0.4, fontFace:MONO, fontSize:11, color:MUTED, margin:0 });
  });
  s.addText("SQL  ·  document retrieval  ·  hybrid — every answer cited to source",
    { x:0.9, y:6.7, w:11, h:0.4, fontFace:MONO, fontSize:12, color:DOC, margin:0 });
})();

// ============ SLIDE 2 — THE PROBLEM ============
(() => {
  const s = darkSlide();
  kicker(s, "THE PROBLEM", 0.9, 0.7);
  s.addText("Trucking carriers run on paper.", { x:0.85, y:1.1, w:11.5, h:0.9, fontFace:SERIF, fontSize:38, bold:true, color:INK, margin:0 });

  s.addText([
    { text:"An active fleet generates ", options:{ color:INK } },
    { text:"50+ documents every week", options:{ color:AMBER, bold:true } },
    { text:" — titles, tax forms, fuel records, registrations, maintenance receipts. They live in filing cabinets, glove boxes, and email threads. Nothing is searchable. Nothing is organized by truck.", options:{ color:MUTED } },
  ], { x:0.9, y:2.05, w:11.4, h:1.1, fontFace:SANS, fontSize:18, margin:0, lineSpacingMultiple:1.1 });

  // the operator's unanswerable questions as cards
  const qs = [
    "Which trucks are profitable?",
    "How much did I spend on parts last month?",
    "Where's the tax form for truck 84?",
    "What do I need to renew these plates?",
  ];
  qs.forEach((q,i) => {
    const x = 0.9 + (i%2)*5.9, y = 3.5 + Math.floor(i/2)*1.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w:5.6, h:1.1, rectRadius:0.08,
      fill:{ color:PANEL }, line:{ color:LINE, width:1 }, shadow:shadow() });
    s.addText("?", { x:x+0.25, y:y+0.2, w:0.7, h:0.7, fontFace:SERIF, fontSize:34, bold:true, color:DANGER, align:"center", margin:0 });
    s.addText(q, { x:x+1.0, y:y+0.32, w:4.4, h:0.5, fontFace:SANS, fontSize:16, color:INK, valign:"middle", margin:0 });
  });

  s.addText("Today, none of these can be answered without digging through physical files.",
    { x:0.9, y:6.55, w:11.4, h:0.5, fontFace:MONO, fontSize:13, color:DANGER, margin:0 });
})();

// ============ SLIDE 3 — THE INSIGHT / WHAT WE BUILT ============
(() => {
  const s = darkSlide();
  kicker(s, "WHAT WE BUILT", 0.9, 0.7);
  s.addText("One question box. Three kinds of answer.", { x:0.85, y:1.1, w:11.5, h:0.9, fontFace:SERIF, fontSize:34, bold:true, color:INK, margin:0 });
  s.addText("The hard part isn't search — it's that different questions need different machinery. FleetIQ routes each one.",
    { x:0.9, y:2.0, w:11.4, h:0.6, fontFace:SANS, fontSize:17, color:MUTED, margin:0 });

  const cards = [
    [SQL,    "SQL",    "Counts, totals, costs, due dates over structured fleet records.", '"How much on parts last month?"'],
    [DOC,    "DOC",    "Find or quote a specific document from 1,014 scanned files.", '"Where\'s the tax form for truck 8?"'],
    [HYBRID, "HYBRID", "A record lookup AND a document, merged into one grounded answer.", '"What\'s due, and what renews it?"'],
  ];
  cards.forEach(([c,tag,desc,ex],i) => {
    const x = 0.9 + i*3.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y:2.9, w:3.7, h:3.5, rectRadius:0.1,
      fill:{ color:PANEL }, line:{ color:LINE, width:1 }, shadow:shadow() });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:x+0.3, y:3.2, w:1.4, h:0.5, rectRadius:0.06, fill:{ color:BG }, line:{ color:c, width:1 } });
    s.addText(tag, { x:x+0.3, y:3.2, w:1.4, h:0.5, fontFace:MONO, fontSize:13, bold:true, color:c, align:"center", valign:"middle", margin:0 });
    s.addText(desc, { x:x+0.3, y:3.95, w:3.1, h:1.5, fontFace:SANS, fontSize:15, color:INK, margin:0, lineSpacingMultiple:1.1 });
    s.addText(ex, { x:x+0.3, y:5.65, w:3.1, h:0.6, fontFace:MONO, fontSize:12, italic:true, color:c, margin:0 });
  });
})();

// ============ SLIDE 4 — ARCHITECTURE ============
(() => {
  const s = darkSlide();
  kicker(s, "ARCHITECTURE", 0.9, 0.7);
  s.addText("Classify → route → ground", { x:0.85, y:1.1, w:11.5, h:0.8, fontFace:SERIF, fontSize:34, bold:true, color:INK, margin:0 });

  // node helper
  const node = (x,y,w,h,label,sub,color) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius:0.08, fill:{ color:PANEL }, line:{ color:color||LINE, width:1.5 }, shadow:shadow() });
    s.addText(label, { x, y:y+(sub?0.12:0), w, h:sub?0.5:h, fontFace:SANS, fontSize:15, bold:true, color:INK, align:"center", valign:"middle", margin:0 });
    if(sub) s.addText(sub, { x, y:y+0.55, w, h:0.35, fontFace:MONO, fontSize:10, color:MUTED, align:"center", margin:0 });
  };
  const arrow = (x,y,w) => s.addShape(pres.shapes.LINE, { x, y, w, h:0, line:{ color:AMBER, width:2, endArrowType:"triangle" } });

  // question -> classify
  node(0.9, 2.6, 2.2, 1.0, "Question", '"tax form truck 8?"', AMBER);
  arrow(3.15, 3.1, 0.7);
  node(3.95, 2.6, 2.2, 1.0, "Classify", "LLM picks route", AMBER);

  // three branches
  node(7.0, 1.5, 2.3, 0.9, "SQL", "fleet.db query", SQL);
  node(7.0, 2.85, 2.3, 0.9, "Retrieval", "vector search", DOC);
  node(7.0, 4.2, 2.3, 0.9, "Hybrid", "both, merged", HYBRID);
  arrow(6.2, 3.1, 0.75);
  s.addShape(pres.shapes.LINE, { x:6.95, y:1.95, w:0, h:1.15, line:{ color:LINE, width:1 } });
  s.addShape(pres.shapes.LINE, { x:6.95, y:3.1, w:0, h:1.55, line:{ color:LINE, width:1 } });

  // ground
  node(10.2, 2.85, 2.3, 0.9, "Ground", "answer + cite", AMBER);
  arrow(9.35, 1.95, 0.8);
  arrow(9.35, 3.3, 0.8);
  arrow(9.35, 4.65, 0.8);

  // grounding guarantee callout
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:0.9, y:5.5, w:11.5, h:1.3, rectRadius:0.08, fill:{ color:"15201A" }, line:{ color:DOC, width:1 }, shadow:shadow() });
  s.addText([
    { text:"GROUNDED  ", options:{ color:DOC, bold:true, fontFace:MONO } },
    { text:"Every answer comes only from retrieved evidence — a real SQL row or a real document. If the evidence isn't there, it says \"I don't have that\" instead of inventing one.", options:{ color:INK } },
  ], { x:1.2, y:5.7, w:10.9, h:0.9, fontFace:SANS, fontSize:15, valign:"middle", margin:0, lineSpacingMultiple:1.05 });
})();

// ============ SLIDE 5 — THE DATA (credibility) ============
(() => {
  const s = darkSlide();
  kicker(s, "THE DATA", 0.9, 0.7);
  s.addText("1,014 documents. Realistically messy.", { x:0.85, y:1.1, w:11.5, h:0.8, fontFace:SERIF, fontSize:34, bold:true, color:INK, margin:0 });
  s.addText("Modeled on 12 real carrier forms — Form 2290, IFTA returns, BOLs, ELD logs, DOT medicals. Internally consistent: a truck's VIN matches across its 2290, registration, and invoices.",
    { x:0.9, y:1.95, w:11.4, h:0.9, fontFace:SANS, fontSize:16, color:MUTED, margin:0, lineSpacingMultiple:1.1 });

  // left: big stats
  const stats = [["1,014","total documents"],["280","messy scans (OCR)"],["12","real form types"],["25","trucks · 90 loads"]];
  stats.forEach(([n,l],i) => {
    const y = 3.1 + i*0.95;
    s.addText(n, { x:0.9, y, w:1.8, h:0.7, fontFace:SERIF, fontSize:32, bold:true, color:AMBER, align:"right", margin:0 });
    s.addText(l, { x:2.85, y:y+0.12, w:3.0, h:0.5, fontFace:MONO, fontSize:13, color:INK, valign:"middle", margin:0 });
  });

  // right: messiness note card
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:7.0, y:3.0, w:5.4, h:3.6, rectRadius:0.1, fill:{ color:PANEL }, line:{ color:LINE, width:1 }, shadow:shadow() });
  s.addText("Why the mess matters", { x:7.3, y:3.25, w:4.8, h:0.5, fontFace:SANS, fontSize:18, bold:true, color:AMBER, margin:0 });
  s.addText([
    { text:"Real fleet paper is photographed and scanned — skewed, stained, stamped, with handwritten notes in the margins.", options:{ breakLine:true, color:INK } },
    { text:"", options:{ breakLine:true, fontSize:8 } },
    { text:"280 of our docs are degraded scans that require OCR. A system that survives them is the differentiator — not one that only reads clean text.", options:{ color:MUTED } },
  ], { x:7.3, y:3.85, w:4.8, h:2.5, fontFace:SANS, fontSize:14.5, margin:0, lineSpacingMultiple:1.15 });
})();

// ============ SLIDE 6 — EVALS (the winning slide) ============
(() => {
  const s = darkSlide();
  kicker(s, "WHAT MOST TEAMS WON'T SHOW", 0.9, 0.7, DOC);
  s.addText("We measure whether it's right.", { x:0.85, y:1.1, w:11.5, h:0.8, fontFace:SERIF, fontSize:34, bold:true, color:INK, margin:0 });
  s.addText("A 20-question gold set across all three routes — including grounding traps where the right answer is \"I don't have that.\" Every answer scored for route accuracy and grounding.",
    { x:0.9, y:1.95, w:11.4, h:0.9, fontFace:SANS, fontSize:16, color:MUTED, margin:0, lineSpacingMultiple:1.1 });

  // eval chart (placeholder numbers — swap with live results)
  s.addChart(pres.charts.BAR, [{
    name:"Accuracy", labels:["Route accuracy","Grounding (traps caught)","Content correct"],
    values:[90, 100, 85]
  }], {
    x:0.9, y:3.1, w:7.2, h:3.6, barDir:"bar",
    chartColors:[DOC], chartArea:{ fill:{ color:BG } },
    catAxisLabelColor:MUTED, valAxisLabelColor:MUTED, catAxisLabelFontFace:MONO, catAxisLabelFontSize:11,
    valAxisMinVal:0, valAxisMaxVal:100, valGridLine:{ color:LINE, size:0.5 }, catGridLine:{ style:"none" },
    showValue:true, dataLabelColor:INK, dataLabelFontFace:MONO, dataLabelFontSize:12, dataLabelPosition:"outEnd",
    showLegend:false, showTitle:false,
  });
  s.addText("← replace with your live numbers at demo time",
    { x:0.9, y:6.75, w:7, h:0.3, fontFace:MONO, fontSize:10, italic:true, color:MUTED, margin:0 });

  // right: why it matters
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:8.5, y:3.1, w:3.9, h:3.6, rectRadius:0.1, fill:{ color:"15201A" }, line:{ color:DOC, width:1 }, shadow:shadow() });
  s.addText("Why this wins", { x:8.8, y:3.35, w:3.3, h:0.5, fontFace:SANS, fontSize:18, bold:true, color:DOC, margin:0 });
  s.addText([
    { text:"Almost no team brings an eval harness.", options:{ breakLine:true, bold:true, color:INK } },
    { text:"", options:{ breakLine:true, fontSize:8 } },
    { text:"An agent you can't measure is a demo. An agent with a failure map is engineering. We can tell you exactly where it breaks — and that's the most senior thing in the room.", options:{ color:MUTED } },
  ], { x:8.8, y:3.95, w:3.3, h:2.5, fontFace:SANS, fontSize:14, margin:0, lineSpacingMultiple:1.15 });
})();

// ============ SLIDE 7 — STACK + GENERALIZES ============
(() => {
  const s = darkSlide();
  kicker(s, "THE STACK", 0.9, 0.7);
  s.addText("Production-grade, not a prompt wrapper.", { x:0.85, y:1.1, w:11.5, h:0.8, fontFace:SERIF, fontSize:32, bold:true, color:INK, margin:0 });

  const stack = [
    ["LangGraph", "stateful routing agent"],
    ["Tesseract OCR", "reads the messy scans"],
    ["Chroma + embeddings", "vector retrieval, truck-tagged"],
    ["SQLite", "structured fleet records"],
    ["Groq + Claude", "fast routing, grounded synthesis"],
    ["FastAPI + live UI", "shows the route it took"],
  ];
  stack.forEach(([t,d],i) => {
    const x = 0.9 + (i%3)*3.95, y = 2.2 + Math.floor(i/3)*1.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w:3.7, h:1.05, rectRadius:0.08, fill:{ color:PANEL }, line:{ color:LINE, width:1 }, shadow:shadow() });
    s.addText(t, { x:x+0.25, y:y+0.15, w:3.2, h:0.45, fontFace:SANS, fontSize:16, bold:true, color:AMBER, margin:0 });
    s.addText(d, { x:x+0.25, y:y+0.58, w:3.2, h:0.4, fontFace:MONO, fontSize:11, color:MUTED, margin:0 });
  });

  // generalizes band
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:0.9, y:5.1, w:11.5, h:1.7, rectRadius:0.1, fill:{ color:"1A1726" }, line:{ color:HYBRID, width:1 }, shadow:shadow() });
  s.addText("The trucking data is swappable.", { x:1.25, y:5.35, w:11, h:0.5, fontFace:SANS, fontSize:20, bold:true, color:HYBRID, margin:0 });
  s.addText("The same classify→route→ground engine answers over enterprise BigQuery (Statement 1) or 400-page manufacturing manuals (Statement 9). One engine, many domains.",
    { x:1.25, y:5.9, w:10.9, h:0.8, fontFace:SANS, fontSize:15, color:INK, margin:0, lineSpacingMultiple:1.05 });
})();

// ============ SLIDE 8 — CLOSE ============
(() => {
  const s = darkSlide();
  s.addShape(pres.shapes.OVAL, { x:-2.5, y:3.5, w:8, h:7, fill:{ color:"1B2433", transparency:40 }, line:{ type:"none" } });
  kicker(s, "FLEETIQ", 0.9, 1.4);
  s.addText("From filing cabinet to answer.", { x:0.85, y:1.85, w:11.5, h:1.0, fontFace:SERIF, fontSize:46, bold:true, color:INK, margin:0 });
  s.addText("Ask in plain English. Get a grounded, cited answer — SQL, document, or both. Nothing invented.",
    { x:0.9, y:3.1, w:10.5, h:0.8, fontFace:SANS, fontSize:19, color:MUTED, margin:0 });

  const pts = [
    ["1,014 docs", "ingested + OCR'd", AMBER],
    ["3 routes", "SQL / doc / hybrid", SQL],
    ["grounded", "measured, not claimed", DOC],
  ];
  pts.forEach(([n,l,c],i) => {
    const x = 0.9 + i*3.9;
    s.addText(n, { x, y:4.3, w:3.6, h:0.7, fontFace:SERIF, fontSize:30, bold:true, color:c, margin:0 });
    s.addText(l, { x, y:5.05, w:3.6, h:0.4, fontFace:MONO, fontSize:12, color:MUTED, margin:0 });
  });

  s.addShape(pres.shapes.LINE, { x:0.9, y:6.0, w:11.5, h:0, line:{ color:LINE, width:1 } });
  s.addText("Built at Buildathon Dallas 2026  ·  Problem Statement 7  ·  github.com/Nanduu24",
    { x:0.9, y:6.3, w:11.5, h:0.4, fontFace:MONO, fontSize:12, color:MUTED, margin:0 });
})();

pres.writeFile({ fileName: "/home/claude/fleetiq/deck/FleetIQ_Pitch.pptx" }).then(f => console.log("saved", f));
