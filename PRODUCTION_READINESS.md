# Tradeskee Production Readiness Plan

This document turns the current prototype into a dependable production application. Complete the phases in order. Do not add more data sources or LLM features until the earlier phase is working in staging.

## Current Status

Tradeskee currently has:

- A FastAPI backend in `src/`
- A React frontend in `tradely/`
- MongoDB integration
- Alpha Vantage and LLM integrations
- Dockerfiles and GitHub Actions checks
- Basic backend integration tests and frontend build checks

The project is not yet production-ready. The first priority is to make one complete stock-data workflow reliable from frontend request to stored response.

## Important Clarification

### AWS infrastructure

AWS is not currently implemented. `src/core/config.py` contains a few AWS-related environment fields, but the repository does not yet contain AWS infrastructure, Terraform/CDK, IAM policies, VPC configuration, deployment manifests, or an AWS CI/CD pipeline.

The recommended initial AWS target is:

```text
Route 53 -> CloudFront -> S3
						 |
						 +-> Application Load Balancer -> ECS Fargate API
															   |
						 MongoDB Atlas <-----------------------+
						 ElastiCache Redis <-------------------+
						 AWS Secrets Manager
						 CloudWatch + X-Ray/Sentry
```

Use managed services first rather than operating MongoDB or Redis on EC2. A practical AWS implementation should include:

- S3 and CloudFront for the React frontend
- ECS Fargate behind an Application Load Balancer for the FastAPI container
- MongoDB Atlas with private networking where available, or DocumentDB only after compatibility testing
- ElastiCache for Redis-backed caching, queues, and rate limiting
- Secrets Manager for API keys, database credentials, JWT secrets, and LLM credentials
- IAM task roles with least-privilege permissions; do not put long-lived AWS keys in application environment variables
- A VPC with private subnets for ECS, Redis, and database access, plus public subnets only for the load balancer
- CloudWatch logs, metrics, alarms, and deployment health checks
- ECR for versioned backend images
- GitHub Actions with OIDC federation to AWS, so CI does not store a permanent AWS access key
- Terraform or AWS CDK for repeatable infrastructure changes

Do not begin with production deployment until a staging AWS environment can be created from code, destroyed safely, and recreated without manual console configuration.

### Application security

Security is not fully implemented in the current application. The roadmap below describes the controls that must be added and tested. Existing configuration fields such as `SECRET_KEY`, `ALLOWED_API_KEYS`, and `RATE_LIMIT_PER_MINUTE` do not provide protection by themselves because the current routes do not consistently enforce them.

Before public release, the application must have at least:

- Authentication and authorization on protected endpoints
- Production-only secret validation and secret rotation
- TLS at the load balancer and secure cookie/token settings where applicable
- Strict CORS allowlists and security headers
- Redis-backed rate limiting and abuse controls
- Input validation, request-size limits, and safe error responses
- Dependency, container, and secret scanning in CI
- Audit logging for authentication and sensitive actions
- Centralized logs with request IDs and alerting
- Backups, restore testing, and a documented incident response process

The security controls must be verified by automated tests and a pre-release security review. A deployed HTTPS endpoint alone is not sufficient to call the application secure.

## Definition Of Done

A release is ready for production only when:

- The backend and frontend build in CI.
- The backend Docker image builds and starts from a clean checkout.
- Staging uses production-like environment variables and services.
- Readiness checks verify required dependencies.
- Authentication, authorization, rate limiting, and CORS restrictions are enabled.
- External API failures, timeouts, and stale data are handled explicitly.
- The main user workflow has unit, integration, and end-to-end coverage.
- Logs, metrics, error tracking, backups, and rollback procedures are in place.
- Security and dependency scans pass.
- No production secret is stored in the repository.

## Phase 1: Make The Existing Application Deployable

### 1. Fix the container definition

Update `Dockerfile` so it only copies files that exist. The current file attempts to copy a root-level `config.py`, but configuration lives in `src/core/config.py`.

Verify locally:

```bash
docker build -t tradeskee-backend .
docker run --rm -p 8000:8000 --env-file .env tradeskee-backend
curl http://localhost:8000/health
```

Acceptance criteria:

- The image builds from a clean checkout.
- The container runs as a non-root user.
- `/health` returns HTTP 200.
- No secret is baked into the image.

### 2. Consolidate configuration

Use `src/core/config.py` as the single source of truth.

Replace direct calls to `os.getenv()` and `load_dotenv()` in application code with the settings object. In particular, standardize:

- `MONGODB_URL`
- `MONGODB_DB_NAME`
- `ALPHA_VANTAGE_API_KEY`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`

Remove conflicting names such as `MONGO_URI` and `MONGODB_URI` unless they are deliberately supported as migration aliases.

Production settings must:

- Reject the default secret key.
- Reject the `demo` Alpha Vantage key.
- Require a valid database URL.
- Disable debug mode.
- Use explicit production CORS origins.

Add tests for missing and invalid production configuration.

### 3. Fix the frontend/backend API contract

The backend mounts stock routes below `/api/v1/stocks`. The frontend API client currently calls paths such as `/analyze_all/...` directly.

Choose one consistent contract. Recommended frontend configuration:

```text
REACT_APP_API_BASE_URL=https://api.example.com/api/v1/stocks
```

Then verify every frontend request against the generated OpenAPI document:

```bash
curl http://localhost:8000/api/v1/openapi.json
```

Acceptance criteria:

- The frontend can load metadata, news, market prices, and analysis against staging.
- No request depends on a localhost URL in a production build.
- API errors produce useful UI error states.

### 4. Add a local service environment

Create a `docker-compose.yml` for local development and staging-like testing with:

- backend
- MongoDB
- Redis
- optional Ollama service

Use named volumes for MongoDB data. Keep secrets in an untracked `.env` file or a secret manager.

## Phase 2: Stabilize Runtime Behavior

### 1. Use managed application lifecycles

Create FastAPI lifespan handlers to:

- create one MongoDB client
- verify the MongoDB connection
- create one shared async HTTP client
- initialize Redis when configured
- close all clients during shutdown

Do not create database or network clients at module import time.

### 2. Remove blocking network calls

`stock_services.py` uses synchronous `requests` calls inside async functions. Replace them with `httpx.AsyncClient`.

Every external request must define:

- connection timeout
- read timeout
- maximum retries
- exponential backoff
- handling for HTTP 429, 5xx, invalid JSON, and provider error payloads

Do not retry permanent errors such as invalid ticker symbols or authentication failures.

### 3. Separate liveness and readiness

Keep `/health` as a cheap process liveness check.

Add `/ready` that checks the dependencies required for serving requests:

- MongoDB
- Redis, if enabled
- required provider configuration

Return HTTP 503 when the application cannot serve traffic. Do not expose connection strings or credentials in the response.

### 4. Validate request input

Add typed request and response models for all routes.

Validate:

- ticker format
- question length
- context length
- all `limit` values with minimum and maximum bounds
- supported date ranges

Return consistent validation errors. Do not pass unvalidated user input into provider URLs or LLM prompts.

### 5. Make expensive analysis asynchronous

The `analyze_all` endpoint currently performs multiple upstream calls and an LLM request in one HTTP request.

Change it to:

1. Create an analysis job.
2. Return a job ID with HTTP 202.
3. Process the job in a worker.
4. Persist status, errors, timestamps, and results.
5. Expose a status/result endpoint.
6. Allow cancellation or expiry for abandoned jobs.

Use a queue backed by Redis or a managed job system. Do not rely on in-process background tasks when multiple workers will run.

## Phase 3: Add Security Controls

### 1. Authentication and authorization

Define the user model and permissions before adding user-specific saved analyses.

Implement:

- authenticated API access
- password or external identity provider flow
- secure password hashing if passwords are stored
- access tokens with expiry and rotation
- authorization checks on saved analyses and user data

Keep public health and documentation access intentional. Protect data and analysis endpoints by default.

### 2. API protection

Implement and test:

- rate limiting per user and IP
- request body size limits
- CORS allowlists
- security response headers
- request correlation IDs
- audit logs for authentication and sensitive operations

Use Redis for rate limits when running more than one backend worker.

### 3. Secrets and dependencies

Store production secrets in the deployment platform's secret manager. Rotate all credentials before the first public release.

Add CI checks for:

- secret scanning
- dependency vulnerabilities
- outdated base images
- Python and npm lockfile integrity

Pin direct dependencies and remove duplicate or unused entries from `requirements.txt`.

## Phase 4: Improve Data And Analysis Trustworthiness

Every displayed result should include:

- provider/source
- retrieval timestamp
- data period
- whether the value is live, cached, or stale
- any provider limitation or missing field

Store the source data and analysis metadata needed to reproduce an LLM result:

- analysis ID
- model name and version
- prompt version
- source data version
- creation time

Treat provider responses as untrusted input. Validate and normalize them before storing or displaying them.

Add a clear financial-information disclaimer. LLM output must not present predictions, fabricated sources, or unsupported claims as facts.

## Phase 5: Build A Real Test Strategy

### Backend tests

Add tests for:

- settings validation in development, staging, and production
- all service success and failure paths
- provider timeouts and rate limits
- response parsing and normalization
- MongoDB repositories
- authentication and authorization
- rate limiting
- readiness failures
- analysis job lifecycle

Mock provider calls in unit tests. Use disposable MongoDB and Redis services for integration tests.

### API contract tests

Validate that:

- every frontend request maps to a backend route
- response models match the OpenAPI schema
- error responses have a stable shape
- breaking API changes require a version change

### Frontend tests

Cover:

- loading states
- empty states
- provider/API errors
- analysis job polling
- stale data indicators
- responsive layouts
- accessible keyboard and screen-reader behavior

### CI requirements

GitHub Actions should run:

```bash
# Backend
pytest --cov=src --cov-fail-under=80
black --check src tests
isort --check-only src tests
flake8 src tests
mypy src

# Frontend
cd tradely
npm ci
npm run lint
npm run format:check
npm test -- --watchAll=false
npm run build
```

CI should also build the Docker image and run integration tests with MongoDB and Redis service containers.

## Phase 6: Observability And Operations

Add:

- structured JSON logs
- request ID on every request and log entry
- latency and error metrics
- provider call counts, latency, and failure rates
- analysis job duration and failure metrics
- error tracking such as Sentry
- dashboards and alerts

Create runbooks for:

- provider outage
- database outage
- Redis outage
- elevated error rate
- credential rotation
- rollback
- restoring a database backup

Configure:

- automated MongoDB backups
- tested restore procedures
- log retention
- health-check-based deployment rollback
- separate development, staging, and production environments

## Recommended Release Sequence

### Release 1: Reliable stock data

- Fix Docker and configuration mismatches.
- Fix frontend route configuration.
- Add managed MongoDB and HTTP clients.
- Replace blocking HTTP calls.
- Add bounded inputs and typed responses.
- Add real MongoDB integration tests.

### Release 2: Protected service

- Add authentication.
- Enforce rate limits.
- Add readiness checks.
- Add structured errors and security headers.
- Add Redis-backed caching and rate limiting.

### Release 3: Asynchronous analysis

- Add the analysis job model and worker.
- Persist reproducible analysis metadata.
- Add job status and result endpoints.
- Add end-to-end coverage for the analysis workflow.

### Release 4: Production operations

- Deploy staging.
- Add monitoring, alerting, backups, and runbooks.
- Perform load, failure, and security testing.
- Complete a rollback rehearsal.
- Deploy a limited production release and monitor it.

## First Week Checklist

- [ ] Fix the invalid `config.py` copy in `Dockerfile`.
- [ ] Standardize MongoDB environment variables and database name.
- [ ] Remove import-time API key validation.
- [ ] Align frontend API paths with `/api/v1/stocks`.
- [ ] Add bounded query parameters.
- [ ] Add a `/ready` endpoint.
- [ ] Add MongoDB to CI as a service.
- [ ] Add mocked tests for one complete stock metadata flow.
- [ ] Add Docker image build to CI.
- [ ] Update `README.md` with local, staging, and production run instructions.

Do not call the application production-ready until the Definition Of Done at the top of this document is satisfied.

## Flexible Learning Roadmap

Use this as a sequence of learning blocks rather than a fixed delivery schedule. Each block is expected to take roughly one to two weeks when worked on part-time. Spend less time when the topic is familiar and more time when the practical exercise exposes gaps. The important rule is to finish the learning exercise and acceptance criteria before moving to the next block.

### Before Starting: Learn The Shape Of The System

Suggested time: 2 to 3 focused sessions.

Read up on:

- FastAPI application structure, dependency injection, lifespan events, and response models
- Twelve-Factor App configuration and environment management
- Docker images, containers, health checks, and non-root users
- HTTP fundamentals: status codes, timeouts, retries, idempotency, and reverse proxies
- MongoDB connection pooling and indexes

Suggested official reading:

- [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/)
- [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [The Twelve-Factor App](https://12factor.net/)
- [Docker get started](https://docs.docker.com/get-started/)
- [MongoDB data modeling and relationships](https://www.mongodb.com/docs/manual/data-modeling/)

Learning exercise:

1. Draw the request path from the React component to the FastAPI route, service, external provider, and database.
2. Run the current frontend and backend locally.
3. Write down every configuration value and external dependency required by one stock endpoint.
4. Identify which parts are synchronous, asynchronous, cached, or persisted.

Exit criteria:

- You can explain the main request path without looking at the code.
- You can identify where a request can fail and what the user currently sees.
- You have selected one small stock-data workflow as the learning project.

### Block 1: Make One Workflow Deployable

Suggested time: weeks 1 to 2, with flexibility.

Focus on Docker, configuration, and the frontend/backend API contract. Complete Phase 1, but limit the scope to one workflow such as stock metadata.

Read up on:

- Docker multi-stage builds and image hardening
- Pydantic Settings and environment-specific configuration
- OpenAPI as an API contract
- React environment variables and production builds

Learning exercise:

- Fix the Dockerfile and build the image.
- Make one frontend request work against the versioned backend route.
- Add a typed backend response model and a frontend loading/error state.
- Document the workflow from local startup to successful response.

Exit criteria:

- A clean checkout can build and run the selected workflow.
- Configuration is supplied externally.
- The frontend and backend agree on the route and response shape.

### Block 2: Make The Runtime Reliable

Suggested time: weeks 3 to 4, with flexibility.

Focus on async I/O, lifecycle management, retries, readiness, and input validation.

Read up on:

- Async Python and why blocking I/O harms an async web server
- Timeout and retry design
- FastAPI dependency injection and lifespan management
- MongoDB indexes and connection pools
- Redis caching fundamentals

Suggested official reading:

- [HTTPX async support](https://www.python-httpx.org/async/)
- [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [Redis caching patterns](https://redis.io/docs/latest/develop/use/patterns/)

Learning exercise:

- Replace one `requests` call with a managed async HTTP client.
- Add tests for timeout, provider rate limit, and malformed provider data.
- Add `/ready` and deliberately make a dependency unavailable to observe the result.
- Measure the selected endpoint before and after removing blocking I/O.

Exit criteria:

- Dependencies are created and closed predictably.
- External failures produce stable application errors.
- Invalid inputs are rejected before reaching providers.
- Readiness accurately represents whether the service can handle traffic.

### Block 3: Apply Real Application Security

Suggested time: weeks 5 to 7, with flexibility.

Focus on authentication, authorization, secrets, rate limiting, safe errors, and security testing. Treat this as implementation work, not a checklist exercise.

Read up on:

- OWASP Top 10
- Authentication versus authorization
- Password hashing and token expiry
- CORS, CSRF, XSS, SSRF, and injection risks
- Threat modeling and least privilege
- Secure secret storage and rotation

Suggested official reading:

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
- [OWASP threat modeling](https://owasp.org/www-community/Threat_Modeling)
- [FastAPI security](https://fastapi.tiangolo.com/tutorial/security/)

Learning exercise:

1. Write a short threat model for the stock-analysis workflow.
2. List assets, users, trust boundaries, abuse cases, and mitigations.
3. Protect one endpoint and test unauthenticated, authenticated, and unauthorized requests.
4. Add rate-limit tests and verify that secrets never appear in logs or error responses.

Exit criteria:

- You can explain why each security control exists.
- Protected routes fail closed.
- Security behavior is covered by automated tests.
- A dependency or secret scan runs in CI.

### Block 4: Introduce AWS Infrastructure

Suggested time: weeks 8 to 10, with flexibility.

Focus on deploying a staging environment using infrastructure as code. Do not start with production credentials or a large multi-service design.

Read up on:

- AWS IAM, VPCs, security groups, and private subnets
- ECS Fargate, ECR, Application Load Balancers, and health checks
- S3 and CloudFront static hosting
- Secrets Manager and IAM task roles
- GitHub Actions OIDC federation
- Terraform or AWS CDK state and change management

Suggested official reading:

- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
- [Amazon ECS on AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [AWS IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GitHub Actions AWS OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [Terraform AWS provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

Learning exercise:

- Build a minimal staging environment from code.
- Deploy the backend image to ECS and the frontend to S3/CloudFront.
- Put secrets in Secrets Manager and grant only the task role the permissions it needs.
- Destroy and recreate the environment to prove it is reproducible.

Exit criteria:

- No long-lived AWS access key is stored in GitHub.
- The API is reachable through HTTPS and passes load-balancer health checks.
- Logs and deployment failures are visible.
- The staging environment can be recreated without undocumented console steps.

### Block 5: Test The Product Workflow

Suggested time: weeks 11 to 12, with flexibility.

Focus on integration, contract, frontend, and end-to-end testing.

Read up on:

- Test pyramid and test boundaries
- Contract testing with OpenAPI
- Test doubles and provider fakes
- Playwright browser testing
- Load and failure testing

Learning exercise:

- Test the complete workflow against disposable MongoDB and Redis services.
- Add a browser test for loading a ticker and handling an upstream failure.
- Add a Docker build and staging smoke test to CI.
- Set a coverage threshold for important backend modules rather than chasing a number everywhere.

Exit criteria:

- CI catches broken routes, response shapes, and critical user journeys.
- Tests do not depend on live Alpha Vantage or LLM services.
- The staging deployment has an automated smoke test.

### Block 6: Operate It Safely

Suggested time: weeks 13 to 14, with flexibility.

Focus on observability, backups, incident response, cost awareness, and release discipline.

Read up on:

- Structured logging and correlation IDs
- Metrics, traces, alert thresholds, and SLOs
- Database backup and restore testing
- Blue/green or rolling deployments
- Incident response and post-incident reviews

Learning exercise:

- Create one dashboard for availability, latency, provider failures, and analysis jobs.
- Trigger an alert using a controlled failure.
- Restore a backup in a non-production environment.
- Perform a rollback rehearsal and record the commands needed.

Exit criteria:

- You can detect, investigate, and recover from the main failure modes.
- Backups have been restored successfully, not merely configured.
- A release can be rolled back without improvising under pressure.

## A Practical Learning Loop

For each block:

1. Read only enough to understand the problem and vocabulary.
2. Write a short design note in your own words.
3. Make the smallest change that demonstrates the concept.
4. Add a test or measurement that could prove the change wrong.
5. Deploy or run it in an environment close to the real one.
6. Review the result and record what you would change next time.

Keep a small engineering journal with four headings: `What I expected`, `What happened`, `What I learned`, and `Next experiment`. This turns production work into deliberate practice rather than copying infrastructure patterns without understanding them.

Do not advance because a calendar date has arrived. Advance when you can explain the design, demonstrate it working, and show how it fails.
