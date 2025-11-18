# Cesium Guard

Real-time monitoring system untuk tracking kontaminasi Cesium-137 di tambak udang Indonesia.

**RISTEK Mini Hackathon 2025**

## Latar Belakang

Agustus 2025, FDA Amerika Serikat mendeteksi kontaminasi Cesium-137 (Cs-137) pada udang beku dari Indonesia dengan level 68 Bq/kg. Meskipun masih di bawah batas intervensi FDA (1.200 Bq/kg), insiden ini:

- Menyebabkan recall massal di Walmart, Kroger, dan retailer besar lainnya
- Mengakibatkan kerugian ratusan juta dollar per tahun
- Menurunkan kepercayaan pasar internasional terhadap produk perikanan Indonesia
- Mengancam 36-40% total nilai ekspor perikanan nasional

**Masalah utama:** Sistem traceability dan quality control yang masih manual, lambat, dan fragmentasi—sehingga sulit mengidentifikasi sumber kontaminasi dengan cepat dan akurat.

## Solusi Kami

**Cesium Guard** adalah platform monitoring real-time berbasis AI yang menyediakan:

### Fitur Utama

**Interactive Geographic Map**
- Visualisasi lokasi tambak udang across Indonesia (Sumatra, Java, Kalimantan, Sulawesi, Papua)
- Color-coded markers (Safe/Medium/High/Critical) berdasarkan level kontaminasi
- Heatmap overlay untuk identifikasi hotspot area

**Zone-Based Risk Analysis**
- Aggregasi data per zona geografis dengan circular risk radius
- Automatic severity classification
- Top hotspots identification per region

**Real-Time Dashboard**
- Live statistics (total farms, avg contamination, risk distribution)
- Historical trend analysis dengan timeseries chart
- Top 5 contaminated farms ranking

**AI-Powered Classification**
- Automatic risk assessment based on Cs-137 levels:
  - Safe: < 30 ppb
  - Medium: 30-44 ppb
  - High: 45-59 ppb
  - Critical: ≥ 60 ppb
- Predictive alerts untuk early detection

**Sample Tracking System**
- Submit new contamination samples dengan inspector tracking
- Complete history untuk every farm
- Audit trail lengkap untuk compliance

**Live Simulation Mode**
- Test scenario dengan simulated data updates
- Demo untuk stakeholder presentation

## Tech Stack

**Backend:**
- Python 3.x + Flask
- Flask-CORS untuk cross-origin requests
- In-memory data store (scalable ke PostgreSQL/MongoDB)

**Frontend:**
- React 18 (functional components + hooks)
- Tailwind CSS untuk modern UI
- Leaflet.js + Leaflet Heat untuk maps & heatmaps
- Chart.js untuk data visualization

**APIs:**
- RESTful architecture
- JSON data format
- Real-time data polling

## Installation

### Prerequisites
```bash
python3 --version  # Python 3.7+
pip --version
```

### Setup

1. Clone repository
```bash
git clone https://github.com/YOUR-USERNAME/cesium-guard-mvp.git
cd cesium-guard-mvp
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run backend server
```bash
python app.py
```

4. Open browser
```
http://127.0.0.1:5000
```

Server akan running di port 5000 dengan auto-reload enabled.

## API Documentation

### Endpoints

**GET `/api/farms`**
- Returns: List semua farms dengan current contamination status
- Response: `[{id, name, location, lat, lng, value, status, history, lastUpdate}]`

**GET `/api/zones`**
- Returns: Aggregated data per geographic zone
- Response: `[{id, name, center, avg, severity, radius_m, top_farm, count_farms}]`

**GET `/api/stats`**
- Returns: Dashboard statistics dan trends
- Response: `{total, avg, max, min, high, medium, safe, top_hotspots, timeseries, recent_trips}`

**GET `/api/heatmap`**
- Returns: Heatmap points untuk visualization
- Response: `{points: [[lat, lng, intensity]]}`

**POST `/api/samples`**
- Body: `{farm_id: int, value: float, inspector: string}`
- Returns: `{success: bool, farm: object}` or `{error: string}`

**GET `/api/simulate`**
- Simulates random contamination changes
- Returns: `{success: bool}`

### Sample Request

```javascript
// Add new sample
fetch('http://127.0.0.1:5000/api/samples', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    farm_id: 1,
    value: 45.5,
    inspector: "Budi Santoso"
  })
})
```

## Project Structure

```
cesium-guard-mvp/
├── app.py              # Flask backend + API routes
├── index.html          # React frontend application
├── README.md           # Documentation
└── requirements.txt    # Python dependencies
```

## Data Model

### Farm Object
```python
{
  "id": int,
  "name": string,
  "location": string,
  "lat": float,
  "lng": float,
  "value": float,        # Current Cs-137 level (ppb)
  "status": string,      # Safe|Medium|High|Critical
  "history": [           # Sample history
    {
      "time": ISO8601,
      "inspector": string,
      "value": float
    }
  ],
  "lastUpdate": ISO8601
}
```

### Zone Object
```python
{
  "id": string,
  "name": string,
  "center": [lat, lng],
  "avg": float,          # Average contamination
  "severity": string,
  "radius_m": int,       # Risk zone radius
  "top_farm": object,    # Highest contaminated farm
  "count_farms": int
}
```

## Usage Guide

### For Regular Users

1. **View Map Status**
   - Open application
   - Check color-coded markers on map
   - Click markers untuk detailed farm info

2. **Add New Sample**
   - Select farm dari dropdown
   - Enter Cs-137 measurement (ppb)
   - Input inspector name
   - Submit

3. **Monitor Trends**
   - Check dashboard statistics
   - Review timeseries chart
   - Identify top hotspots

### For Admins

1. **Live Simulation**
   - Click "Simulate" button untuk test scenarios
   - Data akan random update across all farms

2. **Export & Compliance**
   - All data accessible via API
   - Complete audit trail tersedia
   - History tracking untuk regulatory compliance

## Scoring Criteria Alignment

| Kriteria | Bobot | Implementasi |
|----------|-------|--------------|
| **Problem Solving & Relevance** | 25% |  Mengatasi real case kontaminasi Cs-137 yang baru terjadi Agustus 2025 |
| **MVP Functionality** | 25% |  Fully functional dengan 6 API endpoints, real-time updates, complete CRUD |
| **Innovation & Creativity** | 20% | AI classification, zone aggregation, heatmap, predictive analysis |
| **Technical Execution** | 10% |  Clean architecture, RESTful API, React hooks, responsive design |
| **Impact & Scalability** | 10% |  Dapat di-scale ke ribuan farms, add database layer, integrate IoT sensors |
| **Design** | 5% |  Modern dark theme UI, intuitive UX, professional visualization |
| **Proposal** | 5% | Complete documentation dengan real case study |

## Real-World Impact

Based on actual 2025 incident:
- **68 Bq/kg detected** vs **1,200 Bq/kg FDA limit** → Our system detects below danger levels
- **500+ containers rejected** → Early detection prevents massive losses
- **$477M export value at risk** → Traceability maintains international trust
- **9 workers exposed in Cikande** → Zone monitoring protects communities

## Future Enhancements

- [ ] PostgreSQL database integration
- [ ] User authentication & role management
- [ ] Mobile app (iOS/Android)
- [ ] IoT sensor integration untuk automatic sampling
- [ ] Machine learning predictions
- [ ] Export compliance reporting (PDF/Excel)
- [ ] Multi-language support (EN/ID)
- [ ] Email/SMS alerts untuk critical levels
- [ ] Integration dengan MFQAA certification system

## Team

- **Ahmad Hoesin** 
- **Dionisius Bennett Andrianto** 
- **Goran Adriano Tamrella** 
- **Gavrila Kartika Sarah Suoth** 
- **William Jesiel** 

## References

- [FDA Response to Cs-137 Contamination](https://www.fda.gov/food/environmental-contaminants-food/fda-response-imported-foods-potentially-contaminated-cesium-137)
- [Indonesia Ministry of Food - Cs-137 Task Force Report](https://tempo.co)
- [IPB University Expert Analysis on Shrimp Safety](https://www.ipb.ac.id/news)

## License

Developed for RISTEK Mini Hackathon 2025 - Universitas Indonesia

---

**Built with 💙 for Indonesian shrimp farmers and exporters**

*Menjaga kualitas ekspor, melindungi reputasi Indonesia di pasar global.*
