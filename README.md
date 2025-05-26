````markdown
# SurgeonMatch API Suite

> A set of RESTful endpoints exposing CareSet’s census-level Medicare claims data—designed for rapid integration into healthcare applications.

---

## 🚀 Quick Start

1. **Clone the Repo**  
   ```bash
   git clone https://github.com/careset/surgeon-match-api.git
   cd surgeon-match-api
````

2. **Create a Virtual Environment & Install**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**

   ```bash
   export DATABASE_URL="postgres://user:pass@hostname:5432/careset"
   export REDIS_URL="redis://localhost:6379/0"
   export API_KEY="YOUR_API_KEY_HERE"
   ```

4. **Run Migrations & Seed Data**

   ```bash
   alembic upgrade head
   python scripts/seed_surveys.py
   ```

5. **Start the Server**

   ```bash
   uvicorn app.main:app --reload
   ```

6. **Visit Docs**
   Open your browser to `http://localhost:8000/docs` for interactive Swagger UI.

---

## 📚 Core Endpoints

### 1. Surgeon Directory

`GET /v1/surgeons`

**Query Params:**

* `specialtyCode` (string)
* `lat`, `lng`, `radiusMiles` (floats)
* `minClaimVolume` (int)
* `acceptsMedicare` (bool)

**Response:**

```json
[
  {
    "npi": "1234567890",
    "name": "Dr. Jane Smith, MD",
    "specialty_code": "47.091",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "claim_volume_6mo": 24,
    "quality_score": 4.7
  },
  …
]
```

---

### 2. Patient Journey

`GET /v1/patientJourneys`

**Query Params:**

* `diagnosisCode` (string)
* `cohortSize` (int)

**Response:**

```json
{
  "diagnosis_code": "K35.80",
  "cohort_size": 5000,
  "avg_time_to_surgery": 2.3,
  "therapy_sequence": [
    { "step": "ER Admission", "percent": 100 },
    { "step": "Imaging",     "percent": 95  },
    { "step": "Surgery",     "percent": 88  }
  ]
}
```

---

### 3. Surgeon Availability Inquiry

`POST /v1/availabilityInquiry`

**Body:**

```json
{
  "npiList": ["1234567890","9876543210"],
  "requestedDate": "2025-06-12"
}
```

**Response:**

```json
[
  { "npi": "1234567890", "available": true,  "notes": "On-call team available" },
  { "npi": "9876543210", "available": false, "notes": "Booked full day"  }
]
```

---

### 4. Surgeon Outcomes & Quality

`GET /v1/surgeonQuality/{npi}`

**Response:**

```json
{
  "npi": "1234567890",
  "procedure_code": "47.091",
  "readmission_rate_30d": 2.1,
  "complication_rate": 1.3,
  "avg_length_of_stay": 3.8
}
```

---

## ⚡ Stretch-Goal Endpoints

### High-Value Practice Finder

`GET /v1/highValuePractices`

* **Params:** `diagnosisCode`, `minCohortSize`, `topN`
* **Purpose:** Ranks practices by treatment gaps (unmet need).

### Part D Payer & Plan Trends

`GET /v1/partDTrends`

* **Params:** `drugCode`, `dateFrom`, `dateTo`, `region`
* **Purpose:** Tracks Part D spend & claim counts by payer/plan.

### Referral Network Graph

`GET /v1/referralGraph`

* **Params:** `npi`, `depth`, `minSharedPatients`
* **Purpose:** Returns nodes/edges for provider referral networks.

### Patient Adherence & Refill Metrics

`GET /v1/adherence`

* **Params:** `npi`, `drugCode`, `period`
* **Purpose:** Computes adherence (PDC, refill gaps, non-adherence).

### Cohort Segmentation Service

`POST /v1/cohortSegments`

* **Body:** `{ diagnosisCode, features[], segmentCount }`
* **Purpose:** Returns algorithmic patient segments for analytics.

### Cost-of-Care & Out-of-Pocket Tracker

`GET /v1/costOfCare`

* **Params:** `drugCode`, `region`
* **Purpose:** Estimates total vs. patient OOP costs by region.

---

## 🔧 QNN “Power-Up” Integration

You can optionally call CareSet’s QNN API for code-level insights:

```bash
# Feature Extraction
curl -X POST https://qnn.ainative.studio/v1/code/feature-extraction \
  -H "Authorization: Bearer YOUR_QNN_KEY" \
  -d '{ "code": "...", "features": ["function_names","docstrings"] }'

# Code Quality Check
curl -X POST https://qnn.ainative.studio/v1/code/quality \
  -H "Authorization: Bearer YOUR_QNN_KEY" \
  -d '{ "code": "...", "metrics": ["style","missing_tests"] }'
```

---

## 🧪 Testing & QA

* **Unit tests** live in `tests/unit/`
* **Integration tests** in `tests/integration/`
* Run all tests with:

  ```bash
  pytest
  ```

---

## 📦 SDK Examples

See `docs/sdk/python.md` and `docs/sdk/js.md` for ready-to-use code snippets.

---

## 📄 License & Contributing

* **License:** MIT
* **Contributing:** Please read `CONTRIBUTING.md` for guidelines on pull requests, code style, and branch management.

---

> *Built with ❤️ by the CareSet Data Platform Team*

```

This README provides a clear overview of all core and stretch endpoints, setup steps, testing instructions, and optional QNN integrations—ready for developer consumption.
```
