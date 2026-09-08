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
    if not isinstance(batch, list):
        return {"ok": False, "error": "batch must be a list"}
    items = {}
    total_in = 0
    total_out = 0
    count = 0
    for i, entry in enumerate(batch):
        result = parse_movement(entry)
        if not result["ok"]:
            return {"ok": False, "error": f"invalid movement at index {i}: {result["error"]}"}
        movement = result["movement"]
        item = movement["item"]
        qty = movement["qty"]
        kind = movement["kind"]
        if item not in items:
            items[item] = {"in": 0, "out": 0, "net": 0}
        if kind == "in":
            items[item]["in"] += qty
            total_in += qty
        else:
            items[item]["out"] += qty
            total_out += qty
        items[item]["net"] = items[item]["in"] - items[item]["out"]
        count += 1
    return {"ok": True, "items": items, "total_in": total_in, "total_out": total_out, "count": count}


def reconcile_stock(payload):
    return None


def audit_inventory(payload):
    return None
