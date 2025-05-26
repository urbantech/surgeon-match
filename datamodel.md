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

## 📦 6. Add-On Tables for Stretch-Goal APIs

### 6.1 high\_value\_practices

Pre-computed “gap” analysis for each practice/cohort.

| Column           | Type           | Constraints                       | Description                                       |
| ---------------- | -------------- | --------------------------------- | ------------------------------------------------- |
| `npi`            | `VARCHAR(10)`  | **PK**, FK → `surgeons(npi)`      | Provider NPI                                      |
| `hco_id`         | `VARCHAR(20)`  |                                   | Health Care Org ID                                |
| `practice_name`  | `TEXT`         | NOT NULL                          | Practice or group name                            |
| `diagnosis_code` | `VARCHAR(10)`  | NOT NULL, FK → `patient_journeys` | ICD-10 code                                       |
| `cohort_size`    | `INTEGER`      | NOT NULL                          | Number of patients in cohort                      |
| `treated_count`  | `INTEGER`      | NOT NULL                          | Number of those patients treated by this practice |
| `gap_percentage` | `DECIMAL(5,2)` | NOT NULL                          | 100 × (1 – treated\_count/cohort\_size)           |
| `last_updated`   | `TIMESTAMP`    | NOT NULL DEFAULT `NOW()`          | When gap was last recalculated                    |

> **Index:** `(diagnosis_code, gap_percentage DESC)` to fetch top practices efficiently.

---

### 6.2 part\_d\_trends

Monthly spend & claim metrics by payer/plan for Part D.

| Column        | Type            | Constraints                       | Description                   |
| ------------- | --------------- | --------------------------------- | ----------------------------- |
| `month`       | `DATE`          | **PK**                            | First day of the month        |
| `plan_id`     | `VARCHAR(20)`   | **PK**                            | Plan identifier               |
| `payer_name`  | `TEXT`          | NOT NULL                          | Payer (e.g. UnitedHealthcare) |
| `drug_code`   | `VARCHAR(15)`   | **PK**, FK → drug reference table | NDC or HCPCS code             |
| `total_spend` | `DECIMAL(12,2)` | NOT NULL                          | Gross Medicare Part D spend   |
| `claim_count` | `INTEGER`       | NOT NULL                          | Number of claims              |
| `avg_cost`    | `DECIMAL(7,2)`  | NOT NULL                          | total\_spend / claim\_count   |
| `updated_at`  | `TIMESTAMP`     | NOT NULL DEFAULT `NOW()`          | Last refresh                  |

> **Index:** `(drug_code, month)` for fast time-series queries.

---

### 6.3 docgraph\_edges

(If not already modeled) Materialize DocGraph PUF for referrals.

| Column            | Type          | Constraints                  | Description                          |
| ----------------- | ------------- | ---------------------------- | ------------------------------------ |
| `from_npi`        | `VARCHAR(10)` | **PK**, FK → `surgeons(npi)` | Referring provider                   |
| `to_npi`          | `VARCHAR(10)` | **PK**, FK → `surgeons(npi)` | Receiving provider                   |
| `shared_patients` | `INTEGER`     | NOT NULL                     | Count of shared patients             |
| `last_updated`    | `TIMESTAMP`   | NOT NULL DEFAULT `NOW()`     | When this edge was last recalculated |

> **Index:** Composite PK on `(from_npi,to_npi)`.

---

### 6.4 adherence\_metrics

Patient adherence & refill stats per provider/drug.

| Column             | Type           | Constraints                            | Description                         |
| ------------------ | -------------- | -------------------------------------- | ----------------------------------- |
| `npi`              | `VARCHAR(10)`  | **PK** composite, FK → `surgeons(npi)` | Provider NPI                        |
| `drug_code`        | `VARCHAR(15)`  | **PK** composite                       | NDC or HCPCS code                   |
| `period_start`     | `DATE`         | **PK** composite                       | Start of measurement window         |
| `period_end`       | `DATE`         | **PK** composite                       | End of measurement window           |
| `pdc`              | `DECIMAL(4,2)` | NOT NULL                               | Proportion of Days Covered          |
| `avg_refill_gap`   | `DECIMAL(5,2)` | NOT NULL                               | Average refill gap in days          |
| `non_adherent_pct` | `DECIMAL(5,2)` | NOT NULL                               | Percentage of patients non-adherent |
| `calculated_at`    | `TIMESTAMP`    | NOT NULL DEFAULT `NOW()`               | When metrics were last computed     |

> **Index:** `(npi, drug_code, period_start)`.

---

### 6.5 cohort\_segments

Stored segment definitions for each disease cohort.

| Column           | Type          | Constraints                       | Description                                               |
| ---------------- | ------------- | --------------------------------- | --------------------------------------------------------- |
| `segment_id`     | `SERIAL`      | **PK**                            | Auto-increment segment identifier                         |
| `diagnosis_code` | `VARCHAR(10)` | NOT NULL, FK → `patient_journeys` | ICD-10 code                                               |
| `criteria`       | `JSONB`       | NOT NULL                          | E.g. `{ "ageGroup": "65–74", "comorbidityCount": ">=2" }` |
| `segment_size`   | `INTEGER`     | NOT NULL                          | Number of patients in this segment                        |
| `created_at`     | `TIMESTAMP`   | NOT NULL DEFAULT `NOW()`          | When segment was generated                                |

> **Index:** `(diagnosis_code, segment_id)`.

---

### 6.6 cost\_of\_care

Aggregated total vs. patient out-of-pocket costs by region/drug.

| Column              | Type            | Constraints              | Description                             |
| ------------------- | --------------- | ------------------------ | --------------------------------------- |
| `region`            | `VARCHAR(10)`   | **PK**                   | ZIP prefix or state code                |
| `drug_code`         | `VARCHAR(15)`   | **PK**                   | NDC or HCPCS code                       |
| `total_cost`        | `DECIMAL(12,2)` | NOT NULL                 | Total Medicare payout                   |
| `avg_patient_oop`   | `DECIMAL(7,2)`  | NOT NULL                 | Average patient out-of-pocket per claim |
| `patient_share_pct` | `DECIMAL(5,2)`  | NOT NULL                 | 100 × patient share / total\_cost       |
| `updated_at`        | `TIMESTAMP`     | NOT NULL DEFAULT `NOW()` | When metrics were last updated          |

> **Index:** `(region, drug_code)` for lookup.

---

These **add-on tables** will seamlessly slot into your existing schema—providing the necessary back-end support for the Stretch-Goal APIs, and empowering developers to build richer, commercial healthcare applications on CareSet’s census-level Medicare data.
