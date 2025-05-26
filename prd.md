# 🏥 SurgeonMatch API PRD

> **Accelerate emergency surgery referrals by exposing Medicare-driven surgeon data via simple, performant REST endpoints.**

---

## 1. Executive Summary

CareSet will ship four new public APIs—Surgeon Directory, Patient Journey, Surgeon Availability Inquiry, and Surgeon Outcomes & Quality—so that developers can build front-ends and integrations in a single day. These endpoints will power apps that match Medicare patients to local surgeons, surface typical care pathways, check on-call availability, and report quality metrics.

---

## 2. Goals & Success Metrics

* **Goal 1:** Deliver four fully documented, authenticated REST endpoints by EOD.
* **Goal 2:** Provide SDK examples (Python, JavaScript) and a Postman collection.
* **Goal 3:** Achieve <200 ms median latency; ≥99% uptime in initial rollout.

**Success Metrics**

* 3rd-party demo app built within 4 hours of launch
* ≥5 internal dev teams onboarded within 1 week
* API error rate <1% over first 48 h

---

## 3. Target Users & Personas

| Persona                | Needs                                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| **Mobile Dev**         | Simple geospatial query for nearby, Medicare-accepting surgeons with volume & rating filters. |
| **Frontend Engineer**  | Embed “Patient Journey” charts and stats in care-coordination dashboards.                     |
| **Data Scientist**     | Bulk pull of cohort disease-progression metrics for analytics.                                |
| **Operations Analyst** | Real-time availability flags for on-call surgeon dispatch.                                    |

---

## 4. Scope & Features

### 4.1 Core Endpoints

1. **Surgeon Directory**

   * **GET** `/v1/surgeons`
   * **Query Params:**

     * `specialtyCode` (ICD-10 or CMS specialty)
     * `lat`, `lng`, `radiusMiles`
     * `minClaimVolume` (integer)
     * `acceptsMedicare` (boolean)
   * **Response:** List of `{ npi, name, specialty, location, claimVolume6mo, qualityScore }`

2. **Patient Journey**

   * **GET** `/v1/patientJourneys`
   * **Query Params:**

     * `diagnosisCode` (ICD-10)
     * `cohortSize` (integer)
   * **Response:** `{ diagnosis, averageTimeToSurgeryDays, topTherapySequence: [{step, percent}] }`

3. **Surgeon Availability Inquiry**

   * **POST** `/v1/availabilityInquiry`
   * **Body:** `{ npiList: [string], requestedDate: ISO8601 }`
   * **Response:** `[ { npi, available: boolean, notes } ]`

4. **Surgeon Outcomes & Quality**

   * **GET** `/v1/surgeonQuality/{npi}`
   * **Response:** `{ npi, surgeryType, 30DayReadmissionRate, complicationRate, averageLengthOfStay }`

### 4.2 Optional Extensions (Stretch)

* **GET** `/v1/highValuePractices` → top practices by “journey gap” score
* **Agent-driven summary** (LangChain micro-service) for plain-language patient-next-step guide

---

## 5. Functional Requirements

| Requirement ID | Description                                              | Priority |
| -------------- | -------------------------------------------------------- | -------- |
| FR-1           | Authenticated access via API key header                  | Must     |
| FR-2           | Support pagination (`limit`/`offset`) on list endpoints  | Must     |
| FR-3           | Geospatial filtering within 0–100 mi radius              | Must     |
| FR-4           | JSON schema validation for request bodies                | Must     |
| FR-5           | OpenAPI (Swagger) docs generated and published           | Must     |
| FR-6           | Example SDK snippets for Python & JavaScript             | Should   |
| FR-7           | Postman collection bundle                                | Should   |
| FR-8           | Rate-limit: 100 req/min per API key                      | Must     |
| FR-9           | CORS support for `*.careset.com` and developer localhost | Must     |

---

## 6. Non-Functional Requirements

| Category        | Requirement                                        |
| --------------- | -------------------------------------------------- |
| **Performance** | P99 latency <500 ms; median <200 ms                |
| **Reliability** | 99% uptime SLA in first month                      |
| **Security**    | Enforce HTTPS, validate API keys, OWASP compliance |
| **Scalability** | Auto-scale via Kubernetes HPA at 50% CPU           |
| **Monitoring**  | Integrate with Datadog (API latency, error rates)  |
| **Logging**     | Structured JSON logs for all requests & responses  |

---

## 7. Data Model & Storage

* **Surgeons** table (indexed by `npi`): name, specialtyCode, lat, lng, address, acceptsMedicare
* **ClaimsAggregates** table: `npi`, `claimVolume6mo`, `qualityScore`
* **Journeys** table: `diagnosisCode`, `avgTimeToSurgery`, JSON `therapySequence`
* **AvailabilityCache** (Redis): key=`npi|date`, `available`, `notes` (TTL=1 hr)

---

## 8. Technical Architecture

```
Client → API Gateway → FastAPI Services ──┐
                                         └─> PostgreSQL (core data)
                                         └─> Redis (availability cache)
                                         └─> CareSet Claims Data Lake (S3 + Athena)
                                         └─> External Scheduling API (for live availability)
```

* **Framework:** Python 3.11 + FastAPI
* **Auth:** API key middleware
* **Docs:** `fastapi.openapi` → Swagger UI
* **Deploy:** Docker → Kubernetes (EKS) with HPA

---

## 9. Day-Of Roadmap

| Hour Block    | Team Activity                                             |
| ------------- | --------------------------------------------------------- |
| **0:00–0:30** | Project kickoff, environment setup, stub definitions      |
| **0:30–1:30** | Implement `/v1/surgeons` & `/v1/patientJourneys`          |
| **1:30–2:00** | Lunch break & quick sync                                  |
| **2:00–3:00** | Implement `/v1/availabilityInquiry` & caching logic       |
| **3:00–4:00** | Implement `/v1/surgeonQuality/{npi}` & wrap up features   |
| **4:00–4:30** | Auto-generate OpenAPI docs, add pagination & rate limit   |
| **4:30–5:00** | Testing, SDK snippet creation, Postman collection, deploy |

---

## 10. Risks & Mitigations

* **Data freshness:** Availability cache TTL too long → keep at 1 hr
* **API key abuse:** Enforce rate limits + monitor spikes
* **Latency spikes:** Add read replicas & optimize Postgres indexes

---

## 11. Approvals & Stakeholders

| Role                  | Name              | Sign-off |
| --------------------- | ----------------- | -------- |
| Product Owner         | Ashish Patel, CEO | ☐        |
| Engineering Lead      | \[Name]           | ☐        |
| Data Platform Owner   | \[Name]           | ☐        |
| Security & Compliance | \[Name]           | ☐        |

---
Below is the **Add-On** section to tack onto the end of your SurgeonMatch PRD—introducing a suite of **Stretch-Goal APIs** that unlock further commercial opportunities on CareSet’s full Medicare dataset.

---

## 12. Stretch-Goal APIs (Add-On)

> **Extend SurgeonMatch’s core functionality with these advanced endpoints—empowering commercial developers to build next-gen healthcare apps.**

### 12.1 High-Value Practice Finder

**GET** `/v1/highValuePractices`

* **Query Params:**

  * `diagnosisCode` (ICD-10)
  * `minCohortSize` (integer)
  * `topN` (integer)
* **Response:** Ranked list of practices with greatest treatment gaps

  ```jsonc
  [
    {
      "npi": "1234567890",
      "hcoId": "98765",
      "practiceName": "Bay Area GI Associates",
      "gapPercentage": 42.5,
      "cohortSize": 550,
      "address": "San Francisco, CA"
    },
    …
  ]
  ```

### 12.2 Part D Payer & Plan-Level Trends

**GET** `/v1/partDTrends`

* **Query Params:**

  * `drugCode` (NDC/HCPCS)
  * `dateFrom`/`dateTo` (YYYY-MM)
  * `region` (state or ZIP prefix)
* **Response:** Monthly spend & claim counts by payer and plan

  ```jsonc
  [
    {
      "month": "2025-01",
      "plan": "Plan D123",
      "payer": "UnitedHealthcare",
      "totalSpend": 1250000.00,
      "claimCount": 4500,
      "avgCost": 277.78
    },
    …
  ]
  ```

### 12.3 Referral Network Graph

**GET** `/v1/referralGraph`

* **Query Params:**

  * `npi` (anchor provider)
  * `depth` (levels of referrals)
  * `minSharedPatients` (integer)
* **Response:** Nodes and edges for provider-to-provider referral graph

  ```jsonc
  {
    "nodes": [
      { "npi": "1111111111", "name": "Dr. A" },
      …
    ],
    "edges": [
      { "from": "1111111111", "to": "2222222222", "sharedPatients": 120 },
      …
    ]
  }
  ```

### 12.4 Patient Adherence & Refill Metrics

**GET** `/v1/adherence`

* **Query Params:**

  * `npi` or `hcoId`
  * `drugCode`
  * `period` (e.g., last 6 months)
* **Response:** Adherence stats (PDC, refill gaps, non-adherent %)

  ```jsonc
  {
    "provider": "1234567890",
    "drugCode": "00071-0150-01",
    "pdc": 0.82,
    "avgRefillGapDays": 12.4,
    "nonAdherentPct": 18.5
  }
  ```

### 12.5 Cohort Segmentation Service

**POST** `/v1/cohortSegments`

* **Body:**

  ```jsonc
  { 
    "diagnosisCode": "E11.9",
    "features": ["ageGroup","comorbidityCount","geography","treatmentLine"],
    "segmentCount": 4
  }
  ```
* **Response:**

  ```jsonc
  [
    { "segmentId": 1, "criteria": {"ageGroup":"65–74","comorbidityCount":">=2"}, "size": 12000 },
    …
  ]
  ```

### 12.6 Cost-of-Care & Out-of-Pocket Tracker

**GET** `/v1/costOfCare`

* **Query Params:**

  * `drugCode`
  * `region`
* **Response:**

  ```jsonc
  {
    "region": "94103",
    "totalCost": 950000.00,
    "avgPatientOOP": 82.50,
    "patientSharePct": 14.8
  }
  ```

---

**These stretch-goal APIs** enable CareSet to:

* Guide pharma to untapped practices via **gap analysis**
* Monitor **Part D** formulary & spend trends in real time
* Visualize **referral networks** for provider collaboration insights
* Power **patient adherence** & cost-forecasting tools
* Automate **cohort segmentation** for targeted analytics
* Forecast **financial burden** for patients

Integrate any subset of these endpoints in a later sprint to offer richer, commercial-grade developer experiences on top of CareSet’s census-level claims data.
