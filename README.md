# Cesium Guard

**Traceability intelligence console for cesium-safe shrimp exports.**

Built for **RISTEK Mini Hackathon 2025**, Cesium Guard helps pemerintah, eksportir, dan tim lapangan memantau kontaminasi Cs‑137 secara real time, menetapkan prioritas sampling, dan menjaga kepercayaan buyer global.

---

## 1. Problem Snapshot

- Agustus 2025: FDA USA mendeteksi **68 Bq/kg** Cs‑137 pada udang beku asal Indonesia (batas intervensi 1.200 Bq/kg).
- Dampak utama:
  - Recall massal (Walmart, Kroger, dll) dan kerugian ratusan juta USD.
  - >500 kontainer ditahan, 36‑40% nilai ekspor perikanan ikut terancam.
  - Reputasi supply chain (petambak, eksportir, regulator) menurun.
- **Akar masalah:** traceability masih manual & terfragmentasi, sehingga inspeksi lambat, sulit menentukan prioritas zona, dan tidak ada alat simulasi untuk menilai risiko.

---

## 2. Solution Overview

Cesium Guard menghadirkan **console berbasis web** yang memadukan peta interaktif, intelijen zona, dan workflow berbasis peran:

| Modul | Highlights |
|-------|------------|
| Interactive Map | 27 tambak + heatmap, radius risiko per zona pesisir, riwayat sampling. |
| Zone Intelligence | 13 coastal regions dengan severity dinamis, average ppb, dan top farm. |
| Dashboard | Totals, distribution, timeseries trend, top hotspots, compliance snapshot. |
| Action Center | Untuk admin: AI projection, zona prioritas, status gateway ekspor, tombol simulate/export JSON. |
| Field Missions | Untuk inspector: daftar lokasi sampling, SLA backlog, sampling queue (farms overdue >36 jam). |
| Sampling Form | Tambah sampel baru (ppb + inspector + catatan) dengan audit trail otomatis. |
| Simulation Engine | Mean-reversion per zona → hasil lebih realistis, tidak langsung “semua merah”. |

**Demo login**
```
Admin     : admin / secureadmin
Inspector : inspector / fieldops
```

---

## 3. Architecture & Tech Stack

- **Frontend:** React 18 (hooks), Tailwind CSS, Leaflet + Leaflet.heat, Chart.js.
- **Backend:** Python 3 + Flask, Flask-CORS, in-memory data seeds (siap di-port ke PostgreSQL/MongoDB).
- **APIs:** REST/JSON, polling periodik (12 detik) untuk sensasi live feed.
- **Auth:** Lightweight token store (admin vs field) untuk membatasi simulasi, ekspor, dan sampling form.

```
cesium-guard-mvp/
├── app.py           # Flask app, data seeds, role-based endpoints
├── index.html       # React UI (served via Flask send_from_directory)
├── requirements.txt # python -r dependencies
└── README.md        # this file
```

---

## 4. Getting Started

```bash
# 1. clone & enter repo
git clone https://github.com/YOUR-USERNAME/cesium-guard-mvp.git
cd cesium-guard-mvp

# 2. install deps
pip install -r requirements.txt

# 3. run dev server (auto-reload on)
python app.py

# 4. open dashboard
open http://127.0.0.1:5000
```

> **Tip:** gunakan akun demo di atas untuk mencoba peran admin dan field inspector.

---

## 5. API Reference (summary)

| Method | Endpoint        | Description |
|--------|-----------------|-------------|
| GET    | `/api/farms`    | List tambak (support query `status`, `zone`). |
| GET    | `/api/farm/<id>`| Detail + analytics + history. |
| GET    | `/api/zones`    | Aggregasi zona (center, avg, severity, radius, top farm). |
| GET    | `/api/stats`    | Dashboard metrics, compliance snapshot, timeseries. |
| GET    | `/api/heatmap`  | Points + intensitas untuk layer heatmap. |
| GET    | `/api/intel`    | Action intel: AI projection, priority zones, gateways, sampling queue. |
| POST   | `/api/samples`  | Tambah sampel baru (role: admin/field). |
| GET    | `/api/simulate` | Jalankan simulasi (role: admin). |
| GET    | `/api/export`   | Export JSON summary (role: admin). |
| POST   | `/api/login`    | Auth → token + profile. |
| POST   | `/api/logout`   | Invalidate token. |

Sample request:

```javascript
await fetch('/api/samples', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    farm_id: 8,
    value: 42.3,
    inspector: 'Budi Santoso',
    notes: 'Sampling ulang karena alert high'
  })
});
```

---

## 6. Data Model (simplified)

```python
Farm = {
  "id": int,
  "name": str,
  "location": str,
  "lat": float,
  "lng": float,
  "value": float,          # current ppb
  "status": "Safe|Medium|High|Critical",
  "history": [
    {"time": iso8601, "inspector": str, "value": float, "notes": str}
  ],
  "lastUpdate": iso8601,
  "export_ready": bool
}

Zone = {
  "id": str,
  "name": str,
  "center": [lat, lng],     # center for overlay
  "avg": float,
  "severity": str,
  "radius_m": int,
  "count_farms": int,
  "top_farm": {"id": int, "name": str, "value": float}
}
```

---

## 7. Role Workflows

### Admin Command Center
1. Login → dashboard menampilkan Action Center (AI projection, priority zones, export gateways).
2. Gunakan tombol **Simulate** untuk stress-test rantai pasok, atau **Download compliance JSON** untuk briefing regulator/importer.
3. Pantau kartu **Sampling SLA** & **Sampling Queue** untuk memutuskan dispatch tim lapangan.

### Field Inspector Console
1. Login sebagai `inspector` → melihat Field Missions + Field Toolkit.
2. Ikuti daftar prioritas sampling (otomatis diambil dari priority zones/top hotspots).
3. Input hasil sampling via form (farm, nilai ppb, inspector, catatan) → dashboard langsung update.

---

## 8. Hackathon Scoring Alignment

| Kriteria | Bobot | Implementasi |
|----------|-------|--------------|
| Problem Solving & Relevansi | 25% | Address real Cs‑137 incident (data 2025), memetakan akar masalah traceability. |
| Fungsionalitas MVP | 25% | 10+ API routes, role-based auth, simulasi, heatmap, sampling workflow, export JSON. |
| Inovasi & Kreativitas | 20% | Action Center, AI projection, sampling SLA, adaptive zone radius, command/field experiences. |
| Technical Execution | 10% | Flask + React hooks, modular helpers, mean-reversion simulation, per-zone analytics. |
| Impact & Scalability | 10% | Mudah dipindah ke DB/cloud, siap integrasi IoT sensors, output compliance-ready JSON. |
| Design | 5% | Dark mode, responsive layout, clear typography, role-based UI states. |
| Proposal/Docs | 5% | README ini + konteks insiden + API table mempermudah juri memahami solusi. |

---

## 9. Roadmap Ide Lanjutan

- [ ] Persistensi production (PostgreSQL / Supabase) + historisasi lengkap.
- [ ] Device auth + granular permissions (HQ, Provinsi, Field).
- [ ] Edge IoT integration (sensor Cs‑137 / turbidity / pH) untuk auto-sampling.
- [ ] Predictive analytics (LSTM/Prophet) untuk forecasting zona rawan.
- [ ] Multi-language UI (EN/ID) + offline-ready PWA.
- [ ] PDF/Excel compliance pack & auto-email untuk buyer/regulator.

---

## 10. Tim

- **Ahmad Hoesin** 
- **Dionisius Bennett Andrianto** 
- **Goran Adriano Tamrella** 
- **Gavrila Kartika Sarah Suoth** 
- **William Jesiel** 

---

## 11. License & Credits

Developed exclusively for **RISTEK Mini Hackathon 2025 – Universitas Indonesia**.  
🦐 Built with 💙 to protect Indonesian shrimp farmers, exporters, and coastal communities.

> *Menjaga kualitas ekspor, memulihkan reputasi Indonesia di pasar global.*
