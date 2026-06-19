"""
Lane B — OCR ingestion pipeline. THE HARD PART, handled.

Reads every document in data/docs/:
  - clean PDFs  -> native text extraction (pdfplumber, fast)
  - messy PNGs  -> Tesseract OCR (handles skew/stains/handwriting as best it can)
Then for each doc:
  - tags it to truck/driver/load via data/manifest.json (ground truth)
  - chunks the text
  - embeds + stores in a Chroma vector DB at db/chroma/

Every chunk carries metadata {file, doc_type, truck_id, driver_id, load_id} so the
agent can ground answers and the SQL side can join. This is the contract Lane C
and Lane D depend on.

Run:  python ingest/pipeline.py            # full ingest (~1000 docs)
      python ingest/pipeline.py --limit 50 # quick smoke test

Speed: OCR is the bottleneck. ~280 scans dominate runtime. Kick this off in HOUR 1.
"""
import os, json, sys, time, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "data", "docs")
MANIFEST = os.path.join(ROOT, "data", "manifest.json")
CHROMA_DIR = os.path.join(ROOT, "db", "chroma")

# ---------- embeddings ----------
# Chroma's default downloads an ONNX model. At the event that works; offline it may not.
# We provide a no-download fallback so the pipeline ALWAYS runs. Swap EMBEDDER at the
# event for real semantic quality (sentence-transformers or an API embedder).
def get_embedding_function():
    # 1) try sentence-transformers (best quality, needs model download)
    try:
        from chromadb.utils import embedding_functions
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2")
    except Exception:
        pass
    # 2) fallback: deterministic hashing embedder, zero downloads, runs anywhere
    import hashlib
    from chromadb import EmbeddingFunction, Documents, Embeddings
    class HashEmbedder(EmbeddingFunction):
        DIM = 384
        def __call__(self, inputs: Documents) -> Embeddings:
            out = []
            for text in inputs:
                vec = [0.0] * self.DIM
                for tok in text.lower().split():
                    h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
                    vec[h % self.DIM] += 1.0
                norm = sum(v*v for v in vec) ** 0.5 or 1.0
                out.append([v / norm for v in vec])
            return out
    print("  [embeddings] using no-download HASH fallback "
          "(swap for sentence-transformers at the event for semantic quality)")
    return HashEmbedder()

# ---------- text extraction ----------
def extract_pdf(path):
    import pdfplumber
    out = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            out.append(t)
    return "\n".join(out)

def extract_image(path):
    import pytesseract
    from PIL import Image
    img = Image.open(path)
    # light preprocess helps Tesseract on scans: grayscale + upscale
    img = img.convert("L")
    if img.width < 1500:
        img = img.resize((int(img.width*1.5), int(img.height*1.5)))
    # psm 4: assume a single column of text of variable sizes (good for forms)
    return pytesseract.image_to_string(img, config="--psm 4")

def extract(path):
    if path.lower().endswith(".pdf"):
        return extract_pdf(path), "native"
    return extract_image(path), "ocr"

# ---------- chunking ----------
def chunk(text, size=600, overlap=80):
    text = " ".join(text.split())  # normalize whitespace
    if len(text) <= size:
        return [text] if text.strip() else []
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap
    return chunks

# ---------- main ingest ----------
def run(limit=None, reset=True):
    import chromadb
    with open(MANIFEST) as f:
        man = {m["file"]: m for m in json.load(f)["documents"]}

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    if reset:
        try: client.delete_collection("fleet_docs")
        except Exception: pass
    col = client.get_or_create_collection("fleet_docs", embedding_function=get_embedding_function())

    files = sorted([f for f in os.listdir(DOCS) if f.endswith((".pdf", ".png"))])
    if limit: files = files[:limit]

    t0 = time.time()
    ids, docs, metas = [], [], []
    n_ocr = n_native = n_empty = 0
    for n, fn in enumerate(files, 1):
        path = os.path.join(DOCS, fn)
        try:
            text, method = extract(path)
        except Exception as e:
            print(f"  ! {fn}: {e}"); continue
        if method == "ocr": n_ocr += 1
        else: n_native += 1
        meta_src = man.get(fn, {})
        chunks = chunk(text)
        if not chunks:
            n_empty += 1
        for ci, ch in enumerate(chunks):
            ids.append(f"{fn}::{ci}")
            docs.append(ch)
            metas.append({
                "file": fn,
                "doc_type": meta_src.get("doc_type", "unknown"),
                "truck_id": meta_src.get("truck_id", -1),
                "driver_id": meta_src.get("driver_id", -1),
                "load_id": str(meta_src.get("load_id", "")),
                "format": meta_src.get("format", "pdf"),
                "extract_method": method,
            })
        # batch flush every 500 chunks (chroma embeds on add)
        if len(ids) >= 500:
            col.add(ids=ids, documents=docs, metadatas=metas)
            ids, docs, metas = [], [], []
        if n % 100 == 0:
            print(f"  ...{n}/{len(files)} docs  ({n_ocr} OCR, {n_native} native)  {time.time()-t0:.0f}s")

    if ids:
        col.add(ids=ids, documents=docs, metadatas=metas)

    dt = time.time() - t0
    print("=" * 52)
    print(f"  Ingested {len(files)} docs in {dt:.0f}s")
    print(f"  Native (PDF): {n_native}   OCR (scan): {n_ocr}   empty: {n_empty}")
    print(f"  Vector chunks: {col.count()}")
    print(f"  Chroma DB: {CHROMA_DIR}")
    print("=" * 52)
    return col

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    run(limit=args.limit)
