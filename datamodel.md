# 🎯 SurgeonMatch Data Model

### 🗄️ 1. **surgeons**

Stores core provider metadata and location.

| Column             | Type           | Constraints                        | Description                               |
| ------------------ | -------------- | ---------------------------------- | ----------------------------------------- |
| `npi`              | `VARCHAR(10)`  | **PK**, NOT NULL                   | National Provider Identifier              |
| `name`             | `TEXT`         | NOT NULL                           | Full provider name                        |
| `specialty_code`   | `VARCHAR(10)`  | NOT NULL, FK → `specialties(code)` | CMS or ICD-10 specialty code              |
| `address`          | `TEXT`         |                                    | Mailing or practice address               |
| `latitude`         | `DECIMAL(9,6)` | NOT NULL                           | Geo latitude (WGS84)                      |
| `longitude`        | `DECIMAL(9,6)` | NOT NULL                           | Geo longitude (WGS84)                     |
| `accepts_medicare` | `BOOLEAN`      | NOT NULL DEFAULT `TRUE`            | Whether the provider accepts Medicare A/B |
| `created_at`       | `TIMESTAMP`    | NOT NULL DEFAULT `NOW()`           | Record creation time                      |
| `updated_at`       | `TIMESTAMP`    | NOT NULL DEFAULT `NOW()`           | Last update time (via trigger)            |

> **Indexes:**
>
> * `IDX_surgeons_location` on (`latitude`,`longitude`)
> * `IDX_surgeons_specialty` on (`specialty_code`)

---

### 🗄️ 2. **claims\_aggregates**

Holds pre-computed volumes & quality scores per surgeon.

| Column             | Type           | Constraints                  | Description                                |
| ------------------ | -------------- | ---------------------------- | ------------------------------------------ |
| `npi`              | `VARCHAR(10)`  | **PK**, FK → `surgeons(npi)` | Provider NPI                               |
| `claim_volume_6mo` | `INTEGER`      | NOT NULL DEFAULT `0`         | Number of Medicare A/B claims in last 6 mo |
| `quality_score`    | `DECIMAL(3,2)` | NOT NULL DEFAULT `0.00`      | Composite quality metric (0.00–5.00)       |
| `updated_at`       | `TIMESTAMP`    | NOT NULL DEFAULT `NOW()`     | Last refresh timestamp                     |

> **Indexes:**
>
> * PK on `npi` ensures fast join to `surgeons`.

---

### 🗄️ 3. **patient\_journeys**

Aggregates disease-cohort progression statistics.

| Column                | Type           | Constraints                    | Description                                                |
| --------------------- | -------------- | ------------------------------ | ---------------------------------------------------------- |
| `diagnosis_code`      | `VARCHAR(10)`  | **PK**, FK → `diagnoses(code)` | ICD-10 diagnosis identifier                                |
| `cohort_size`         | `INTEGER`      | NOT NULL                       | Number of patients in this cohort                          |
| `avg_time_to_surgery` | `DECIMAL(5,2)` | NOT NULL                       | Mean days from diagnosis to surgery                        |
| `therapy_sequence`    | `JSONB`        | NOT NULL                       | Ordered list of `{ step:STRING, percent:NUMERIC }` objects |
| `last_updated`        | `TIMESTAMP`    | NOT NULL DEFAULT `NOW()`       | When these metrics were last recalculated                  |

> **Example `therapy_sequence`:**
>
> ```json
> [
>   { "step": "ER Admission", "percent": 100.0 },
>   { "step": "Imaging",     "percent": 95.0   },
>   { "step": "Surgery",     "percent": 88.0   }
> ]
> ```

---

### 🗄️ 4. **availability\_cache**

Short-lived cache of surgeon on-call availability.

| Column           | Type          | Constraints                            | Description                             |
| ---------------- | ------------- | -------------------------------------- | --------------------------------------- |
| `npi`            | `VARCHAR(10)` | **PK** composite, FK → `surgeons(npi)` | Provider NPI                            |
| `requested_date` | `DATE`        | **PK** composite                       | Date for which availability was checked |
| `available`      | `BOOLEAN`     | NOT NULL                               | Whether surgeon is available            |
| `notes`          | `TEXT`        |                                        | Free-form availability details          |
| `fetched_at`     | `TIMESTAMP`   | NOT NULL DEFAULT `NOW()`               | When this cache entry was written       |

> **TTL:**
>
> * Apply Redis or DB TTL of **1 hour** on each key

---

### 🗄️ 5. **surgeon\_quality**

Detailed outcome metrics per surgeon and procedure type.

| Column                 | Type           | Constraints                            | Description                                      |
| ---------------------- | -------------- | -------------------------------------- | ------------------------------------------------ |
| `npi`                  | `VARCHAR(10)`  | **PK** composite, FK → `surgeons(npi)` | Provider NPI                                     |
| `procedure_code`       | `VARCHAR(10)`  | **PK** composite                       | CMS code for the surgery type                    |
| `readmission_rate_30d` | `DECIMAL(4,2)` | NOT NULL                               | Percentage of patients readmitted within 30 days |
| `complication_rate`    | `DECIMAL(4,2)` | NOT NULL                               | Percentage with documented complications         |
| `avg_length_of_stay`   | `DECIMAL(4,2)` | NOT NULL                               | Mean hospital stay (days)                        |
| `last_refreshed`       | `TIMESTAMP`    | NOT NULL DEFAULT `NOW()`               | When metrics were last recalculated              |

> **Indexes:**
>
> * Composite PK (`npi`,`procedure_code`) for direct lookup

---

## 🔗 Relationships & ERD

```
surgeons (1) ───< claims_aggregates (1)
       │
       ├───< availability_cache (M)
       │
       └───< surgeon_quality (M)
       
patient_journeys (1)
```

* **1→1** between `surgeons` and `claims_aggregates`
* **1→M** from `surgeons` to `availability_cache` and `surgeon_quality`
* `patient_journeys` is standalone, keyed by `diagnosis_code`

---

## 📜 JSON Response Schemas

### **GET /v1/surgeons**

```json
[
  {
    "npi": "1234567890",
    "name": "Dr. Jane Smith, MD",
    "specialty_code": "47.091",
    "latitude": 37.774900,
    "longitude": -122.419400,
    "claim_volume_6mo": 24,
    "quality_score": 4.70
  },
  …
]
```

### **GET /v1/patientJourneys**

```json
{
  "diagnosis_code": "K35.80",
  "cohort_size": 5000,
  "avg_time_to_surgery": 2.30,
  "therapy_sequence": [
    { "step": "ER Admission", "percent": 100.0 },
    { "step": "Imaging",     "percent": 95.0   },
    { "step": "Surgery",     "percent": 88.0   }
  ]
}
```

### **POST /v1/availabilityInquiry**

```json
[
  { "npi": "1234567890", "available": true,  "notes": "On-call team available" },
  { "npi": "9876543210", "available": false, "notes": "Booked full day"  }
]
```

### **GET /v1/surgeonQuality/{npi}**

```json
{
  "npi": "1234567890",
  "procedure_code": "47.091",
  "readmission_rate_30d": 2.10,
  "complication_rate": 1.30,
  "avg_length_of_stay": 3.80
}
```

---
