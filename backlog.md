## Epic 1: Authentication & API Gateway

Prepare the foundation for secure, rate-limited API access.

1. **User Story 1.1: API Key Validation**

   * **As** an external developer
   * **I want** to include my API key in each request header
   * **So that** the gateway can authenticate and authorize my calls
   * **Acceptance Criteria:**

     * Requests missing or invalid keys return `401 Unauthorized`
     * Valid keys pass through to service

2. **User Story 1.2: Rate Limiting**

   * **As** an API consumer
   * **I want** my requests limited to 100/min
   * **So that** the service remains performant and available for all users
   * **Acceptance Criteria:**

     * Excess requests return `429 Too Many Requests` with a `Retry-After` header

---

## Epic 2: Surgeon Directory API

Enable geospatial and specialty-based surgeon lookups.

1. **User Story 2.1: Basic Directory Endpoint**

   * **As** a mobile app developer
   * **I want** `GET /v1/surgeons`
   * **So that** I can retrieve a list of surgeons
   * **Acceptance Criteria:**

     * Returns JSON array of surgeon objects
     * Each object matches the approved schema (`npi`, `name`, `specialty_code`, `latitude`, `longitude`, `claim_volume_6mo`, `quality_score`)

2. **User Story 2.2: Geospatial Filtering**

   * **As** a care coordinator
   * **I want** to filter by `lat`, `lng`, `radiusMiles`
   * **So that** I only see surgeons within my area
   * **Acceptance Criteria:**

     * Surgeons beyond the radius are excluded
     * Edge-case: radius = 0 returns only surgeons at exactly that point

3. **User Story 2.3: Specialty & Volume Filters**

   * **As** a pharma marketer
   * **I want** to filter by `specialtyCode` and `minClaimVolume`
   * **So that** I target high-volume specialists
   * **Acceptance Criteria:**

     * Only surgeons matching both filters appear
     * Invalid codes or negative volumes return `400 Bad Request`

4. **User Story 2.4: Medicare Acceptance Flag**

   * **As** a patient advocate
   * **I want** to filter by `acceptsMedicare=true`
   * **So that** I only see providers who will accept my coverage
   * **Acceptance Criteria:**

     * Passing `acceptsMedicare=false` returns providers who do not

---

## Epic 3: Patient Journey API

Expose cohort-level disease progression insights.

1. **User Story 3.1: Journey Summary Endpoint**

   * **As** a front-end engineer
   * **I want** `GET /v1/patientJourneys?diagnosisCode=XXX&cohortSize=Y`
   * **So that** I can visualize typical care pathways
   * **Acceptance Criteria:**

     * Returns `diagnosis_code`, `cohort_size`, `avg_time_to_surgery`, and `therapy_sequence` array
     * Invalid ICD-10 codes produce `404 Not Found`

2. **User Story 3.2: Cohort Size Validation**

   * **As** a user
   * **I want** `cohortSize` to be between 100 and 1,000,000
   * **So that** the system remains performant
   * **Acceptance Criteria:**

     * Out-of-range values return `400 Bad Request` with an explanatory message

---

## Epic 4: Surgeon Availability Inquiry API

Check who is on-call or available on a given date.

1. **User Story 4.1: Availability Inquiry Endpoint**

   * **As** an emergency coordinator
   * **I want** `POST /v1/availabilityInquiry`
   * **So that** I can check multiple NPIs for availability on `requestedDate`
   * **Acceptance Criteria:**

     * Accepts JSON body with `npiList` (array) and `requestedDate` (ISO-8601 date)
     * Returns an array of `{ npi, available, notes }`

2. **User Story 4.2: Cache Lookup & Fallback**

   * **As** an API maintainer
   * **I want** availability results cached for 1 hr
   * **So that** repeated queries are fast and do not overload external services
   * **Acceptance Criteria:**

     * If cache hit, returns cached response
     * On cache miss, calls external scheduling system, stores result, returns new data

---

## Epic 5: Surgeon Outcomes & Quality API

Surface readmission, complication, and LOS metrics.

1. **User Story 5.1: Quality Metrics Endpoint**

   * **As** a data scientist
   * **I want** `GET /v1/surgeonQuality/{npi}`
   * **So that** I can retrieve quality metrics for that surgeon
   * **Acceptance Criteria:**

     * Returns `{ npi, procedure_code, readmission_rate_30d, complication_rate, avg_length_of_stay }`
     * Invalid or unknown `npi` yields `404 Not Found`

2. **User Story 5.2: Procedure Code Filtering**

   * **As** a clinical analyst
   * **I want** to optionally filter by `procedureCode` query param
   * **So that** I can get metrics for a specific surgery type
   * **Acceptance Criteria:**

     * Returns only the matching composite record
     * Multiple codes → multiple array entries

---

## Epic 6: Documentation, SDKs & Examples

1. **User Story 6.1: OpenAPI Spec & Swagger UI**

   * **As** a developer
   * **I want** interactive API docs
   * **So that** I can explore endpoints and test them directly
   * **Acceptance Criteria:**

     * All endpoints documented, with models and example requests/responses

2. **User Story 6.2: SDK Snippets**

   * **As** a third-party dev
   * **I want** ready-to-use Python and JavaScript examples
   * **So that** I can integrate quickly
   * **Acceptance Criteria:**

     * Snippets cover authentication, each endpoint, error handling

3. **User Story 6.3: Postman Collection**

   * **As** a QA engineer
   * **I want** a Postman collection
   * **So that** I can automate exploratory testing
   * **Acceptance Criteria:**

     * Contains all endpoints, pre-configured with environment variables

---

## Epic 7: Testing & QA

1. **User Story 7.1: Unit Tests for Each Endpoint**

   * **As** a developer
   * **I want** pytest/Jest tests for edge cases and happy-paths
   * **So that** regressions are caught early
2. **User Story 7.2: Integration Tests in Staging**

   * **As** a QA lead
   * **I want** automated smoke tests against the staging deployment
   * **So that** I can verify end-to-end functionality

---

## Epic 8: Deployment & Monitoring

1. **User Story 8.1: CI/CD Pipeline**

   * **As** DevOps
   * **I want** pushes to `develop` auto-deploy to staging, pushes to `main` auto-deploy to prod
2. **User Story 8.2: Monitoring & Alerts**

   * **As** an SRE
   * **I want** Datadog dashboards for latency & error-rates, plus PagerDuty alerts on anomalies

---
