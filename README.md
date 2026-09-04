# SonarAI — Intelligent Side-Scan Sonar (SSS) Survey Analysis Platform

SonarAI is a production-quality, log-first AI analysis platform designed for processing underwater Side-Scan Sonar (SSS) survey image logs.

---

## 🌊 Key Features & System Design

- **Log-First Architecture**: Designed around complete survey image logs (processing multiple sequential sonar frames or ZIP archives) rather than single images.
- **AI Segmentation & Object Detection**: Identifies shipwreck structures and flags novel anomalies/unknown targets (AI4Shipwrecks schema scope).
- **Modular Inference Interface**: Abstract `InferenceProvider` pattern decoupled from the frontend and API layers.
- **Mock & PyTorch Inference Providers**: Ships with `MockInferenceProvider` for reproducible synthetic SSS masks, overlays, and 128-dim SSL feature vectors. Automatically switches to `PyTorchInferenceProvider` when `best_ssl_unet_accuracy.pth` is added to `backend/app/weights/`.
- **Live Pipeline Monitor**: Real-time image-by-image processing checklist (`✓ Completed`, `→ Processing`, `○ Pending`) with speed and progress percentage.
- **Interactive Sonar Inspector**: Side-by-side view (Original SSS vs AI Segmentation & Bounding Box Overlay), zoom/pan controls, SSL Feature Representation heatmaps, and detection details.
- **Survey Analytics & Map View**: Aggregated survey metrics, Recharts classification ratios, timeline navigator, and geolocation missing-metadata fallback notifications.

---

## 📁 Project Structure

```
sonar-detection/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI server entrypoint & static mounts
│   │   ├── config.py                   # Paths, allowed extensions, JSON store path
│   │   ├── api/                        # REST API Routes
│   │   │   ├── logs.py                 # Upload log/ZIP, list, detail, detections
│   │   │   ├── analysis.py             # Start job, status polling, results
│   │   │   └── health.py               # Health & provider state check
│   │   ├── models/
│   │   │   └── inference.py            # Abstract Base Class InferenceProvider
│   │   ├── services/
│   │   │   ├── log_service.py          # Storage and metadata manager
│   │   │   ├── analysis_service.py     # Background survey processing task runner
│   │   │   ├── inference_service.py    # Active provider factory & selector
│   │   │   ├── mock_provider.py        # MockInferenceProvider (synthetic DEMO results)
│   │   │   └── pytorch_provider.py     # PyTorchInferenceProvider (.pth model loader)
│   │   ├── schemas/                    # Pydantic data schemas
│   │   │   ├── log.py
│   │   │   ├── analysis.py
│   │   │   └── detection.py
│   │   ├── storage/
│   │   │   ├── uploads/                # Received survey image files
│   │   │   └── outputs/                # Generated masks, overlays, thumbnails
│   │   └── weights/
│   │       └── PLACE_MODEL_HERE.txt    # Instructions for placing best_ssl_unet_accuracy.pth
│   ├── test_backend.py                 # Backend unit & endpoint verification tests
│   └── requirements.txt                # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/                 # React UI components
│   │   │   ├── Navbar.tsx              # Top navigation & active model status indicator
│   │   │   ├── SummaryCards.tsx        # Dashboard metric overview cards
│   │   │   ├── LogTable.tsx            # Recent survey logs list & action buttons
│   │   │   ├── ImageOverlayViewer.tsx  # Side-by-side original vs overlay viewer
│   │   │   ├── DetectionDetails.tsx    # Bbox, class, confidence, novelty, location panel
│   │   │   ├── SSLFeatureViewer.tsx    # 128-D SSL feature embedding representation
│   │   │   └── ProcessingStatus.tsx    # Real-time pipeline status & image checklist
│   │   ├── pages/                      # Views (Dashboard, Upload, Processing, Survey, Image, Map)
│   │   ├── services/
│   │   │   └── api.ts                  # Centralized fetch API client
│   │   ├── types/
│   │   │   └── sonar.ts                # TypeScript interfaces
│   │   ├── App.tsx                     # Router setup
│   │   └── index.css                   # Tailwind dark ocean theme styling
│   └── package.json
└── README.md
```

---

## 🚀 How to Run the Application

### 1. Start Backend Server
```bash
# Navigate to project root
cd backend

# Install dependencies
python -m pip install -r requirements.txt

# Run backend API server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Backend API will be live at: `http://127.0.0.1:8000`  
Swagger API Docs available at: `http://127.0.0.1:8000/docs`

### 2. Run Backend Unit Tests
```bash
python backend/test_backend.py
```

### 3. Start Frontend Dev Server
```bash
cd frontend

# Install packages
npm install

# Launch Vite dev server
npm run dev
```
Frontend UI will be live at: `http://localhost:5173`

---

## 🔌 Connecting the Kaggle-Trained PyTorch Model

When your Kaggle training produces the PyTorch model checkpoint:

1. Copy the `.pth` file into `backend/app/weights/best_ssl_unet_accuracy.pth`.
2. Restart the backend server.
3. `PyTorchInferenceProvider` will automatically detect the weights and switch from DEMO mode to real PyTorch U-Net inference without requiring any frontend code changes!

---

## 📡 REST API Summary

- `POST /api/logs/upload`: Accepts multiple SSS images or ZIP archive, creates survey log.
- `GET /api/logs`: Returns survey logs summary list.
- `GET /api/logs/{log_id}`: Returns survey log details and image records.
- `POST /api/logs/{log_id}/analyze`: Spawns async background analysis pipeline.
- `GET /api/logs/{log_id}/status`: Polling endpoint returning progress percentage & live image state.
- `GET /api/logs/{log_id}/results`: Survey-level aggregated stats and per-image counts.
- `GET /api/logs/{log_id}/images`: Returns ordered list of images.
- `GET /api/logs/{log_id}/images/{image_id}`: Returns single image detail, mask/overlay URLs, SSL features, and detections.
- `GET /api/logs/{log_id}/detections`: Returns all detections for the survey.
- `GET /api/health`: Health status and active inference provider mode.
