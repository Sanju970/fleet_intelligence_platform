"""Integration tests over the generated dataset. Skipped on a fresh clone until
`make build` (or the generate/build_db steps) has produced the artifacts."""
import os, json, sqlite3
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "fleet.db")
MANIFEST = os.path.join(ROOT, "data", "manifest.json")

pytestmark = pytest.mark.skipif(
    not (os.path.exists(DB) and os.path.exists(MANIFEST)),
    reason="dataset not built — run `make build` first",
)


@pytest.fixture(scope="module")
def docs():
    with open(MANIFEST) as f:
        return json.load(f)["documents"]


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(DB)
    yield c
    c.close()


def test_core_tables_present(con):
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"trucks", "drivers", "trailers", "loads", "expenses", "registrations"} <= names


def test_every_truck_has_a_registration(con):
    trucks = con.execute("SELECT COUNT(*) FROM trucks").fetchone()[0]
    regs = con.execute("SELECT COUNT(DISTINCT truck_id) FROM registrations").fetchone()[0]
    assert trucks > 0 and regs == trucks


def test_expenses_reference_real_trucks(con):
    orphans = con.execute(
        "SELECT COUNT(*) FROM expenses WHERE truck_id NOT IN (SELECT truck_id FROM trucks)"
    ).fetchone()[0]
    assert orphans == 0


def test_documents_link_to_valid_entities(con, docs):
    truck_ids = {r[0] for r in con.execute("SELECT truck_id FROM trucks")}
    for d in docs:
        tid = d.get("truck_id")
        if tid not in (None, -1):
            assert tid in truck_ids, f"{d['file']} tagged to unknown truck {tid}"


def test_annual_docs_cover_every_truck(con, docs):
    truck_ids = {r[0] for r in con.execute("SELECT truck_id FROM trucks")}
    for dt in ("vehicle_title", "form_2290", "vehicle_registration"):
        covered = {d["truck_id"] for d in docs if d["doc_type"] == dt and d.get("truck_id", -1) > 0}
        assert covered == truck_ids, f"{dt} missing for trucks {truck_ids - covered}"
