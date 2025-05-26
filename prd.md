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
