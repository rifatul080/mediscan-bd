
# MediScan BD

### Smart Medicine Detection & Pharmacy Billing System

> A real-time pharmacy billing system for Bangladesh that detects medicines from camera images using OCR, matches them against a local database, and generates instant itemized bills with print support.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [How It Works](#how-it-works)
- [API Reference](#api-reference)
- [Database Design](#database-design)
- [Team](#team)
- [Acknowledgements](#acknowledgements)

---

## Overview

MediScan BD is a university software engineering project built for Uttara University, Bangladesh. It addresses a real daily problem faced by pharmacies across the country — slow and error-prone manual medicine search during billing.

The system allows a pharmacist to hold a medicine packet in front of a camera. The system automatically captures the image, reads the text using OCR (Optical Character Recognition), matches it against a locally stored medicine database, and builds a live bill in real time. The completed bill can be printed with a single click.

The system is designed to work **fully offline** — no internet connection is required during billing operations. Internet is only needed for periodic database synchronization.

---

## Problem Statement

In most pharmacies across Bangladesh, billing is done by manually typing or searching medicine names — a process that is:

- **Slow** — takes 2–5 minutes per customer during busy hours
- **Error-prone** — similar medicine names cause mistakes
- **Inefficient** — staff spend time searching instead of serving

MediScan BD solves this by automating the detection step. The pharmacist simply holds up each medicine packet and the system identifies it automatically.

---

## Key Features

- **Auto-capture camera** — detects when a medicine packet is held still and captures automatically, no button press required
- **OCR-based detection** — reads printed text from medicine packets using EasyOCR
- **Fuzzy matching** — finds the correct medicine even when OCR makes small errors
- **Live billing panel** — medicines are added to a live bill in real time on the same screen
- **Partial strip support** — supports billing per tablet or per full strip
- **Discount support** — percentage or flat discount on any bill
- **Print receipt** — one-click browser print for any printer including thermal receipt printers
- **Transaction history** — all past bills stored and viewable with expandable details
- **Offline-first** — works completely without internet during billing
- **Multi-source database** — medicine data scraped from MedEasy and Chaldal
- **Camera selector** — supports multiple cameras including external webcams

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  Scan Page → Live Bill → Billing Page → History Page    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (localhost:8000)
┌──────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                      │
│                                                          │
│  /detect/ocr    → OCR Pipeline                           │
│  /medicines/    → Medicine Search                        │
│  /billing/      → Bill Management                        │
└──────────┬────────────────────┬────────────────────────┘
           │                    │
┌──────────▼──────┐   ┌─────────▼──────────────────────┐
│  SQLite DB      │   │  OCR Engine (EasyOCR)           │
│  mediscan.db    │   │  Preprocessor (OpenCV)          │
│  6,400+ records │   │  Fuzzy Matcher (RapidFuzz)      │
└─────────────────┘   └────────────────────────────────┘
```

### Detection Pipeline

```
Camera Frame
     │
     ▼
Motion Detection (canvas pixel comparison)
     │
     ▼ (stable frame detected)
Auto Capture
     │
     ▼
Image Preprocessing (OpenCV)
  - Resize 2x
  - Grayscale
  - Adaptive brightness
  - CLAHE contrast
  - Denoise + Sharpen
     │
     ▼
EasyOCR Text Extraction
     │
     ▼
Text Cleaning & Name Extraction
     │
     ▼
Fuzzy Matching (RapidFuzz multi-strategy)
  - token_sort_ratio
  - partial_ratio
  - token_set_ratio
  - brand name scoring
     │
     ▼
Top 3 Medicine Suggestions
     │
     ▼
Pharmacist Confirms → Added to Live Bill
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React (Create React App) | Pharmacist UI |
| Backend | FastAPI (Python) | REST API |
| Database | SQLite | Local medicine storage |
| OCR | EasyOCR | Text extraction from images |
| Image Processing | OpenCV | Image preprocessing |
| Fuzzy Matching | RapidFuzz | Tolerant medicine name matching |
| Web Scraping | Playwright + Scrapy | Medicine data collection |
| HTTP Client | Axios | Frontend API calls |
| Camera | react-webcam | Browser camera access |
| PDF/Print | Browser Print API | Receipt printing |

---

## Project Structure

```
mediscan-bd/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings and constants
│   │   ├── database.py              # SQLite connection
│   │   │
│   │   ├── models/
│   │   │   ├── medicine.py          # Medicine table
│   │   │   ├── transaction.py       # Billing transactions
│   │   │   └── user.py              # User accounts
│   │   │
│   │   ├── routers/
│   │   │   ├── detection.py         # /detect/ocr, /detect/barcode
│   │   │   ├── medicines.py         # /medicines/search
│   │   │   ├── billing.py           # /billing/create, /billing/{id}
│   │   │   └── auth.py              # Authentication
│   │   │
│   │   ├── services/
│   │   │   ├── ocr_engine.py        # EasyOCR wrapper
│   │   │   ├── preprocessor.py      # OpenCV image processing
│   │   │   ├── fuzzy_matcher.py     # RapidFuzz matching logic
│   │   │   ├── barcode_scanner.py   # pyzbar barcode reading
│   │   │   └── receipt_generator.py # ReportLab PDF generation
│   │   │
│   │   └── scraper/
│   │       ├── medeasy_scraper.py   # Scrapes medeasy.health
│   │       ├── chaldal_scraper.py   # Scrapes chaldal.com/pharmacy
│   │       ├── normalizer.py        # Data standardization
│   │       └── deduplicator.py      # Duplicate removal
│   │
│   ├── data/
│   │   └── mediscan.db              # SQLite database (not in repo)
│   ├── receipts/                    # Generated PDF receipts
│   ├── requirements.txt
│   └── run.py                       # Server entry point
│
├── frontend/
│   └── src/
│       ├── App.js                   # React router setup
│       ├── pages/
│       │   ├── Scan.jsx             # Main scan + live bill page
│       │   ├── Billing.jsx          # Print-ready bill page
│       │   └── History.jsx          # Transaction history
│       ├── components/
│       │   └── Navbar.jsx
│       └── services/
│           └── api.js               # All API calls
│
├── diagrams/                        # UML diagrams
├── docs/                            # Project documents
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/rifatul080/mediscan-bd.git
cd mediscan-bd
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Build the Medicine Database

```bash
cd backend
venv\Scripts\activate
python app/scraper/medeasy_scraper.py
```

### 5. Run the Application

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate
python run.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm start
```

Frontend: `http://localhost:3000`  
Backend API docs: `http://localhost:8000/docs`

---

## How It Works

### Scanning a Medicine

1. Pharmacist opens the Scan page and clicks **Start Camera**
2. Holds a medicine packet still inside the blue frame
3. System detects motion, waits for the image to stabilize
4. Auto-captures the image — green **CAPTURED!** flash appears
5. Image is sent to the backend OCR endpoint
6. EasyOCR reads the text from the preprocessed image
7. Fuzzy matcher finds the top 3 closest medicines in the database
8. Suggestions appear below the live bill with confidence percentages
9. Pharmacist clicks **+ Add** to add the correct medicine to the live bill
10. Process repeats for the next medicine

### Completing a Bill

1. All medicines added to the live bill panel
2. Quantities adjusted per item if needed
3. Optional discount applied (percentage or flat amount)
4. Pharmacist clicks **Confirm Bill**
5. Redirected to Billing page — click **Print** to print the receipt

---

## API Reference

### Detection

| Method | Endpoint | Description |
|---|---|---|
| POST | `/detect/ocr` | Detect medicine from base64 image |
| POST | `/detect/barcode` | Look up medicine by barcode |
| GET | `/detect/test` | Check if OCR engine is loaded |

### Medicines

| Method | Endpoint | Description |
|---|---|---|
| GET | `/medicines/search?query=` | Fuzzy search by name |
| GET | `/medicines/{id}` | Get medicine by ID |
| GET | `/medicines/barcode/{barcode}` | Get medicine by barcode |

### Billing

| Method | Endpoint | Description |
|---|---|---|
| POST | `/billing/create` | Create a new bill |
| GET | `/billing/` | Get all bills |
| GET | `/billing/{id}` | Get a specific bill |
| GET | `/billing/{id}/receipt` | Download PDF receipt |

---

## Database Design

### medicines table

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| brand_name | TEXT | Medicine brand name |
| generic_name | TEXT | Generic / chemical name |
| manufacturer | TEXT | Pharmaceutical company |
| strength | TEXT | Dosage e.g. "500mg" |
| form | TEXT | tablet / syrup / injection |
| unit_price | REAL | Price per unit/strip |
| pack_size | INTEGER | Units per pack |
| barcode | TEXT | Barcode if available |
| source | TEXT | Data source website |
| last_updated | TEXT | Date last synced |

---

## Known Limitations

- OCR accuracy depends on camera quality and lighting conditions
- Very similar medicine names may require pharmacist confirmation
- Database covers approximately 60–70% of registered medicines in Bangladesh
- EasyOCR requires ~2GB RAM and takes 3–5 seconds per scan
- SQLite is not suitable for multi-user concurrent access at scale

---

## Developer

**Uttara University — Department of CSE**  
**Course:** Software Engineering Lab (CSE06133310)  
**Supervisor:** Md. Ashraful Kabir, Lecturer

| Name | ID | Role |
|---|---|---|
| Rifatul Islam | 2233081315 | Solo Developer — Full system design, backend, frontend, OCR pipeline, database, scraper |

---

## Acknowledgements

- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — OCR engine
- [FastAPI](https://fastapi.tiangolo.com) — Python web framework
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — Fuzzy string matching
- [OpenCV](https://opencv.org) — Image preprocessing
- [MedEasy Bangladesh](https://medeasy.health) — Medicine data source
- [Chaldal](https://chaldal.com) — Medicine data source

---

*Built with care for Bangladesh's pharmacy community.*
