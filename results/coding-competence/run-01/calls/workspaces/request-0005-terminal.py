# lab_pipeline.py: laboratory sample cleaning, normalization, aggregation and reporting.
# Conventions: functions take one JSON-style argument and return JSON-compatible
# values; invalid input yields exactly the string "invalid". Sample entries are
# validated only here in clean_sample.


def clean_sample(entry):
    if not isinstance(entry, dict):
        return "invalid"
    if "id" not in entry or "conc" not in entry or "vol" not in entry:
        return "invalid"
    ident = entry["id"]
    conc = entry["conc"]
    vol = entry["vol"]
    if not isinstance(ident, str) or len(ident) == 0:
        return "invalid"
    if isinstance(conc, bool) or not isinstance(conc, (int, float)) or not conc > 0:
        return "invalid"
    if isinstance(vol, bool) or not isinstance(vol, (int, float)) or not vol > 0:
        return "invalid"
    flag = entry.get("flag", False)
    if not isinstance(flag, bool):
        return "invalid"
    group = entry.get("group", "unassigned")
    if not isinstance(group, str) or len(group) == 0:
        return "invalid"
    return {"id": ident, "conc": float(conc), "vol": float(vol), "flag": flag, "group": group}


def normalize_batch(payload):
    if not isinstance(payload, dict):
        return "invalid"
    if "samples" not in payload or "dilution" not in payload:
        return "invalid"
    samples = payload["samples"]
    dilution = payload["dilution"]
    if not isinstance(samples, list) or len(samples) == 0:
        return "invalid"
    if not isinstance(dilution, (int, float)) or not dilution > 0:
        return "invalid"
    normalized_samples = []
    total_mass = 0.0
    for sample in samples:
        cleaned = clean_sample(sample)
        if cleaned == "invalid":
            return "invalid"
        adj_conc = cleaned["conc"] * dilution
        mass = adj_conc * cleaned["vol"]
        normalized_samples.append({
            "id": cleaned["id"],
            "adj_conc": adj_conc,
            "mass": mass,
            "flag": cleaned["flag"],
            "group": cleaned["group"]
        })
        total_mass += mass
    return {"samples": normalized_samples, "total_mass": total_mass}


def aggregate_run(run):
    if not isinstance(run, dict):
        return "invalid"
    if "samples" not in run or "dilution" not in run:
        return "invalid"
    samples = run["samples"]
    dilution = run["dilution"]
    include_flagged = run.get("include_flagged", False)
    if not isinstance(samples, list) or len(samples) == 0:
        return "invalid"
    if not isinstance(dilution, (int, float)) or not dilution > 0:
        return "invalid"
    if not isinstance(include_flagged, bool):
        return "invalid"
    normalized = normalize_batch({"samples": samples, "dilution": dilution})
    if normalized == "invalid":
        return "invalid"
    samples_data = normalized["samples"]
    filtered_samples = [s for s in samples_data if include_flagged or not s["flag"]]
    groups = {}
    for sample in filtered_samples:
        group_name = sample["group"]
        if group_name not in groups:
            groups[group_name] = {
                "count": 0,
                "total_mass": 0.0,
                "total_conc": 0.0
            }
        groups[group_name]["count"] += 1
        groups[group_name]["total_mass"] += sample["mass"]
        groups[group_name]["total_conc"] += sample["adj_conc"]
    group_list = []
    for group_name in sorted(groups.keys()):
        group_data = groups[group_name]
        mean_conc = group_data["total_conc"] / group_data["count"] if group_data["count"] > 0 else 0.0
        group_list.append({
            "group": group_name,
            "count": group_data["count"],
            "total_mass": group_data["total_mass"],
            "mean_conc": mean_conc
        })
    return {
        "groups": group_list,
        "count": len(filtered_samples)
    }


def build_report(job):
    if not isinstance(job, dict):
        return "invalid"
    if "title" not in job or "samples" not in job or "dilution" not in job:
        return "invalid"
    title = job["title"]
    samples = job["samples"]
    dilution = job["dilution"]
    if not isinstance(title, str) or len(title) == 0:
        return "invalid"
    if not isinstance(samples, list) or len(samples) == 0:
        return "invalid"
    if not isinstance(dilution, (int, float)) or not dilution > 0:
        return "invalid"
    aggregate_input = {
        "samples": samples,
        "dilution": dilution,
        "include_flagged": True
    }
    aggregate_result = aggregate_run(aggregate_input)
    if aggregate_result == "invalid":
        return "invalid"
    groups = aggregate_result["groups"]
    group_count = len(groups)
    grand_total_mass = sum(g["total_mass"] for g in groups)
    top_group = None
    max_mass = -1
    for group in groups:
        if group["total_mass"] > max_mass or (group["total_mass"] == max_mass and (top_group is None or group["group"] < top_group)):
            max_mass = group["total_mass"]
            top_group = group["group"]
    return {
        "title": title,
        "group_count": group_count,
        "grand_total_mass": grand_total_mass,
        "top_group": top_group,
        "groups": groups
    }