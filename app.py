# app.py
# Flask backend for Shrimp Contamination Dashboard (zone circles: Sumatra, Java, Kalimantan, Sulawesi, Papua)
# Run: pip install flask flask-cors
#       python app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random, statistics, math

app = Flask(__name__)
CORS(app)

# -----------------------
# ZONES (island centers used for circle placement)
# -----------------------
ZONES_META = {
    "sumatra":  {"name": "Sumatra", "center": [0.7893, 101.4528]},
    "java":     {"name": "Java",    "center": [-7.2756, 112.7977]},
    "kalimantan":{"name":"Kalimantan","center":[-1.0, 114.0]},
    "sulawesi": {"name": "Sulawesi","center":[-1.5, 121.0]},
    "papua":    {"name": "Papua",   "center":[-4.0, 138.0]}
}

# -----------------------
# Preloaded farms (demo) distributed across islands
# Each farm: id,name,lat,lng,history (list of {time,inspector,value})
# -----------------------
now = datetime.utcnow()
def make_history(base, days=7):
    # create synthetic history points for last `days`
    arr = []
    for d in range(days):
        t = (now - timedelta(days=(days-d-1))).isoformat()
        v = round(max(0, base + random.uniform(-6,6)), 2)
        arr.append({"time": t, "inspector": random.choice(["Asep","Siti","Tono","Budi","Ani"]), "value": v})
    return arr

FARMS = [
    {"id": 1, "name": "Sumatra Shrimp Farm A", "location": "Medan, Sumatra", "lat": 3.5952, "lng": 98.6722},
    {"id": 2, "name": "Sumatra Shrimp Farm B", "location": "Padang, Sumatra", "lat": -0.9471, "lng": 100.4172},
    {"id": 3, "name": "Java Coastal Farm A", "location": "Jakarta, Java", "lat": -6.2000, "lng": 106.8166},
    {"id": 4, "name": "Java Coastal Farm B", "location": "Surabaya, Java", "lat": -7.2575, "lng": 112.7521},
    {"id": 5, "name": "Kalimantan Delta Farm", "location": "Samarinda, Kalimantan", "lat": -0.5021, "lng": 117.1537},
    {"id": 6, "name": "Sulawesi Aqua Farm", "location": "Makassar, Sulawesi", "lat": -5.1477, "lng": 119.4327},
    {"id": 7, "name": "Papua Biofarm", "location": "Jayapura, Papua", "lat": -2.5339, "lng": 140.7181},
]

# seed base contamination and history
for f in FARMS:
    base = round(random.uniform(12, 65), 2)  # base value
    f["history"] = make_history(base, days=7)
    # set current to last history value
    f["value"] = f["history"][-1]["value"]
    # status by thresholds
    if f["value"] >= 60:
        f["status"] = "Critical"
    elif f["value"] >= 45:
        f["status"] = "High"
    elif f["value"] >= 30:
        f["status"] = "Medium"
    else:
        f["status"] = "Safe"
    f["lastUpdate"] = f["history"][-1]["time"]

# -----------------------
# Helpers
# -----------------------
def compute_zone_aggregation():
    """
    For each zone, compute:
     - avg contamination (avg across farms assigned to that zone)
     - severity label
     - recommended radius (meters) for circle visualization
    Assignment to zone: naive nearest zone center (sufficient for demo)
    """
    zone_values = {k: [] for k in ZONES_META.keys()}
    zone_farms = {k: [] for k in ZONES_META.keys()}

    for f in FARMS:
        lat, lng = f["lat"], f["lng"]
        # find nearest zone center
        best = None
        bestd = 1e9
        for zid, meta in ZONES_META.items():
            cy, cx = meta["center"]
            d = (cy - lat)**2 + (cx - lng)**2
            if d < bestd:
                bestd = d; best = zid
        zone_values[best].append(f["value"])
        zone_farms[best].append(f)

    zones_out = []
    for zid, meta in ZONES_META.items():
        vals = zone_values[zid]
        avg_val = round(statistics.mean(vals),2) if vals else 0
        if avg_val >= 60:
            severity = "Critical"
        elif avg_val >= 45:
            severity = "High"
        elif avg_val >= 30:
            severity = "Medium"
        else:
            severity = "Safe"
        # compute radius in meters: scale avg_val -> radius (capped)
        # mapping: avg_val 0 -> 20000 m, 30 -> 60000, 60 -> 140000, >60 grows more, capped at 220000
        radius = int(min(220000, 20000 + avg_val * 3000))
        # pick top farm if exists
        top_farm = None
        if zone_farms[zid]:
            top_farm = max(zone_farms[zid], key=lambda x: x["value"])
        zones_out.append({
            "id": zid,
            "name": meta["name"],
            "center": meta["center"],
            "avg": avg_val,
            "severity": severity,
            "radius_m": radius,
            "top_farm": {"id": top_farm["id"], "name": top_farm["name"], "value": top_farm["value"]} if top_farm else None,
            "count_farms": len(zone_farms[zid])
        })
    return zones_out

def agg_stats():
    vals = [f["value"] for f in FARMS]
    if not vals:
        return {"total":0,"avg":0,"max":0,"min":0,"high":0,"medium":0,"safe":0}
    total = len(FARMS)
    avgv = round(sum(vals)/len(vals),2)
    high = sum(1 for v in vals if v >= 45)
    medium = sum(1 for v in vals if 30 <= v < 45)
    safe = sum(1 for v in vals if v < 30)
    top_hotspots = sorted([{"id":f["id"], "name":f["name"], "value":f["value"]} for f in FARMS], key=lambda x: x["value"], reverse=True)[:5]
    # timeseries: average across farms for each day in history (assuming aligned by index)
    days = len(FARMS[0]["history"]) if FARMS else 0
    timeseries = []
    for i in range(days):
        vals_day = [f["history"][i]["value"] if i < len(f["history"]) else f["value"] for f in FARMS]
        timeseries.append({"t": (now - timedelta(days=days-i-1)).date().isoformat(), "v": round(statistics.mean(vals_day),2)})
    return {"total": total, "avg": avgv, "max": max(vals), "min": min(vals), "high": high, "medium": medium, "safe": safe, "top_hotspots": top_hotspots, "timeseries": timeseries}

# -----------------------
# API endpoints
# -----------------------
@app.route("/api/farms", methods=["GET"])
def api_farms():
    # return farms with summary fields (do not include full history optionally)
    return jsonify(FARMS)

@app.route("/api/zones", methods=["GET"])
def api_zones():
    return jsonify(compute_zone_aggregation())

@app.route("/api/stats", methods=["GET"])
def api_stats():
    s = agg_stats()
    # also include recent trips demo
    s["recent_trips"] = [
        {"location": "Site visit - Java southeast coast", "time": (now - timedelta(days=1)).strftime("%d %b %Y %H:%M")},
        {"location": "Lab pick-up - Bali", "time": (now - timedelta(days=2)).strftime("%d %b %Y %H:%M")}
    ]
    return jsonify(s)

@app.route("/api/heatmap", methods=["GET"])
def api_heatmap():
    points = [[f["lat"], f["lng"], max(0.1, f["value"]/10)] for f in FARMS]
    return jsonify({"points": points})

@app.route("/api/samples", methods=["POST"])
def api_samples():
    data = request.get_json() or {}
    farm_id = data.get("farm_id")
    value = data.get("value")
    inspector = data.get("inspector", "unknown")
    if farm_id is None or value is None:
        return jsonify({"success": False, "error": "missing fields"}), 400
    farm = next((f for f in FARMS if f["id"] == farm_id), None)
    if not farm:
        return jsonify({"success": False, "error": "farm not found"}), 404
    nowiso = datetime.utcnow().isoformat()
    farm.setdefault("history", []).append({"time": nowiso, "inspector": inspector, "value": float(value)})
    farm["value"] = float(value)
    if farm["value"] >= 60:
        farm["status"] = "Critical"
    elif farm["value"] >= 45:
        farm["status"] = "High"
    elif farm["value"] >= 30:
        farm["status"] = "Medium"
    else:
        farm["status"] = "Safe"
    farm["lastUpdate"] = nowiso
    return jsonify({"success": True, "farm": farm})

@app.route("/api/simulate", methods=["GET"])
def api_simulate():
    # randomize values to simulate live updates
    for f in FARMS:
        change = random.uniform(-8, 10)
        newv = round(max(0, f["value"] + change), 2)
        f.setdefault("history", []).append({"time": datetime.utcnow().isoformat(), "inspector": "sim", "value": newv})
        f["value"] = newv
        if newv >= 60:
            f["status"] = "Critical"
        elif newv >= 45:
            f["status"] = "High"
        elif newv >= 30:
            f["status"] = "Medium"
        else:
            f["status"] = "Safe"
        f["lastUpdate"] = f["history"][-1]["time"]
    return jsonify({"success": True})

# root
@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "Shrimp Contamination API running"})

# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
