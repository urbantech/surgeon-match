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
Here’s an **Add-On Backlog** of Epics and User Stories covering the Stretch-Goal APIs. You can slot these into your main backlog to plan a follow-up sprint.

---

## Epic 9: High-Value Practice Finder

Identify provider practices with the greatest treatment gaps for precision outreach.

* **User Story 9.1: High-Value Practices Endpoint**

  * **As** a pharma marketer
  * **I want** `GET /v1/highValuePractices?diagnosisCode=&minCohortSize=&topN=`
  * **So that** I can retrieve the top practices with the largest unmet need
  * **Acceptance Criteria:**

    * Returns array of `{ npi, hcoId, practiceName, gapPercentage, cohortSize, address }`
    * Supports pagination (`limit`/`offset`)

* **User Story 9.2: Gap Calculation Job**

  * **As** a data engineer
  * **I want** a daily batch job that computes `gapPercentage = 1 – (treatedCount/cohortSize)`
  * **So that** the API can serve pre-computed values quickly
  * **Acceptance Criteria:**

    * Job writes to `high_value_practices` table
    * Completes within nightly maintenance window

---

## Epic 10: Part D Payer & Plan-Level Trends

Power dashboards tracking drug spend and claim counts by plan.

* **User Story 10.1: Part D Trends Endpoint**

  * **As** a data analyst
  * **I want** `GET /v1/partDTrends?drugCode=&dateFrom=&dateTo=&region=`
  * **So that** I can chart Part D spend & claims over time by payer/plan
  * **Acceptance Criteria:**

    * Returns array of `{ month, plan, payer, totalSpend, claimCount, avgCost }`
    * Supports filtering by date range and region

* **User Story 10.2: Trends Aggregation Pipeline**

  * **As** a backend engineer
  * **I want** a scheduled ETL that aggregates monthly Part D metrics into `part_d_trends`
  * **So that** the endpoint can return queried data in <200ms
  * **Acceptance Criteria:**

    * ETL runs monthly, writing to `part_d_trends` table
    * Logs success/failure and alert on errors

---

## Epic 11: Referral Network Graph

Expose provider referral relationships for network visualizations.

* **User Story 11.1: Referral Graph Endpoint**

  * **As** a developer
  * **I want** `GET /v1/referralGraph?npi=&depth=&minSharedPatients=`
  * **So that** I can render a network graph of provider referrals
  * **Acceptance Criteria:**

    * Returns `{ nodes: […], edges: […] }` with correct weights
    * Limits depth to prevent combinatorial explosion

* **User Story 11.2: DocGraph Materialization**

  * **As** a data engineer
  * **I want** to materialize the DocGraph PUF into a `docgraph_edges` table
  * **So that** the API can query edges efficiently
  * **Acceptance Criteria:**

    * Table is kept in sync via daily refresh
    * Indexed on `(from_npi,to_npi)`

---

## Epic 12: Patient Adherence & Refill Metrics

Surface adherence statistics to drive patient-engagement tools.

* **User Story 12.1: Adherence Endpoint**

  * **As** a care coordinator
  * **I want** `GET /v1/adherence?npi=&drugCode=&period=`
  * **So that** I can retrieve PDC, refill gaps, and non-adherent percentages
  * **Acceptance Criteria:**

    * Returns `{ provider, drugCode, pdc, avgRefillGapDays, nonAdherentPct }`
    * Validates `period` format and returns `400` on error

* **User Story 12.2: Adherence Metrics ETL**

  * **As** a data engineer
  * **I want** a windowed calculation job that computes adherence metrics for `adherence_metrics`
  * **So that** our API returns pre-computed stats
  * **Acceptance Criteria:**

    * Job processes rolling windows (e.g., last 6 months)
    * Stores results with `calculated_at` timestamps

---

## Epic 13: Cohort Segmentation Service

Enable dynamic patient segmentation for advanced analytics.

* **User Story 13.1: Cohort Segmentation Endpoint**

  * **As** a data scientist
  * **I want** `POST /v1/cohortSegments` with features & segmentCount
  * **So that** I can receive algorithmically derived patient segments
  * **Acceptance Criteria:**

    * Returns array of `{ segmentId, criteria, size }`
    * Leverages simple k-means or decision trees

* **User Story 13.2: Segmentation Compute Job**

  * **As** a data engineer
  * **I want** to run the clustering algorithm on demand or schedule
  * **So that** segments can be generated for new diagnosis codes
  * **Acceptance Criteria:**

    * Job writes to `cohort_segments` table
    * Accepts arbitrary feature sets

---

## Epic 14: Cost-of-Care & Out-of-Pocket Tracker

Forecast financial burden for patients at the region level.

* **User Story 14.1: Cost-of-Care Endpoint**

  * **As** a patient support app developer
  * **I want** `GET /v1/costOfCare?drugCode=&region=`
  * **So that** I can show total vs. patient OOP costs
  * **Acceptance Criteria:**

    * Returns `{ region, totalCost, avgPatientOOP, patientSharePct }`
    * Validates region format (ZIP or state code)

* **User Story 14.2: Cost Aggregation Job**

  * **As** a data engineer
  * **I want** to aggregate cost data into `cost_of_care` daily/monthly
  * **So that** the API can return fresh numbers
  * **Acceptance Criteria:**

    * Job logs run times and errors
    * Updates `updated_at` field

---

## Epic 15: Documentation & Examples for Stretch APIs

* **User Story 15.1: OpenAPI Spec Extensions**

  * **As** a developer
  * **I want** the stretch endpoints added to Swagger UI
  * **So that** I can explore and test them interactively
* **User Story 15.2: SDK Snippets**

  * **As** a third-party dev
  * **I want** code examples for each stretch endpoint
  * **So that** I can onboard quickly
* **User Story 15.3: Postman Collection**

  * **As** a QA engineer
  * **I want** these new endpoints in our Postman collection

---

Slot these new Epics into your roadmap for subsequent sprints—each Epic can be addressed independently or in parallel to rapidly expand CareSet’s API platform.

## Epic 16: Deployment & Monitoring

1. **User Story 8.1: CI/CD Pipeline**

   * **As** DevOps
   * **I want** pushes to `develop` auto-deploy to staging, pushes to `main` auto-deploy to prod
2. **User Story 8.2: Monitoring & Alerts**

   * **As** an SRE
   * **I want** Datadog dashboards for latency & error-rates, plus PagerDuty alerts on anomalies

---
