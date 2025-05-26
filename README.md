# SurgeonMatch API Suite

> A high-performance API for matching Medicare patients with available surgeons based on specialty, location, and availability.

[![CI/CD](https://github.com/urbantech/surgeon-match/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/urbantech/surgeon-match/actions/workflows/ci-cd.yml)

---

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/urbantech/surgeon-match.git
   cd surgeon-match
   ```

2. **Run with Docker Compose**

   ```bash
   docker-compose up -d
   ```

   This will start three containers:
   - PostgreSQL database
   - Redis for caching and rate limiting
   - SurgeonMatch API server

3. **Access the API**

   The API will be available at http://localhost:8888
   
   Swagger UI documentation: http://localhost:8888/docs
   
   ReDoc alternative documentation: http://localhost:8888/redoc

### Manual Setup (Alternative)

1. **Create a Virtual Environment & Install Dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**

   Create a `.env` file in the project root or export variables directly:
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/surgeonmatch
   REDIS_URL=redis://localhost:6379/0
   DEBUG=true
   API_KEY_HEADER=X-API-Key
   API_PREFIX=/api/v1
   SECRET_KEY=your-super-secret-key-change-in-production
   RATE_LIMIT=100
   RATE_LIMIT_PERIOD=60
   ```

3. **Run Database Migrations**

   ```bash
   alembic upgrade head
   ```

4. **Create Initial API Key**

   ```bash
   python scripts/create_initial_api_key.py
   ```

5. **Start the Server**

   ```bash
   uvicorn surgeonmatch.main:app --host 0.0.0.0 --port 8888 --reload
   ```

---

## 📚 API Documentation

### Authentication

All API requests require authentication using an API key in the header:

```
X-API-Key: your-api-key
```

### Rate Limiting

The API is rate-limited to protect against abuse. Default limits are:
- 100 requests per minute per API key

### Core Endpoints

#### Surgeons API

- `GET /api/v1/surgeons` - List all surgeons with pagination and filtering
- `GET /api/v1/surgeons/{id}` - Get surgeon details by ID
- `GET /api/v1/surgeons/npi/{npi}` - Get surgeon details by NPI number
- `GET /api/v1/surgeons/search` - Search surgeons by name, specialty, or location

#### Claims API

- `GET /api/v1/claims` - List all claims with pagination and filtering
- `GET /api/v1/claims/{id}` - Get claim details by ID
- `GET /api/v1/claims/surgeon/{surgeon_id}` - Get claims for a specific surgeon

#### Quality Metrics API

- `GET /api/v1/quality-metrics` - List all quality metrics with pagination and filtering
- `GET /api/v1/quality-metrics/{id}` - Get quality metric details by ID
- `GET /api/v1/quality-metrics/surgeon/{surgeon_id}` - Get quality metrics for a specific surgeon

#### API Keys

- `GET /api/v1/api-keys` - List all API keys (admin only)
- `POST /api/v1/api-keys` - Create a new API key (admin only)
- `DELETE /api/v1/api-keys/{id}` - Delete an API key (admin only)

### Response Format

All API responses are in JSON format and follow this structure:

```json
{
  "data": { ... },  // Requested data or array of items
  "meta": {         // Metadata about the request/response
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

### Error Handling

Errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }  // Optional additional error details
  }
}
```

## 🧪 Testing

SurgeonMatch has several test scripts to validate functionality:

```bash
# Run HTTP-based API tests
python scripts/test_api_http.py

# Run curl-based API tests
./scripts/test_api_curl.sh

# Run validation against database
python scripts/final_validation.py
```

## 🔧 Development Guidelines

### Code Style

- Python code follows PEP 8 with Black formatter (line length: 100 characters)
- Use type hints for all function parameters and return values
- Use docstrings for all public functions, classes, and modules
- SQL keywords should be in UPPERCASE

### Git Workflow

- Branch naming convention:
  - `feature/{issue-id}-short-description` for new features
  - `bugfix/{issue-id}-short-description` for bug fixes
  - `hotfix/{issue-id}-short-description` for critical production fixes

- Create WIP commits for incremental progress
- All PRs must have descriptive titles and detailed descriptions
- Squash commits when merging to main

### Testing

- Write tests for all new features and bug fixes
- Aim for 80%+ test coverage
- Use pytest for unit and integration tests
- Mock external services in unit tests
- Reset test data after each test

### Database

- All schema changes must be made through Alembic migrations
- Include both `upgrade` and `downgrade` paths in migrations
- Test migrations on staging before production
- Use SQLAlchemy's ORM for simple queries
- Use raw SQL for complex analytics
- Add appropriate indexes for frequently queried columns

### API Design

- Follow RESTful principles
- Use kebab-case for URLs
- Use camelCase for JSON properties
- Version all APIs (e.g., `/api/v1/endpoint`)
- Document all endpoints with OpenAPI

### Performance

- P99 latency < 500ms
- Median latency < 200ms
- Maximum response time: 2s
- Cache responses for 1 hour by default
- Use Redis for caching
- Invalidate cache on data updates

---

## 🛡️ Security Guidelines

### Authentication

- Use API keys for service-to-service communication
- Rotate API keys quarterly
- Never commit API keys to version control
- Store keys securely in the database with appropriate hashing

### Data Protection

- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Implement rate limiting (default: 100 requests/minute per API key)
- Log all access to sensitive data

### HIPAA Compliance

- Maintain audit logs for all data access
- Implement access controls based on need-to-know principles
- Store only minimal required PHI
- Regular security audits and vulnerability scanning

## 🔥 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 👮 License

This project is licensed under the terms of the MIT license. See the LICENSE file for details.

---

Built with ❤️ by the SurgeonMatch team

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
