import json
import os
from datetime import datetime

DATA_FILE = "sessions.json"

def load_sessions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_session(results):
    sessions = load_sessions()
    session = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "results": results,
        "avg_scores": _average_scores(results)
    }
    sessions.append(session)
    with open(DATA_FILE, "w") as f:
        json.dump(sessions, f, indent=2)
    return session

def _average_scores(results):
    dims = ["clarity", "specificity", "relevance", "structure", "impact"]
    totals = {d: 0 for d in dims}
    count = len(results)
    if count == 0:
        return totals
    for r in results:
        for d in dims:
            totals[d] += r["evaluation"]["scores"].get(d, 0)
    return {d: round(totals[d] / count, 2) for d in dims}

def get_weakest_dimension(sessions):
    if not sessions:
        return "structure"
    dims = ["clarity", "specificity", "relevance", "structure", "impact"]
    totals = {d: 0 for d in dims}
    count = len(sessions)
    for s in sessions:
        for d in dims:
            totals[d] += s["avg_scores"].get(d, 0)
    averages = {d: totals[d] / count for d in dims}
    return min(averages, key=averages.get)