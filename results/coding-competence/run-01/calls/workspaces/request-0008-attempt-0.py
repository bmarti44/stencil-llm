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
    if not isinstance(payload, dict):
        return {"ok": False, "error": "payload must contain opening, movements and optional allow_backorder only"}
    required_fields = {"opening", "movements"}
    if not required_fields.issubset(payload.keys()):
        return {"ok": False, "error": "payload must contain opening, movements and optional allow_backorder only"}
    if len(set(payload.keys()) - {"opening", "movements", "allow_backorder"}) > 0:
        return {"ok": False, "error": "payload must contain opening, movements and optional allow_backorder only"}
    
    # Validate opening
    opening = payload["opening"]
    if not isinstance(opening, dict):
        return {"ok": False, "error": "opening must map item names to nonnegative integers"}
    for item, qty in opening.items():
        if not isinstance(item, str) or not item.strip():
            return {"ok": False, "error": "opening must map item names to nonnegative integers"}
        if not isinstance(qty, int) or qty < 0:
            return {"ok": False, "error": "opening must map item names to nonnegative integers"}
    
    # Validate allow_backorder
    allow_backorder = payload.get("allow_backorder")
    if allow_backorder is not None:
        if not isinstance(allow_backorder, list):
            return {"ok": False, "error": "allow_backorder must be a list of item names"}
        for item in allow_backorder:
            if not isinstance(item, str) or not item.strip():
                return {"ok": False, "error": "allow_backorder must be a list of item names"}
    
    # Summarize movements
    summary = summarize_movements(payload["movements"])
    if not summary["ok"]:
        return summary
    
    # Calculate closing balances
    closing = {}
    for item in opening:
        closing[item] = opening[item]
    
    for item, data in summary["items"].items():
        net = data["net"]
        if item in closing:
            closing[item] += net
        else:
            closing[item] = net
    
    # Check for negative balances
    negative_items = [item for item, balance in closing.items() if balance < 0 and (allow_backorder is None or item not in allow_backorder)]
    if negative_items:
        negative_items.sort()
        return {"ok": False, "error": "negative closing balance", "item": negative_items[0], "balance": closing[negative_items[0]]}
    
    return {"ok": True, "closing": closing, "total_in": summary["total_in"], "total_out": summary["total_out"]}


def audit_inventory(payload):
    result = reconcile_stock(payload)
    if not result["ok"]:
        return result
    
    closing = result["closing"]
    total_in = result["total_in"]
    total_out = result["total_out"]
    
    # Find shortages
    shortages = [item for item, balance in closing.items() if balance < 0]
    shortages.sort()
    shortage_count = len(shortages)
    status = "clear" if shortage_count == 0 else "shortage"
    
    return {
        "ok": True,
        "closing": closing,
        "shortages": shortages,
        "shortage_count": shortage_count,
        "status": status,
        "total_in": total_in,
        "total_out": total_out
    }