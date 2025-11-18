from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import random, statistics, math, os
from uuid import uuid4
from functools import wraps

app = Flask(__name__)
CORS(app)

# -----------------------
# CONFIGURATION
# -----------------------
# Real FDA thresholds based on 2025 incident
THRESHOLD_CRITICAL = 60  # ppb (parts per billion)
THRESHOLD_HIGH = 45
THRESHOLD_MEDIUM = 30
FDA_INTERVENTION_LEVEL = 1200  # Bq/kg (becquerel per kilogram)

# Conversion: 1 Bq/kg ≈ 0.027 ppb for Cs-137
def bq_to_ppb(bq):
    return round(bq * 0.027, 2)

def ppb_to_bq(ppb):
    return round(ppb / 0.027, 2)

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
# -----------------------
now = datetime.utcnow()

def make_history(base, days=7):
    """Create synthetic history points for last N days with realistic variation"""
    arr = []
    for d in range(days):
        t = (now - timedelta(days=(days-d-1))).isoformat()
        # Add seasonal/random variation
        variation = random.uniform(-6, 6)
        v = round(max(0, base + variation), 2)
        arr.append({
            "time": t, 
            "inspector": random.choice(["Asep","Siti","Tono","Budi","Ani","Dewi","Eko"]), 
            "value": v,
            "notes": ""
        })
    return arr

# More realistic farm data
FARMS = [
    {"id": 1, "name": "Tambak Udang Medan Prima", "location": "Medan, North Sumatra", "lat": 3.5952, "lng": 98.6722, "operator": "CV Maju Jaya", "capacity": "15 ha"},
    {"id": 2, "name": "Padang Coastal Shrimp Farm", "location": "Padang, West Sumatra", "lat": -0.9471, "lng": 100.4172, "operator": "PT Samudra Raya", "capacity": "8 ha"},
    {"id": 3, "name": "Jakarta Bay Aquaculture", "location": "Jakarta, Java", "lat": -6.2000, "lng": 106.8166, "operator": "PT Bahari Nusantara", "capacity": "12 ha"},
    {"id": 4, "name": "Surabaya Delta Farm", "location": "Surabaya, East Java", "lat": -7.2575, "lng": 112.7521, "operator": "CV Delta Prima", "capacity": "20 ha"},
    {"id": 5, "name": "Lampung Export Shrimp", "location": "Lampung, Sumatra", "lat": -5.4292, "lng": 105.2619, "operator": "PT Lampung Sejahtera", "capacity": "18 ha"},
    {"id": 6, "name": "Cirebon Coastal Farm", "location": "Cirebon, West Java", "lat": -6.7063, "lng": 108.5571, "operator": "CV Cirebon Makmur", "capacity": "10 ha"},
    {"id": 7, "name": "Samarinda Delta Aqua", "location": "Samarinda, East Kalimantan", "lat": -0.5021, "lng": 117.1537, "operator": "PT Kalimantan Shrimp", "capacity": "25 ha"},
    {"id": 8, "name": "Makassar Premium Shrimp", "location": "Makassar, South Sulawesi", "lat": -5.1477, "lng": 119.4327, "operator": "CV Sulawesi Aqua", "capacity": "14 ha"},
    {"id": 9, "name": "Jayapura Bio Farm", "location": "Jayapura, Papua", "lat": -2.5339, "lng": 140.7181, "operator": "PT Papua Marine", "capacity": "6 ha"},
    {"id": 10, "name": "Banyuwangi Shrimp Center", "location": "Banyuwangi, East Java", "lat": -8.2194, "lng": 114.3691, "operator": "CV Jawa Timur Makmur", "capacity": "16 ha"},
]

# Initialize farms with realistic base values
for f in FARMS:
    # Some farms have higher base contamination (near industrial areas)
    if "Jakarta" in f["location"] or "Lampung" in f["location"]:
        base = round(random.uniform(40, 75), 2)  # Higher risk areas
    else:
        base = round(random.uniform(12, 45), 2)  # Normal risk
    
    f["history"] = make_history(base, days=14)  # 2 weeks history
    f["value"] = f["history"][-1]["value"]
    f["value_bq"] = ppb_to_bq(f["value"])
    
    # Status classification
    if f["value"] >= THRESHOLD_CRITICAL:
        f["status"] = "Critical"
    elif f["value"] >= THRESHOLD_HIGH:
        f["status"] = "High"
    elif f["value"] >= THRESHOLD_MEDIUM:
        f["status"] = "Medium"
    else:
        f["status"] = "Safe"
    
    f["lastUpdate"] = f["history"][-1]["time"]
    f["certifications"] = random.choice([
        ["HACCP", "BAP"],
        ["HACCP"],
        ["BAP", "CBIB"],
        ["HACCP", "BAP", "CBIB"]
    ])
    f["export_ready"] = f["status"] in ["Safe", "Medium"]

# -----------------------
# AUTH + HELPER FUNCTIONS
# -----------------------
USERS = {
    "admin": {
        "password": "secureadmin",
        "role": "admin",
        "name": "National Control Center",
        "team": "Cesium Guard Core"
    },
    "inspector": {
        "password": "fieldops",
        "role": "field",
        "name": "Lapangan Inspector",
        "team": "Mobile Rapid Response"
    }
}

TOKENS = {}

def get_status(value):
    """Determine contamination status based on ppb value"""
    if value >= THRESHOLD_CRITICAL:
        return "Critical"
    elif value >= THRESHOLD_HIGH:
        return "High"
    elif value >= THRESHOLD_MEDIUM:
        return "Medium"
    return "Safe"

def compute_zone_aggregation():
    """
    Aggregate farms by geographic zones
    Returns zone statistics including avg contamination, severity, recommended radius
    """
    zone_values = {k: [] for k in ZONES_META.keys()}
    zone_farms = {k: [] for k in ZONES_META.keys()}

    # Assign farms to nearest zone
    for f in FARMS:
        lat, lng = f["lat"], f["lng"]
        best = None
        bestd = 1e9
        for zid, meta in ZONES_META.items():
            cy, cx = meta["center"]
            d = (cy - lat)**2 + (cx - lng)**2
            if d < bestd:
                bestd = d
                best = zid
        zone_values[best].append(f["value"])
        zone_farms[best].append(f)

    zones_out = []
    for zid, meta in ZONES_META.items():
        vals = zone_values[zid]
        avg_val = round(statistics.mean(vals), 2) if vals else 0
        severity = get_status(avg_val)
        
        # Dynamic radius based on contamination severity
        # Critical: 140km, High: 80km, Medium: 50km, Safe: 30km
        radius_map = {"Critical": 140000, "High": 80000, "Medium": 50000, "Safe": 30000}
        radius = radius_map.get(severity, 30000)
        
        # Find top contaminated farm in zone
        top_farm = None
        export_ready_count = 0
        if zone_farms[zid]:
            top_farm = max(zone_farms[zid], key=lambda x: x["value"])
            export_ready_count = sum(1 for f in zone_farms[zid] if f["export_ready"])
        
        zones_out.append({
            "id": zid,
            "name": meta["name"],
            "center": meta["center"],
            "avg": avg_val,
            "avg_bq": ppb_to_bq(avg_val),
            "severity": severity,
            "radius_m": radius,
            "top_farm": {
                "id": top_farm["id"], 
                "name": top_farm["name"], 
                "value": top_farm["value"],
                "value_bq": top_farm["value_bq"]
            } if top_farm else None,
            "count_farms": len(zone_farms[zid]),
            "export_ready": export_ready_count
        })
    
    return sorted(zones_out, key=lambda x: x["avg"], reverse=True)

def agg_stats():
    """Calculate comprehensive dashboard statistics"""
    vals = [f["value"] for f in FARMS]
    if not vals:
        return {"total": 0, "avg": 0, "max": 0, "min": 0}
    
    total = len(FARMS)
    avgv = round(sum(vals) / len(vals), 2)
    
    # Count by status
    critical = sum(1 for v in vals if v >= THRESHOLD_CRITICAL)
    high = sum(1 for v in vals if THRESHOLD_HIGH <= v < THRESHOLD_CRITICAL)
    medium = sum(1 for v in vals if THRESHOLD_MEDIUM <= v < THRESHOLD_HIGH)
    safe = sum(1 for v in vals if v < THRESHOLD_MEDIUM)
    
    # Top hotspots
    top_hotspots = sorted([
        {
            "id": f["id"], 
            "name": f["name"], 
            "location": f["location"],
            "value": f["value"],
            "value_bq": f["value_bq"],
            "status": f["status"]
        } for f in FARMS
    ], key=lambda x: x["value"], reverse=True)[:5]
    
    # Timeseries: average across all farms for each day
    days = len(FARMS[0]["history"]) if FARMS else 0
    timeseries = []
    for i in range(days):
        vals_day = [f["history"][i]["value"] if i < len(f["history"]) else f["value"] for f in FARMS]
        date_obj = now - timedelta(days=days-i-1)
        timeseries.append({
            "t": date_obj.date().isoformat(),
            "v": round(statistics.mean(vals_day), 2),
            "label": date_obj.strftime("%d %b")
        })
    
    # Export readiness
    export_ready = sum(1 for f in FARMS if f["export_ready"])
    
    # FDA compliance check
    fda_compliant = sum(1 for f in FARMS if f["value_bq"] < FDA_INTERVENTION_LEVEL)
    
    return {
        "total": total,
        "avg": avgv,
        "avg_bq": ppb_to_bq(avgv),
        "max": max(vals),
        "min": min(vals),
        "critical": critical,
        "high": high,
        "medium": medium,
        "safe": safe,
        "export_ready": export_ready,
        "fda_compliant": fda_compliant,
        "top_hotspots": top_hotspots,
        "timeseries": timeseries
    }

def compute_intel():
    """Generate higher-level insights for the dashboard action center"""
    now_utc = datetime.utcnow()
    stats = agg_stats()
    zones = compute_zone_aggregation()

    overdue = 0
    for f in FARMS:
        last = f.get("lastUpdate")
        try:
            last_dt = datetime.fromisoformat(last) if last else now_utc
        except ValueError:
            last_dt = now_utc
        if now_utc - last_dt > timedelta(hours=36):
            overdue += 1

    high_alert_zones = [z for z in zones if z["severity"] in ("High", "Critical")]
    priority_zones = []
    for z in high_alert_zones[:3]:
        action = "Deploy task force & lock exports" if z["severity"] == "Critical" else "Schedule intensified sampling"
        priority_zones.append({
            "name": z["name"],
            "severity": z["severity"],
            "avg": z["avg"],
            "count": z["count_farms"],
            "action": action
        })

    timeseries = stats.get("timeseries", [])
    if len(timeseries) >= 2:
        delta = round(timeseries[-1]["v"] - timeseries[-2]["v"], 2)
        projection = round(timeseries[-1]["v"] + delta, 2)
    elif timeseries:
        delta = 0
        projection = timeseries[-1]["v"]
    else:
        delta = 0
        projection = stats["avg"]

    signal = "stable"
    if delta > 1.5:
        signal = "rising"
    elif delta < -1.5:
        signal = "falling"

    export_gateways = [
        {
            "name": "Tanjung Priok",
            "status": "Surveillance" if stats["critical"] else "Normal",
            "risk": "High" if stats["critical"] > 2 else ("Medium" if stats["high"] > 1 else "Low"),
            "throughput": "52 shipments / week"
        },
        {
            "name": "Belawan Medan",
            "status": "Heightened sampling" if stats["high"] else "Normal",
            "risk": "Medium" if stats["high"] else "Low",
            "throughput": "31 shipments / week"
        },
        {
            "name": "Makassar Port",
            "status": "Normal",
            "risk": "Low",
            "throughput": "18 shipments / week"
        }
    ]

    playbooks = [
        {
            "title": "North Java cold-chain sweep",
            "owner": "HQ Compliance",
            "status": "Green-lit",
            "impact": "Verifies 12 processors before FDA inspection",
            "cta": "Dispatch mobile XRF lab"
        },
        {
            "title": "Delta remediation kit",
            "owner": "Field Ops",
            "status": "Queued",
            "impact": "Deploy activated carbon treatment to critical ponds",
            "cta": "Ship supplies via Surabaya hub"
        },
        {
            "title": "Exporter confidence briefing",
            "owner": "Trade Desk",
            "status": "Drafting",
            "impact": "Brief US buyers on containment steps & compliance metrics",
            "cta": "Attach latest Cesium Guard export JSON"
        }
    ]

    return {
        "last_refresh": now_utc.isoformat(),
        "sampling_backlog": overdue,
        "pending_samples": stats["high"] + stats["critical"],
        "sla_hours": 24,
        "sla_pressure": round((overdue / stats["total"]) * 100, 1) if stats["total"] else 0,
        "ai_projection": {
            "next_avg": projection,
            "delta": delta,
            "signal": signal,
            "confidence": 0.74
        },
        "priority_zones": priority_zones,
        "export_gateways": export_gateways,
        "playbooks": playbooks
    }

def generate_token(username):
    token = str(uuid4())
    TOKENS[token] = {
        "username": username,
        "issued_at": datetime.utcnow(),
        "role": USERS[username]["role"],
        "name": USERS[username]["name"],
        "team": USERS[username]["team"]
    }
    return token

def get_user_from_request():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        return TOKENS.get(token)
    return None

def require_role(allowed=None):
    """
    Decorator-like helper for role protected endpoints.
    allowed: list or None (means any authenticated)
    """
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            user = get_user_from_request()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            if allowed and user["role"] not in allowed:
                return jsonify({"error": "Forbidden"}), 403
            request.current_user = user
            return func(*args, **kwargs)
        return inner
    return wrapper

# -----------------------
# API ENDPOINTS
# -----------------------
@app.route("/")
def root():
    """Serve the main HTML page"""
    try:
        return send_from_directory('.', 'index.html')
    except:
        return jsonify({
            "status": "Cesium Guard API Running",
            "version": "2.0",
            "endpoints": ["/api/farms", "/api/zones", "/api/stats", "/api/heatmap", "/api/samples", "/api/simulate"]
        })

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").lower()
    password = data.get("password", "")
    if username not in USERS or USERS[username]["password"] != password:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    token = generate_token(username)
    profile = {
        "username": username,
        "role": USERS[username]["role"],
        "name": USERS[username]["name"],
        "team": USERS[username]["team"]
    }
    return jsonify({"success": True, "token": token, "profile": profile})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        TOKENS.pop(token, None)
    return jsonify({"success": True})

@app.route("/api/me", methods=["GET"])
def api_me():
    user = get_user_from_request()
    if not user:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "profile": user})

@app.route("/api/farms", methods=["GET"])
def api_farms():
    """Get all farms with current contamination data"""
    # Optional filtering
    status_filter = request.args.get('status')
    zone_filter = request.args.get('zone')
    
    farms_filtered = FARMS
    
    if status_filter:
        farms_filtered = [f for f in farms_filtered if f["status"].lower() == status_filter.lower()]

    if zone_filter:
        zone = zone_filter.lower()
        center = ZONES_META.get(zone)
        if center:
            cy, cx = center["center"]
            farms_filtered = [
                f for f in farms_filtered
                if abs(f["lat"] - cy) < 8 and abs(f["lng"] - cx) < 8
            ]
    
    return jsonify(farms_filtered)

@app.route("/api/farm/<int:farm_id>", methods=["GET"])
def api_farm_detail(farm_id):
    """Get detailed info for specific farm"""
    farm = next((f for f in FARMS if f["id"] == farm_id), None)
    if not farm:
        return jsonify({"error": "Farm not found"}), 404
    
    # Add additional analytics
    history_vals = [h["value"] for h in farm["history"]]
    farm_detail = farm.copy()
    farm_detail["analytics"] = {
        "trend": "increasing" if history_vals[-1] > history_vals[0] else "decreasing",
        "volatility": round(statistics.stdev(history_vals), 2) if len(history_vals) > 1 else 0,
        "avg_last_7days": round(statistics.mean(history_vals[-7:]), 2),
        "peak": max(history_vals),
        "lowest": min(history_vals)
    }
    
    return jsonify(farm_detail)

@app.route("/api/zones", methods=["GET"])
def api_zones():
    """Get aggregated zone data"""
    return jsonify(compute_zone_aggregation())

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Get dashboard statistics"""
    s = agg_stats()
    
    # Add recent field activities (demo)
    s["recent_activities"] = [
        {
            "type": "inspection",
            "location": "Jakarta Bay Aquaculture",
            "time": (now - timedelta(hours=2)).strftime("%d %b %Y %H:%M"),
            "result": "Sample collected - pending analysis"
        },
        {
            "type": "certification",
            "location": "Lampung Export Shrimp", 
            "time": (now - timedelta(days=1)).strftime("%d %b %Y %H:%M"),
            "result": "HACCP renewal approved"
        },
        {
            "type": "alert",
            "location": "Surabaya Delta Farm",
            "time": (now - timedelta(days=2)).strftime("%d %b %Y %H:%M"),
            "result": "Elevated readings detected"
        }
    ]
    
    # Add compliance metrics
    s["compliance"] = {
        "fda_standard": FDA_INTERVENTION_LEVEL,
        "indonesia_standard": 500,  # Bq/kg
        "compliant_farms": s["fda_compliant"],
        "compliance_rate": round((s["fda_compliant"] / s["total"]) * 100, 1) if s["total"] > 0 else 0
    }
    
    s["recent_trips"] = [
        {"location": "Makassar Premium Shrimp", "time": (now - timedelta(hours=5)).strftime("%d %b %Y %H:%M")},
        {"location": "Padang Coastal Shrimp Farm", "time": (now - timedelta(hours=12)).strftime("%d %b %Y %H:%M")},
        {"location": "Banyuwangi Shrimp Center", "time": (now - timedelta(days=1)).strftime("%d %b %Y %H:%M")}
    ]

    s["risk_matrix"] = {
        "safe_pct": round((s["safe"] / s["total"]) * 100, 1) if s["total"] else 0,
        "medium_pct": round((s["medium"] / s["total"]) * 100, 1) if s["total"] else 0,
        "high_pct": round((s["high"] / s["total"]) * 100, 1) if s["total"] else 0,
        "critical_pct": round((s["critical"] / s["total"]) * 100, 1) if s["total"] else 0,
        "priority_actions": [
            "Sinkronisasi data lab ke gudang pusat setiap 6 jam",
            "Prioritaskan inspeksi di zona Critical lebih dari 48 jam",
            "Aktifkan simulasi untuk stress-test rantai pasok"
        ]
    }

    return jsonify(s)

@app.route("/api/heatmap", methods=["GET"])
def api_heatmap():
    """Get heatmap data points"""
    points = [[f["lat"], f["lng"], max(0.1, f["value"]/10)] for f in FARMS]
    return jsonify({"points": points})

@app.route("/api/samples", methods=["POST"])
@require_role(allowed=["admin", "field"])
def api_samples():
    """Submit new contamination sample"""
    data = request.get_json() or {}
    farm_id = data.get("farm_id")
    value = data.get("value")
    inspector = data.get("inspector", "Unknown")
    notes = data.get("notes", "")
    
    if farm_id is None or value is None:
        return jsonify({"success": False, "error": "Missing required fields: farm_id and value"}), 400
    
    farm = next((f for f in FARMS if f["id"] == farm_id), None)
    if not farm:
        return jsonify({"success": False, "error": "Farm not found"}), 404
    
    # Validate value
    try:
        value = float(value)
        if value < 0:
            return jsonify({"success": False, "error": "Value cannot be negative"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid value format"}), 400
    
    # Add sample to history
    nowiso = datetime.utcnow().isoformat()
    farm.setdefault("history", []).append({
        "time": nowiso,
        "inspector": inspector,
        "value": value,
        "notes": notes
    })
    
    # Update current values
    farm["value"] = value
    farm["value_bq"] = ppb_to_bq(value)
    farm["status"] = get_status(value)
    farm["lastUpdate"] = nowiso
    farm["export_ready"] = farm["status"] in ["Safe", "Medium"]
    
    return jsonify({
        "success": True,
        "message": "Sample recorded successfully",
        "farm": farm,
        "alert": "⚠️ CRITICAL LEVEL DETECTED!" if farm["status"] == "Critical" else None
    })

@app.route("/api/simulate", methods=["GET"])
@require_role(allowed=["admin"])
def api_simulate():
    """Simulate random contamination changes for demo"""
    for f in FARMS:
        change = random.uniform(-8, 10)
        newv = round(max(0, f["value"] + change), 2)
        
        f.setdefault("history", []).append({
            "time": datetime.utcnow().isoformat(),
            "inspector": "auto-sim",
            "value": newv,
            "notes": "Simulated data"
        })
        
        f["value"] = newv
        f["value_bq"] = ppb_to_bq(newv)
        f["status"] = get_status(newv)
        f["lastUpdate"] = f["history"][-1]["time"]
        f["export_ready"] = f["status"] in ["Safe", "Medium"]
    
    return jsonify({"success": True, "message": "Simulation completed", "timestamp": datetime.utcnow().isoformat()})

@app.route("/api/export", methods=["GET"])
@require_role(allowed=["admin"])
def api_export():
    """Export data in JSON format for reporting"""
    export_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": agg_stats(),
        "zones": compute_zone_aggregation(),
        "farms": FARMS,
        "thresholds": {
            "critical": THRESHOLD_CRITICAL,
            "high": THRESHOLD_HIGH,
            "medium": THRESHOLD_MEDIUM,
            "fda_intervention": FDA_INTERVENTION_LEVEL
        }
    }
    return jsonify(export_data)

@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    """Get active alerts for critical contamination"""
    alerts = []
    for f in FARMS:
        if f["status"] == "Critical":
            alerts.append({
                "severity": "critical",
                "farm_id": f["id"],
                "farm_name": f["name"],
                "location": f["location"],
                "value": f["value"],
                "value_bq": f["value_bq"],
                "message": f"⚠️ CRITICAL: {f['name']} exceeds safe threshold",
                "timestamp": f["lastUpdate"],
                "action_required": "Immediate inspection and export suspension recommended"
            })
        elif f["status"] == "High":
            alerts.append({
                "severity": "warning",
                "farm_id": f["id"],
                "farm_name": f["name"],
                "location": f["location"],
                "value": f["value"],
                "value_bq": f["value_bq"],
                "message": f"⚡ HIGH RISK: {f['name']} approaching critical levels",
                "timestamp": f["lastUpdate"],
                "action_required": "Enhanced monitoring required"
            })
    
    return jsonify({"alerts": sorted(alerts, key=lambda x: x["value"], reverse=True), "count": len(alerts)})

@app.route("/api/intel", methods=["GET"])
def api_intel():
    """Serve synthesized insights for the action center"""
    return jsonify(compute_intel())

# -----------------------
# ERROR HANDLERS
# -----------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# -----------------------
# RUN SERVER
# -----------------------
if __name__ == "__main__":
    print("=" * 60)
    print("🦐 CESIUM GUARD - Shrimp Contamination Monitoring System")
    print("=" * 60)
    print(f"📊 Loaded {len(FARMS)} farms across {len(ZONES_META)} zones")
    print(f"🌐 Server starting at: http://127.0.0.1:5000")
    print(f"📡 API endpoints available at: http://127.0.0.1:5000/api/")
    print("=" * 60)
    print("\nPress CTRL+C to stop\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
