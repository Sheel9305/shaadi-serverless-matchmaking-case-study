# Presentation Slide Deck (12 Slides)
**Topic:** Serverless Matchmaking Recommendations: A Shaadi.com Cloud Computing Case Study  
**Course:** IT457 Cloud Computing | **Group Number:** 49  
**Team:** Bhaumik Luhar (202301468) · Sheel Shah (202301420) · Nakul Patel (202301261)  

---

## Slide 1: Title & Overview
- **Title:** Serverless Matchmaking Recommendations: A Shaadi.com Cloud Case Study
- **Course:** IT457 Cloud Computing, Group 49
- **Team Members:**
  - Bhaumik Luhar (202301468) — Case Study, Docs, Architecture, Report Lead
  - Sheel Shah (202301420) — Backend API, Algorithms, AWS Infrastructure
  - Nakul Patel (202301261) — Frontend Interface, Benchmarks, Cost Modeling
- **Speaker:** Bhaumik Luhar
- **Speaker Note (30s):**  
  *"Good morning. Today Group 49 presents our study of how Shaadi.com uses Amazon Web Services for large-scale matchmaking and event processing, alongside our own event-driven serverless recommendation prototype built on AWS Lambda and API Gateway."*

---

## Slide 2: Shaadi.com Scale & Business Problem
- **Massive Scale:** 35M+ registered users, 4M+ people matched [S1, S7].
- **Core Computational Challenge:**
  - Mutual search-and-ranking over millions of complex profiles.
  - Hard constraint filtering (age, city, religion, education).
  - Soft behavioral ranking (activity, views, mutual interest signals).
- **Traffic Patterns:** Extreme diurnal evening peaks, seasonal surges (COVID-19 surge: +30% users, 1.8M $\rightarrow$ 2.5M daily interest requests [S5]).
- **Why Cloud?** On-premise private clouds lacked elasticity, created database bottlenecks, and limited algorithm testing [S2].
- **Speaker:** Bhaumik Luhar
- **Speaker Note (45s):**  
  *"Matchmaking is not like shopping on Amazon where goods are static. Here, both sides must be mutually compatible. Shaadi.com experiences huge traffic swings, making fixed on-prem servers either overloaded during peaks or wasted during valleys. Moving to AWS provided the elastic compute and managed data services they needed."*

---

## Slide 3: Sourced Cloud Architecture Wins
- **Database Scalability:**
  - MySQL on EC2 $\rightarrow$ **Amazon DynamoDB** for messaging: **$\ge 60\%$ cost reduction**, **43%–50% peak latency drop** (`GetMessages` p50–p95) [S3].
  - Relational workloads to **Amazon Aurora**: **55% database savings**, **40% faster migration** [S7].
- **Storage & Compute Optimization:**
  - Storage: EBS `gp2` $\rightarrow$ `gp3` cut monthly storage spend by **25%** without downtime [S5].
  - Early serverless tasks on Lambda + DynamoDB achieved **>80% cost savings** [S7].
- **Modern Photo-Review Microservices (2022):**
  - Legacy monolith decomposed into **API Gateway, Lambda, Step Functions, EventBridge, and Rekognition** [S4].
  - Automated photo moderation cut publishing time by **95%** [S2, S4].
- **Visual:** `docs/diagrams/rendered/case_study_overview.png`
- **Speaker:** Bhaumik Luhar
- **Speaker Note (60s):**  
  *"Our research uncovered concrete, verified numbers: DynamoDB cut messaging costs by at least 60% while slashing peak latency by half. Migrating databases to Aurora cut costs by 55%, and an asynchronous serverless photo-review pipeline using Lambda, EventBridge, and Step Functions reduced photo posting delays by 95%."*

---

## Slide 4: Academic Rigor: Verified Facts vs. Popular Claims
- **The Course Metric:** *"AI/ML on 67 billion event records $\rightarrow$ 4 million matches."*
- **Our Verification Findings:**
  - **Verified Fact 1:** In Amazon's 2016 Mumbai region launch announcement, Amazon verified that Shaadi.com's **Redshift data warehouse** analyzed **67 billion records** for business trends and reporting [S7].
  - **Verified Fact 2:** Shaadi.com helped **over 4 million people** find matches over its operating history [S1, S7].
  - **The Context:** In 2018, trade press [S6] merged these two distinct facts into a single "AI/ML on 67B records" headline.
- **Academic Distinction:** We treat Redshift big-data analytics and the 4 million people helped as primary verified facts, while clarifying the popular media ML framing.
- **Speaker:** Bhaumik Luhar
- **Speaker Note (45s):**  
  *"We applied strict verification to our case study. The 67 billion records were analyzed by Amazon Redshift for enterprise business intelligence, as verified in AWS's 2016 Mumbai announcement. The 4 million refers to actual people matched over years. We present these as verified primary facts while distinguishing them from secondary trade-press narratives."*

---

## Slide 5: Student Prototype: Objective & Scope
- **Objective:** Build an event-driven serverless recommendation engine demonstrating cloud principles:
  - FaaS execution with zero idle compute.
  - Managed API gateway routing, rate limiting, and CORS.
  - Elastic concurrency scaling and cold-start characterization.
  - Empirical cost per 1,000 requests.
- **Academic Disclaimer:**
  - **Not** Shaadi.com's proprietary algorithm.
  - **Not** black-box ML on unverified data.
  - Runs on **100% synthetic profiles** with an explainable, deterministic heuristic.
- **Speaker:** Sheel Shah
- **Speaker Note (30s):**  
  *"To explore these cloud principles hands-on, we built an academic serverless API that demonstrates auto-scaling, cold starts, and cost modeling on synthetic data with an explainable scoring heuristic."*

---

## Slide 6: Student Cloud Architecture
- **Client Tier:** Static responsive web interface (`frontend/`).
- **Edge Tier:** Amazon API Gateway HTTP API v2 (CORS, Throttling: 50 rps, burst 100).
- **Compute Tier:** AWS Lambda (Python 3.12, 512 MB, x86_64, Mangum ASGI adapter).
- **Application:** FastAPI app with Pydantic validation (strict 400 vs. 422 error taxonomy).
- **Data Tier:** In-memory repository pattern loading 64 synthetic candidate profiles.
- **Observability & Security:** CloudWatch JSON logging, least-privilege IAM execution role.
- **Visual:** `docs/diagrams/rendered/student_architecture.png`
- **Speaker:** Sheel Shah
- **Speaker Note (45s):**  
  *"The architecture uses API Gateway HTTP API to trigger a Python 3.12 Lambda function. Inside Lambda, Mangum adapts API Gateway events to FastAPI. The candidate repository is loaded into memory during container init, enabling sub-10 ms execution with zero idle cost."*

---

## Slide 7: Explainable Compatibility Algorithm
- **Formula:** $\text{Total Score} = S_{\text{age}} (30) + S_{\text{location}} (25) + S_{\text{education}} (15) + S_{\text{interests}} (30) \in [0, 100]$
- **Component Breakdown:**
  - **Age (30 pts):** Linear decay: $30 \times \max(0, 1 - |\Delta\text{age}| / 10)$.
  - **Location (25 pts):** Preferred city = 25 pts; User's city = 10 pts; else 0.
  - **Education (15 pts):** Exact degree = 15 pts; Same field group = 8 pts; else 0.
  - **Interests (30 pts):** Overlap coefficient: $30 \times |A \cap B| / \min(|A|, |B|)$.
- **Deterministic Ordering:** Ties broken by `candidate_id` for 100% reproducible test verification.
- **Visual:** `docs/diagrams/rendered/recommendation_flow.png`
- **Speaker:** Sheel Shah
- **Speaker Note (45s):**  
  *"Instead of an opaque black box, our scoring heuristic is completely transparent and defensible. Age, location, education, and interests combine to form a 0-to-100 score with plain-English explanation reasons returned in every response."*

---

## Slide 8: Live Demonstration
- **Demonstration Steps:**
  1. Service health check (`GET /health` indicator showing active status and candidate count).
  2. Recommendation submission for profile U001 (showing top matches, score breakdowns, and self-exclusion).
  3. Strict filtering demonstration (no-match edge case).
  4. Validation rejection (submitting invalid age $< 18$ triggering an HTTP 422 with exact field diagnostics).
- **Target URL:** AWS Deployed HTTP API endpoint (or localhost fallback if network unavailable).
- **Speaker:** Nakul Patel
- **Speaker Note (90s):**  
  *"[Conducting live demo] Here is our frontend communicating directly with the API. The health indicator is green. Submitting user U001 returns the top 5 candidates with complete component score breakdowns. Notice U001 is excluded from their own results. If we enter an age of 16, the API immediately responds with HTTP 422 Unprocessable Entity detailing the validation failure."*

---

## Slide 9: Verification & Testing Rigor
- **Automated Test Suite:** **110 pytest tests** passing with **99% code coverage**.
- **Test Categories:**
  - Pydantic models & schema boundaries (18 tests).
  - Validation rules: 400 bad request vs. 422 unprocessable entity (16 tests).
  - Scoring formulas, edge cases, and deterministic sorting (24 tests).
  - API endpoint contracts, CORS headers, error payloads (22 tests).
  - Lambda handler event format 2.0 parsing and cold-start flags (14 tests).
  - Self-exclusion and empty candidate matches (16 tests).
- **Static Validation:** `scripts/validate_project.py` checks 85 files for syntax, broken links, and credentials.
- **Visual:** `docs/diagrams/rendered/testing_workflow.png`
- **Speaker:** Nakul Patel
- **Speaker Note (45s):**  
  *"Every component is covered by our 110 automated tests. We achieved 99% line coverage across the backend, validating everything from event parsing and cold-start flags to boundary conditions and error codes."*

---

## Slide 10: Performance Benchmarks & Cold Starts
- **Local Concurrency Scaling (1 to 50 Virtual Users):**
  - 1 VU: 5.86 ms median latency, 0.99 req/s throughput.
  - 10 VUs: 6.38 ms median latency, 9.47 req/s throughput.
  - 25 VUs: 8.48 ms median latency, 23.01 req/s throughput.
  - 50 VUs: 20.31 ms median latency, 43.43 req/s throughput.
  - **Zero errors** across 2,351 benchmarked requests.
- **Cloud Execution & Cold Starts:**
  - Cold starts introduce initial container setup overhead (`Init Duration` ~200–400 ms).
  - Warm execution runs in 5–15 ms.
  - Under concurrent spikes, Lambda scales horizontally by spinning up parallel environments.
- **Visual:** `experiments/charts/local_latency_vs_vus.png`
- **Speaker:** Nakul Patel
- **Speaker Note (60s):**  
  *"Our benchmarks show that under 1 to 25 concurrent users, median latency is under 10 milliseconds. On AWS Lambda, cold starts require an initial container initialization, but subsequent warm requests execute in under 15 milliseconds while auto-scaling horizontally."*

---

## Slide 11: Cloud Cost Modeling
- **Parametric Cost Model Formulation:**
  $$\text{Cost}_{1000} = C_{\text{API}} + C_{\text{Lambda Requests}} + C_{\text{Lambda Compute}} + C_{\text{Logging}}$$
- **Cost Breakdown (at 512 MB memory, 15 ms warm execution):**
  - API Gateway HTTP API: \$0.00100 per 1,000 requests.
  - Lambda Requests: \$0.00020 per 1,000 requests.
  - Lambda Compute (0.015 s $\times$ 0.5 GB $\times$ \$0.0000166667): \$0.000125 per 1,000 requests.
  - CloudWatch Logs: $\approx \$0.000001$ per 1,000 requests.
  - **Total Cost $\approx \$0.0013$ per 1,000 requests (~0.13 cents).**
- **Economic Takeaway:** Compared to a continuous EC2 `t4g.small` (\$12.10/month), serverless provides over **99% cost reduction** for intermittent classroom traffic while scaling to zero when idle.
- **Speaker:** Nakul Patel
- **Speaker Note (45s):**  
  *"Our cost model proves the economic advantage of serverless FaaS. Running 1,000 warm recommendation queries costs approximately 0.13 cents. Compared to paying for a provisioned EC2 instance 24/7, serverless saves over 99% for bursty or low-frequency traffic."*

---

## Slide 12: Limitations, Future Work & Team Summary
- **Prototype Limitations:**
  - Synthetic dataset only; no PII.
  - Rules-based similarity baseline rather than trained neural network.
  - No user authentication (Cognito JWT required for production).
- **Future Production Roadmap:**
  - Transition in-memory store to Amazon DynamoDB with Global Secondary Indexes.
  - Event choreography with Amazon EventBridge for asynchronous interaction logging.
  - Architecture optimization using AWS Graviton (Arm64) for 20% cost efficiency.
- **Team Contributions (Group 49):**
  - Bhaumik Luhar (202301468): Case study research, source verification, architecture documentation, report lead.
  - Sheel Shah (202301420): Backend application, Pydantic validation, scoring algorithm, AWS SAM IaC.
  - Nakul Patel (202301261): Frontend interface, k6 performance tests, CloudWatch analysis, cost modeling.
- **Speaker:** All (Bhaumik Luhar, Sheel Shah, Nakul Patel)
- **Speaker Note (30s):**  
  *"To conclude, this project successfully bridges the theoretical cloud architecture of Shaadi.com with an empirical serverless prototype. We thank our instructor and welcome any questions from the panel."*
