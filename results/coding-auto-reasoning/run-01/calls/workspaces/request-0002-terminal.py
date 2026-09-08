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
    validation = validate_batch(batch)
    if not validation["ok"]:
        return validation
    groups = {}
    for record in validation["valid"]:
        assignment = record["assignment"]
        if assignment not in groups:
            groups[assignment] = []
        groups[assignment].append(record)
    return {
        "ok": True,
        "groups": groups,
        "errors": validation["errors"]
    }


def summarize_class(batch):
    group_result = group_submissions(batch)
    if not group_result["ok"]:
        return group_result
    groups = group_result["groups"]
    assignments = {}
    all_scores = []
    all_students = set()
    for assignment, records in groups.items():
        student_scores = {}
        for record in records:
            student = record["student"]
            score = record["score"]
            if student not in student_scores or score > student_scores[student]:
                student_scores[student] = score
        # Calculate stats for this assignment
        scores = list(student_scores.values())
        submissions = len(scores)
        students = len(student_scores)
        average = round(sum(scores)/submissions, 1) if submissions else None
        assignments[assignment] = {
            "submissions": submissions,
            "students": students,
            "average": average
        }
        # Update overall data
        all_scores.extend(scores)
        all_students.update(student_scores.keys())
    # Calculate overall stats
    overall_submissions = len(all_scores)
    overall_students = len(all_students)
    overall_average = round(sum(all_scores)/overall_submissions, 1) if overall_submissions else None
    return {
        "ok": True,
        "assignments": assignments,
        "overall": {
            "submissions": overall_submissions,
            "students": overall_students,
            "average": overall_average
        },
        "errors": group_result["errors"]
    }