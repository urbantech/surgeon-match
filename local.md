# SurgeonMatch Project Standards

## 1. Project Overview
SurgeonMatch is a high-performance API service that matches Medicare patients with available surgeons based on specialty, location, and availability. The system is built with FastAPI, PostgreSQL, and Redis, emphasizing performance, reliability, and data accuracy.

## 2. Backlog Management
We use GitHub Issues with the following workflow:

### Workflow States
- **To Do**: Newly created issues
- **In Progress**: Actively being worked on
- **In Review**: Code review in progress
- **Done**: Completed and verified

### Branch Naming
- `feature/{issue-id}-short-description` for new features
- `bugfix/{issue-id}-short-description` for bug fixes
- `hotfix/{issue-id}-short-description` for critical production fixes

## 3. Development Standards

### 3.1 Code Style
- Python code follows PEP 8 with Black formatter
- SQL uses UPPERCASE for keywords
- Maximum line length: 100 characters
- Use type hints for all function parameters and returns

### 3.2 Testing
- Write tests for all new features and bug fixes
- Aim for 80%+ test coverage
- Use pytest for unit and integration tests
- Mock external services in unit tests
- Test data must be reset after each test

### 3.3 API Design
- Follow RESTful principles
- Use kebab-case for URLs
- Use camelCase for JSON properties
- Version all APIs (e.g., `/v1/endpoint`)
- Document all endpoints with OpenAPI

## 4. Database Standards

### 4.1 Schema Changes
- All schema changes must be made through Alembic migrations
- Include both `upgrade` and `downgrade` paths
- Test migrations on a staging environment before production

### 4.2 Query Optimization
- Use SQLAlchemy's ORM for simple queries
- Use raw SQL for complex analytics
- Add appropriate indexes for frequently queried columns
- Use `EXPLAIN ANALYZE` for optimizing slow queries

## 5. Performance Requirements

### 5.1 API Response Times
- P99 latency < 500ms
- Median latency < 200ms
- Maximum response time: 2s

### 5.2 Caching Strategy
- Cache responses for 1 hour by default
- Use Redis for caching
- Invalidate cache on data updates
- Use cache keys with appropriate namespacing

## 6. Security Standards

### 6.1 Authentication
- Use API keys for service-to-service communication
- Rotate API keys quarterly
- Never commit API keys to version control

### 6.2 Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Implement rate limiting (100 requests/minute per API key)
- Log all access to sensitive data

## 7. Documentation

### 7.1 API Documentation
- Maintain OpenAPI specification
- Include example requests and responses
- Document error codes and messages

### 7.2 Project Documentation
- Keep README.md updated
- Document environment setup
- Include deployment instructions

## 8. Deployment

### 8.1 Environments
- Development
- Staging
- Production

### 8.2 CI/CD
- Run tests on every push
- Deploy to staging on merge to main
- Manual approval for production deployments

## 9. Monitoring and Logging

### 9.1 Logging
- Structured JSON logging
- Include request IDs for tracing
- Log all API requests and responses

### 9.2 Monitoring
- Monitor error rates
- Set up alerts for high latency
- Track API usage and performance

## 10. Compliance
- HIPAA compliance for handling PHI
- Regular security audits
- Maintain audit logs for all data access
