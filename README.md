# Cesium Guard

Monitoring system buat ngecek kontaminasi cesium di tambak udang. Dibuat untuk RISTEK Mini Hackathon 2025.

## Kenapa bikin ini?

Indonesia kan eksportir udang gede, tapi beberapa waktu lalu ada kasus penolakan ekspor gara-gara kontaminasi cesium. Rugi banget. Masalahnya sistem tracking yang ada sekarang masih manual dan lambat banget.

## Apa yang kita bikin?

Web app sederhana yang bisa:
- Lihat semua tambak udang di map
- Tracking level kontaminasi cesium
- Otomatis kasih warning kalo ada yang bahaya (pake sistem AI sederhana)
- Nyimpen history semua sample
- Visualisasi zona risiko di sekitar tambak yang terkontaminasi

## Fitur

- Map interaktif pake Leaflet.js
- Color-coded markers (hijau/kuning/merah) based on risk level
- Dashboard buat liat statistik cepet
- Form buat input sample baru
- Risk radius 5km kalo ada area high-risk
- History tracking semua pengukuran

## Tech Stack

Simple aja:
- Backend: Python + Flask
- Frontend: HTML, CSS, JS biasa
- Map: Leaflet.js
- Data: In-memory (bisa di-upgrade ke database beneran nanti)

## Cara jalanin

Install dependencies dulu:
```bash
pip install flask flask-cors
```

Jalanin server:
```bash
python app.py
```

Buka browser:
```
http://127.0.0.1:5000
```

Done.

## Struktur file
```
cesium-guard-mvp/
├── app.py              # Backend Flask
├── index.html          # Frontend
├── README.md           
└── requirements.txt    
```

## API

Simple REST API:
- `GET /api/farms` - ambil semua data tambak
- `POST /api/sample` - submit sample baru
- `GET /api/stats` - ambil stats dashboard

## Team

- Ahmad Hoesin
- Dionisius Bennett Andrianto  
- Goran Adriano Tamrella
- Gavrila Kartika Sarah Suoth
- William Jesiel

## Notes

Project ini dibuat buat hackathon. Masih banyak yang bisa di-improve, tapi MVP-nya udah jalan dengan baik.

Kalo ada bug atau mau contribute, feel free.

---

Built for RISTEK Mini Hackathon 2025
