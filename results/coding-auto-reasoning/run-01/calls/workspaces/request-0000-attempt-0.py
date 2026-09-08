def normalize_submission(payload):
    if not isinstance(payload, dict):
        return {"ok": False, "error": "payload must be an object"}
    student = payload.get("student")
    assignment = payload.get("assignment")
    score = payload.get("score")
    if not isinstance(student, str) or student.strip() == "":
        return {"ok": False, "error": "student must be a non-empty string"}
    if not isinstance(assignment, str) or assignment.strip() == "":
        return {"ok": False, "error": "assignment must be a non-empty string"}
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return {"ok": False, "error": "score must be a number"}
    if score < 0 or score > 100:
        return {"ok": False, "error": "score must be between 0 and 100"}
    return {"ok": True, "record": {"student": student.strip(), "assignment": assignment.strip(), "score": score}}


def validate_batch(batch):
    if not isinstance(batch, list):
        return {"ok": False, "error": "batch must be a list"}
    valid = []
    errors = []
    for i, payload in enumerate(batch):
        result = normalize_submission(payload)
        if result["ok"]:
            valid.append(result["record"])
        else:
            errors.append({"index": i, "error": result["error"]})
    counts = {
        "total": len(batch),
        "valid": len(valid),
        "invalid": len(errors)
    }
    return {
        "ok": True,
        "valid": valid,
        "errors": errors,
        "counts": counts
    }


def group_submissions(batch):
    return None


def summarize_class(batch):
    return None
