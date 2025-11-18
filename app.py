from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Sample data - Indonesian shrimp farms
farms = [
    {
        "id": 1,
        "name": "Tambak Udang Indramayu A",
        "lat": -6.3266,
        "lng": 108.3199,
        "value": 15,
        "status": "Safe",
        "location": "Indramayu, Jawa Barat",
        "history": [
            {"value": 15, "time": "2025-11-10T08:00:00", "inspector": "Ahmad"}
        ]
    },
    {
        "id": 2,
        "name": "Tambak Udang Situbondo B",
        "lat": -7.7063,
        "lng": 114.0095,
        "value": 45,
        "status": "Medium",
        "location": "Situbondo, Jawa Timur",
        "history": [
            {"value": 45, "time": "2025-11-12T10:30:00", "inspector": "Budi"}
        ]
    },
    {
        "id": 3,
        "name": "Tambak Udang Lampung C",
        "lat": -5.4292,
        "lng": 105.2619,
        "value": 65,
        "status": "High",
        "location": "Lampung",
        "history": [
            {"value": 65, "time": "2025-11-15T14:20:00", "inspector": "Siti"}
        ]
    },
    {
        "id": 4,
        "name": "Tambak Udang Cirebon D",
        "lat": -6.7063,
        "lng": 108.5571,
        "value": 12,
        "status": "Safe",
        "location": "Cirebon, Jawa Barat",
        "history": [
            {"value": 12, "time": "2025-11-11T09:15:00", "inspector": "Dewi"}
        ]
    },
    {
        "id": 5,
        "name": "Tambak Udang Banyuwangi E",
        "lat": -8.2194,
        "lng": 114.3691,
        "value": 72,
        "status": "High",
        "location": "Banyuwangi, Jawa Timur",
        "history": [
            {"value": 72, "time": "2025-11-16T11:45:00", "inspector": "Eko"}
        ]
    }
]

HIGH_THRESHOLD = 50
MEDIUM_THRESHOLD = 30

def get_status(value):
    """AI-based risk classification"""
    if value >= HIGH_THRESHOLD:
        return "High"
    elif value >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Safe"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/farms', methods=['GET'])
def get_farms():
    """Get all farms with current status"""
    return jsonify(farms)

@app.route('/api/sample', methods=['POST'])
def add_sample():
    """Add new contamination sample"""
    data = request.json
    farm_id = data.get("farm_id")
    value = data.get("value")
    inspector = data.get("inspector", "Unknown")

    if not farm_id or value is None:
        return jsonify({"error": "Missing farm_id or value"}), 400

    for farm in farms:
        if farm["id"] == farm_id:
            farm["value"] = float(value)
            farm["status"] = get_status(float(value))
            farm["history"].append({
                "value": float(value),
                "time": datetime.now().isoformat(),
                "inspector": inspector
            })
            return jsonify({
                "success": True,
                "message": "Sample added successfully",
                "farm": farm
            })
    
    return jsonify({"error": "Farm not found"}), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    total = len(farms)
    high_risk = sum(1 for f in farms if f["status"] == "High")
    medium_risk = sum(1 for f in farms if f["status"] == "Medium")
    safe = sum(1 for f in farms if f["status"] == "Safe")
    
    return jsonify({
        "total_farms": total,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "safe": safe,
        "avg_cesium": round(sum(f["value"] for f in farms) / total, 2)
    })

if __name__ == "__main__":
    print("🦐 Cesium Guard MVP Starting...")
    print("📍 Open browser: http://localhost:5000")
    app.run(debug=True, port=5000)