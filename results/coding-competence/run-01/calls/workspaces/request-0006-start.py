def parse_movement(entry):
    if not isinstance(entry, dict):
        return {"ok": False, "error": "entry must have exactly the fields item, qty and kind"}
    if set(entry.keys()) != {"item", "qty", "kind"}:
        return {"ok": False, "error": "entry must have exactly the fields item, qty and kind"}
    item = entry["item"]
    if not isinstance(item, str) or not item.strip():
        return {"ok": False, "error": "item must be a nonempty string"}
    qty = entry["qty"]
    if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
        return {"ok": False, "error": "qty must be a positive integer"}
    kind = entry["kind"]
    if kind != "in" and kind != "out":
        return {"ok": False, "error": "kind must be 'in' or 'out'"}
    return {"ok": True, "movement": {"item": item, "qty": qty, "kind": kind}}


def summarize_movements(batch):
    return None


def reconcile_stock(payload):
    return None


def audit_inventory(payload):
    return None
