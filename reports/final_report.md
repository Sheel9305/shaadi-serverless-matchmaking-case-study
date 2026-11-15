# Serverless Matchmaking Recommendations: A Shaadi.com Cloud Computing Case Study

**Course:** IT457 Cloud Computing  
**Academic Term:** Autumn 2026  
**Group Number:** 49  

**Authors & Project Team:**
- **Bhaumik Luhar** (Student ID: 202301468) — *Case Study, Documentation, Architecture & Report Lead*
- **Sheel Shah** (Student ID: 202301420) — *Backend Engineering, Serverless API & AWS Infrastructure*
- **Nakul Patel** (Student ID: 202301261) — *Frontend Interface, Experiments, Testing & Cost Modeling*

**Repository:** `https://github.com/thenakulpatel/shaadi-cloud-case-study`  

---

## 2. Abstract

This project investigates the cloud computing architecture of **Shaadi.com**, one of the world's largest online matrimonial matchmaking platforms, analyzing its migration to Amazon Web Services (AWS) to achieve high elasticity, cost optimization, and operational efficiency. We analyze published case studies detailing Shaadi.com's utilization of cloud primitives, including Amazon Redshift for big-data warehousing (analyzing 67 billion event records), Amazon DynamoDB for scalable messaging ($\ge 60\%$ cost reduction and 43–50% peak latency drop), and modern event-driven serverless microservices for automated photo moderation (API Gateway, AWS Lambda, AWS Step Functions, Amazon EventBridge, and Amazon Rekognition).

To translate these industrial cloud concepts into an empirical classroom demonstration, we designed, deployed, and benchmarked an event-driven **serverless recommendation API**. Built with AWS Lambda (Python 3.12, 512 MB) and Amazon API Gateway HTTP API, the prototype implements an explainable, deterministic multi-factor compatibility scoring heuristic across synthetic candidate profiles. The service achieves sub-10 ms execution times in baseline conditions, scales elastically under concurrent synthetic traffic (1–50 virtual users), demonstrates strict input validation (400 vs. 422 error taxonomy), and achieves an empirical operational cost of fractions of a cent per 1,000 requests. This report details the verified architectural facts, our prototype implementation, testing methodology, performance benchmarks, and cost analysis.

---

## 3. Introduction

### 3.1 Motivation & Context
Online matchmaking services operate under uniquely demanding computing requirements. Unlike traditional e-commerce catalogs where consumers browse static inventories of physical goods, matchmaking platforms manage dynamic, bi-directional search-and-ranking operations across human profiles. Millions of members evaluate candidates based on overlapping geographic, demographic, educational, cultural, and behavioral criteria. Traffic is volatile, exhibiting pronounced diurnal evening surges, weekend spikes, and major influxes during cultural seasons and external events.

To sustain this workload without over-provisioning expensive physical data center capacity, Shaadi.com transitioned from on-premise infrastructure to AWS. Studying this real-world migration offers profound academic insights into elasticity, managed database services, serverless computing, and proactive cloud cost management.

### 3.2 Report Structure: Two Distinct Tracks
To preserve strict academic integrity, this report maintains a transparent separation between the industrial case study and our educational software prototype:
1. **Track A (Industrial Case Study):** Examines verified architectural publications, press releases, and technical blogs detailing how Shaadi.com leverages AWS services. Every metric is tagged with its verification status in our Claims Register.
2. **Track B (Student Prototype & Benchmarks):** Details an academic serverless application engineered by our team to demonstrate FaaS execution, API routing, cold-start mechanics, and pay-per-use economics. The prototype uses exclusively synthetic profiles and an explainable rules-based scoring algorithm (not machine learning, and not Shaadi.com's confidential algorithm).

---

## 4. Shaadi.com Case Study Background & Claims Register

Shaadi.com was established to modernize traditional matrimonial search. By 2016, AWS reported that the service had touched over 35 million lives and helped **over 4 million people find matches** [S1, S7]. As user registrations scaled, managing dedicated on-premise hardware clusters in private data centers severely constrained database scalability, prolonged feature deployment cycles, and limited algorithmic experimentation [S2].

### Verified Claims vs. Popular Assertions
A central component of our academic investigation was reconciling trade-press narratives with first-party engineering sources:

| Claim ID | Sourced Statement | Verification Status | Source Reference | Context & Technical Interpretation |
|---|---|---|---|---|
| **C1** | Shaadi.com analyzed **67 billion event records** on AWS | ✅ Verified (Primary for Redshift) / 🟡 ML Contextualized | S7 (Amazon Mumbai Launch), S1, S6 | S7 and S1 verify that Shaadi.com's corporate Amazon Redshift data warehouse processed 67 billion records for business intelligence and analytics. Secondary trade press (S6) subsequently popularized this as "AI/ML on 67B records". |
| **C2** | Generated **4 million matches** | ✅ Verified (Primary) | S1, S7 | Amazon official publications confirm Shaadi.com helped over 4 million *people* find matches. This reflects cumulative human pairings over years, rather than pairs output by an isolated ML job. |
| **C3** | Scale of **35 million+ registered users** | ✅ Verified (Primary) | S1, S2, S7 | Confirmed across multiple first-party AWS case studies and press releases from 2016. |
| **C4** | Core production infrastructure on AWS | ✅ Verified (Primary) | S1, S7 | Utilizes EC2, S3, SNS, SES, ElastiCache, and Redshift. |
| **C5** | Rapid migration & doubled algorithm experimentation | ✅ Verified (Primary Mirror) | S2 | Full stack migrated in ~3 months; on-demand compute doubled concurrent matching algorithm testing capacity. |
| **C6** | Messaging migrated from MySQL to Amazon DynamoDB | ✅ Verified (Primary) | S3 | Transitioned connection requests and chat to DynamoDB with provisioned capacity; cut cost $\ge 60\%$ and lowered peak latency 43–50%. |
| **C7** | Asynchronous, serverless photo-review microservices | ✅ Verified (Primary) | S4 | Deployed API Gateway, Lambda, Step Functions, EventBridge, and Rekognition to automate photo moderation. |
| **C8** | Storage cost optimization during COVID-19 | ✅ Verified (Primary) | S5 | Migrated EBS `gp2` to `gp3`, cutting monthly EBS costs by 25% amidst a 37.44% traffic surge. |
| **C10** | **40% database migration time reduction** | ✅ Verified (Primary) | S7 | Documented in Amazon's official Mumbai Region launch announcement. |
| **C11** | **55% database savings on Amazon Aurora** | ✅ Verified (Primary) | S7 | Validated cost savings moving relational workloads to managed Aurora clusters. |
| **C12** | **50% overall site performance improvement** | ✅ Verified (Primary) | S7 | Observed customer-facing latency improvements after cloud adoption. |
| **C13** | **>80% serverless workload savings** | ✅ Verified (Primary) | S7 | Realized on early tasks transitioned to AWS Lambda and DynamoDB. |

---

## 5. Problem Statement: Matchmaking at Hyperscale

Matchmaking differs fundamentally from classical one-to-many retrieval problems:
1. **Bi-Directional Compatibility:** A match is only valid if Candidate $B$ satisfies Candidate $A$'s criteria *and* Candidate $A$ satisfies Candidate $B$'s expectations.
2. **High-Dimensional Hard and Soft Filtering:** Hard criteria (age ranges, location distance, religion/community, education) prune candidate spaces, while soft criteria (interests, lifestyle, responsiveness) score the survivors.
3. **Diurnal Volatility & Traffic Bursts:** Evening traffic surges and marketing campaigns generate severe concurrency spikes. Fixed-capacity infrastructure forces operators to over-provision hardware for peak hours, paying for idle capacity during troughs.
4. **Data Privacy & Trust Assurance:** Personal preferences and identity photos require rigorous data protection, automated moderation, and strict compliance with least-privilege access principles.

---

## 6. Cloud Computing Challenges & Solutions

| Technical Challenge | Conventional Data Center Bottleneck | AWS Cloud Solution | Documented Outcome |
|---|---|---|---|
| **Traffic Elasticity** | Static server provisioning; risk of brownouts during surges | Amazon EC2 Auto Scaling, EBS elastic resizing | Seamlessly handled COVID-19 surge from 1.8M to 2.5M daily interest requests [S5] |
| **Relational Database Scalability** | Replication lag, sharding complexity, manual patching | Amazon Aurora managed relational database | 40% faster migration, 55% database cost savings [S7] |
| **High-Throughput Chat & Messaging** | Hot partitions and locking in self-managed MySQL on EC2 | Amazon DynamoDB NoSQL with auto-scaled provisioned capacity | $\ge 60\%$ cost reduction; 43–50% peak latency drop [S3] |
| **Unbounded Analytical Queries** | Heavy analytical scans degraded transactional databases | Amazon Redshift dedicated columnar data warehouse | Analyzed 67 billion records for business intelligence without impacting OLTP [S1, S7] |
| **Compute Idle Cost in Media Pipelines** | Dedicated worker servers sat idle waiting for user uploads | AWS Lambda + Step Functions event-driven serverless pipeline | >80% serverless savings [S7]; 95% faster photo publishing [S2, S4] |
| **Algorithmic Experimentation Agility** | Hardware constraints limited A/B testing of match models | On-demand EC2 / FaaS compute capacity | Doubled concurrent matching algorithm evaluations [S2] |

---

## 7. Real-World Architectural Deep Dive

### 7.1 Modern Event-Driven Photo-Review Architecture (2022)
In 2022, Shaadi.com decomposed its monolithic "Photo SaaS" engine into a serverless, event-driven microservices architecture [S4]:

```
[ User (Web / App) ]
         │
         ▼
[ VPC A: Kong API Gateway / min.shaadi.com / my.shaadi.com ]
         │
         ▼ (HTTPS Image Upload Request)
[ AWS API Gateway + AWS Cognito ]
         │
         ▼
[ VPC B: Image Upload Handler (Lambda) ] ──► [ S3 photo_store/uploads ]
         │                                              │
         ├──► [ WebP Converter (Lambda) ] ──────────────┘
         │
         ▼
   [ Event Router (Lambda) ] ──► [ AWS Parameter Store ]
         │
         ▼
   [ Amazon EventBridge ]
         │
         ├──► [ Verification Workflow (Step Functions) ] ──► [ S3 celebrity collection ]
         │                                               ──► [ S3 photo_store/resize ]
         │
         ├──► [ Crop Workflow (Step Functions) ]         ──► [ S3 photo_store/crop ]
         │
         └──► [ Status Tracker Workflow (Step Functions) ]
                     │
                     ├──► Webhook push updates
                     └──► [ Amazon Redshift (status logs) ]
```

### 7.2 Architectural Analysis: Decoupling and Stateful Choreography
- **Loose Coupling via EventBridge:** The `Event Router` Lambda emits standard events to Amazon EventBridge, entirely isolating the upload receiver from downstream consumers. New processing steps (e.g., automated watermarking) can be added without altering existing Lambdas.
- **Stateful Resilience via Step Functions:** Complex multi-step operations (facial feature extraction, celebrity likeness verification against Amazon Rekognition, cropping, format transcoding) are coordinated via Step Functions state machines. Retries, error handling, and parallel branch joins are managed natively without brittle custom code.
- **Cost-Optimized Storage Hierarchy:** Raw media enters staging buckets before WebP conversion and tiered archival to S3, cutting bandwidth and storage overhead.

---

## 8. Proposed Student Prototype Architecture

To demonstrate the cloud computing principles identified in Shaadi.com's architecture—specifically serverless FaaS, managed API routing, elastic concurrency, and pay-per-use economics—we architected an academic serverless recommendation engine:

```
[ Browser Client (HTML5 / Vanilla JS) ]
                 │
                 ▼ HTTPS POST /recommendations
[ Amazon API Gateway HTTP API v2 ]
  - TLS Termination, Routing, Throttling (50 rps / burst 100), CORS
                 │
                 ▼ Event Payload v2.0
[ AWS Lambda Execution Environment (Python 3.12, 512 MB, x86_64) ]
  ├── Mangum ASGI Adapter
  ├── FastAPI Web Framework (Routing & Lifespan)
  ├── Pydantic Input Validation (Strict 400 vs. 422 mapping)
  ├── RecommendationService (Filter → Score → Explain → Sort)
  └── ProfileRepository (Synthetic Candidate Store in Memory)
                 │
                 ▼ Structured JSON Logs
[ Amazon CloudWatch Logs Insights ]
```

### Key Architectural Decisions:
1. **API Gateway HTTP API vs. REST API:** HTTP API was selected for its lower latency, reduced cost (~$1.00/million requests vs. $3.50 for REST), and native CORS handling.
2. **FastAPI + Mangum on AWS Lambda:** Allows identical code execution locally via Uvicorn for rapid testing and in AWS Lambda via Mangum without modification.
3. **In-Memory Repository Pattern:** Candidate data (64 synthetic profiles) is loaded during Lambda execution environment initialization, eliminating cold database queries while demonstrating an abstract repository interface suitable for future DynamoDB backing.
4. **Least-Privilege Security:** The Lambda execution role contains exclusively `AWSLambdaBasicExecutionRole` permissions (write access to CloudWatch Logs). No cloud storage, database, or external network write privileges are granted.

---

## 9. Student Implementation Details

### 9.1 API Specification & Endpoints
The service exposes two primary endpoints:
- `GET /health`: Returns service operational status (`healthy`), candidate pool count, API version, and runtime environment.
- `POST /recommendations`: Accepts a user profile payload and returns the top $N$ ranked candidates with full score breakdowns and plain-English reasons.

### 9.2 Explainable Compatibility Scoring Heuristic
Rather than implementing an opaque, unverified black-box neural network, our prototype implements a transparent, multi-factor compatibility scoring algorithm:

$$\text{Total Score} = S_{\text{age}} + S_{\text{location}} + S_{\text{education}} + S_{\text{interests}}$$

$$\text{Where Total Score} \in [0, 100]$$

| Factor | Weight | Formulation & Scoring Rules | Rationale |
|---|---|---|---|
| **Age Compatibility** | 30% | $30 \times \max\left(0, 1 - \frac{|\Delta\text{age}|}{10}\right)$ | Linear decay over a 10-year age divergence window. |
| **Location Proximity** | 25% | Candidate in preferred city: 25 pts.<br>Candidate in user's city (when another preferred): 10 pts.<br>Otherwise: 0 pts. | Balances explicit relocation preferences against local proximity. |
| **Educational Alignment** | 15% | Exact education match: 15 pts.<br>Same academic group (STEM, Business, Humanities): 8 pts.<br>Otherwise: 0 pts. | Rewards academic compatibility with partial credit for related fields. |
| **Interests Overlap** | 30% | $30 \times \frac{|A \cap B|}{\min(|A|, |B|)}$ (Overlap Coefficient) | Normalizes shared hobbies across profiles with asymmetric list lengths. |

*Deterministic Tie-Breaking:* In the event of identical scores, candidates are ordered deterministically by `candidate_id`, ensuring 100% reproducible test verification.

### 9.3 Strict Validation & Error Handling Taxonomy
The API rigorously separates syntactic vs. semantic client errors:
- **HTTP 400 Bad Request:** Malformed JSON syntax, empty request bodies, or non-object payloads.
- **HTTP 422 Unprocessable Entity:** Syntactically valid JSON failing Pydantic schema constraints (e.g., age $< 18$ or $> 120$, invalid field types, unexpected fields with `extra="forbid"`).

---

## 10. Testing Methodology & Verification

Our testing regime spans unit, integration, edge-case, and static validation tiers:

| Test Suite | File | Tests Count | Coverage Focus |
|---|---|---|---|
| **Data Models** | `backend/tests/test_models.py` | 18 | Pydantic validation, boundary values, default parameters |
| **Validation Rules** | `backend/tests/test_validation.py` | 16 | 400 vs. 422 discrimination, extra field rejection |
| **Scoring Engine** | `backend/tests/test_recommendation.py` | 24 | Individual component formulas, tie-breaking, empty overlap |
| **API Endpoints** | `backend/tests/test_api.py` | 22 | `/health`, `/recommendations`, CORS headers, response structures |
| **Edge Cases** | `backend/tests/test_edge_cases.py` | 16 | Self-exclusion (User U001), zero-candidate matches, boundary limits |
| **Lambda Handler** | `backend/tests/test_handler.py` | 14 | API Gateway v2 event parsing, cold-start flags, exception handling |
| **Total** | — | **110 Passed** | **99% Line Coverage across backend codebase** |

Static validation is enforced by `scripts/validate_project.py`, verifying file presence, JSON/YAML parsing, SAM template linting, Markdown relative link validity, and automated secret scanning across 85 files.

---

## 11. Experimental Results & Performance Analysis

### 11.1 Local Concurrency Benchmarks
Local load testing was executed across four standard concurrency tiers (1, 10, 25, 50 Virtual Users) with 1-second think times:

| Concurrency (VUs) | Total Requests | Throughput (req/s) | Min (ms) | Median (ms) | p90 (ms) | p95 (ms) | Max (ms) | Error Rate |
|---|---|---|---|---|---|---|---|---|
| **1 VU** | 30 | 0.99 | 4.88 | 5.86 | 6.54 | 6.70 | 8.84 | **0.0%** |
| **10 VUs** | 290 | 9.47 | 4.67 | 6.38 | 7.92 | 8.78 | 13.91 | **0.0%** |
| **25 VUs** | 703 | 23.01 | 5.09 | 8.48 | 15.19 | 18.25 | 32.74 | **0.0%** |
| **50 VUs** | 1,328 | 43.43 | 5.34 | 20.31 | 32.14 | 37.24 | 65.17 | **0.0%** |

*Analysis:* Under a single process local worker, throughput scaled linearly from 0.99 to 43.43 req/s. Median latency remained stable under 10 ms up to 25 VUs, rising to 20.31 ms at 50 VUs due to single-threaded CPU contention. Zero errors were recorded across all 2,351 local requests.

### 11.2 AWS Cloud Performance & Cold-Start Mechanics
On AWS Lambda, the execution profile differs significantly from local execution due to infrastructure container lifecycle:
- **Cold Starts:** When a request arrives with no warm execution environment available, Lambda downloads the deployment package, starts the Python 3.12 runtime, and executes module-level imports (`FastAPI`, `Mangum`, `sample_profiles.json`). This produces an `Init Duration` (typically 200–400 ms).
- **Warm Invocations:** Subsequent invocations reuse the initialized container, executing in 5–15 ms.
- **Horizontal Elasticity:** Under concurrent load (e.g. 50 VUs), AWS Lambda provisions multiple parallel execution environments automatically, avoiding the queuing delays observed on single-worker local servers.

---

## 12. Cloud Cost Modeling & Economic Analysis

### 12.1 Parametric Cost Formulation
Cloud costs for the serverless recommendation API are modeled parametrically:

$$\text{Cost}_{1000} = C_{\text{API}} + C_{\text{Lambda Requests}} + C_{\text{Lambda Compute}} + C_{\text{Logging}}$$

Where:
- $C_{\text{API}} = 1,000 \times \frac{\$1.00}{1,000,000} = \$0.0010$ (API Gateway HTTP API)
- $C_{\text{Lambda Requests}} = 1,000 \times \frac{\$0.20}{1,000,000} = \$0.0002$
- $C_{\text{Lambda Compute}} = 1,000 \times \left(\text{Billed Duration in Seconds}\right) \times \left(\frac{512\text{ MB}}{1024}\right) \times \$0.0000166667\text{ per GB-s}$
- $C_{\text{Logging}} = 1,000 \times 1.5\text{ KB} \times \frac{\$0.50}{1,000,000\text{ KB}} \approx \$0.00000075$

### 12.2 Empirical Cost per 1,000 Requests
Using measured median execution durations:
- At an average warm execution duration of **15 ms** (0.015 s) with 512 MB memory:
  - Lambda Compute $= 1,000 \times 0.015 \times 0.5 \times \$0.0000166667 = \$0.000125$
  - **Total Cost per 1,000 Requests $\approx \$0.001325$ (approx. 0.13 cents per thousand requests).**
- Even with 100% cold starts at an average duration of **350 ms**:
  - Lambda Compute $= 1,000 \times 0.350 \times 0.5 \times \$0.0000166667 = \$0.002917$
  - **Total Cost per 1,000 Requests $\approx \$0.004117$ (approx. 0.41 cents per thousand requests).**

### 12.3 Comparison with Fixed EC2 Provisioning
A dedicated `t4g.small` instance in AWS Mumbai costs $\approx \$0.0168/\text{hour}$ or $\approx \$12.10/\text{month}$. At modest or bursty classroom request rates (e.g., 50,000 requests/month), the serverless implementation costs less than **\$0.10/month**, delivering over **99% cost savings** while eliminating server patching and maintenance overhead.

---

## 13. System Limitations & Boundaries

1. **Synthetic Data Only:** Profiles are syntactically and semantically designed for testing. No real user data or PII is used.
2. **Algorithmic Simplicity:** The similarity score is a transparent, rules-based heuristic designed for educational defensibility, not an industrial AI model.
3. **No Authentication:** API endpoints are unauthenticated to facilitate classroom demonstration. Commercial production requires Amazon Cognito JWT authorizers.
4. **Single-Region Scope:** Deployed in a single AWS region (`ap-south-1` Mumbai or `us-east-1`), without multi-region active-active replication.

---

## 14. Future Architectural Improvements

1. **Amazon DynamoDB Backend:** Transitioning from the in-memory JSON file to an Amazon DynamoDB table backed by Global Secondary Indexes (GSIs) for partitioned candidate filtering.
2. **Event Choreography with Amazon EventBridge:** Emitting asynchronous domain events (e.g., `RecommendationViewed`, `CandidateContacted`) onto an EventBridge event bus to mirror Shaadi.com's microservice decoupling.
3. **Authentication via Amazon Cognito:** Enforcing user pool JWT token verification on API Gateway routes.
4. **Architecture Architecture Optimization:** Migrating Lambda execution from x86_64 to Arm64 (AWS Graviton2/3), offering up to 20% lower cost and improved price-performance.

---

## 15. Conclusion

This case study demonstrates the compelling advantages of cloud computing and serverless architectures for modern matchmaking platforms. Shaadi.com's industrial journey illustrates how elastic cloud compute, managed database services (Amazon Aurora and DynamoDB), and event-driven serverless microservices (AWS Lambda, Step Functions, EventBridge) resolve computational bottlenecks, enhance operational velocity, and dramatically reduce infrastructure expenses.

Our student prototype successfully validated these principles at classroom scale: deploying a serverless recommendation API that auto-scales on demand, enforces rigorous input validation, executes in single-digit milliseconds, and incurs zero idle cost. The project bridges theoretical cloud concepts with verified empirical engineering.

---

## 16. References

- **[1]** Amazon Web Services, *"Amazon Web Services Announces New Cloud Region in India (Mumbai Region Launch)"*, Official Press Announcement, June 28, 2016.
- **[2]** J. Barr, *"Hot Startups on AWS – June 2016 – Shaadi.com, Capillary, Mondo"*, AWS News Blog, July 6, 2016. [Online]. Available: `https://aws.amazon.com/blogs/aws/hot-startups-on-aws-june-2016-shaadi-com-capillary-mondo`
- **[3]** *"Matchmaking site Shaadi.com doubles algorithm testing using AWS"*, AWS Customer Case Study, Mirrored on CaseStudies.com, circa 2016. [Online]. Available: `https://www.casestudies.com/company/amazonwebservices/case-study/matchmaking-site-shaadicom-doubles-algorithm-testing-using-aws`
- **[4]** V. Shah and S. Shah, *"How Shaadi.com reduced costs and improved performance with DynamoDB"*, AWS Database Blog, May 19, 2022. [Online]. Available: `https://aws.amazon.com/blogs/database/how-shaadi-com-reduced-costs-and-improved-performance-with-dynamodb`
- **[5]** N. Sood, *"Shaadi.com's approach to transitioning from monolith to microservices"*, Tech Shaadi Engineering Blog, June 10, 2022. [Online]. Available: `https://tech.shaadi.com/2022/06/10/shaadi-coms-approach-to-transitioning-from-monolith-to-microservices/`
- **[6]** *"How Shaadi.com optimized compute costs using Amazon EBS gp3 volumes"*, Tech Shaadi & AWS Storage Blog, August 6, 2021. [Online]. Available: `https://tech.shaadi.com/2021/08/06/2359/`
- **[7]** CXOToday News Desk, *"AWS and cloud growth to accelerate"*, CXOToday, May 30, 2018. [Online]. Available: `https://cxotoday.com/cloud/aws-and-cloud-growth-to-accelerate/`

---

## 17. Team Contributions & AI Statement

### Team Contribution Summary

| Member | Student ID | Primary Responsibilities | Deliverables |
|---|---|---|---|
| **Bhaumik Luhar** | 202301468 | Case study research, source verification, architecture documentation, report authoring & presentation lead | `research/`, `docs/01–05, 09, 10`, `reports/`, `presentation/` |
| **Sheel Shah** | 202301420 | Backend application, models, validation, scoring algorithms, AWS SAM IaC, and deployment | `backend/`, `infrastructure/`, `pytest.ini` |
| **Nakul Patel** | 202301261 | Frontend user interface, k6 performance experiments, CloudWatch queries, and cost model | `frontend/`, `experiments/`, `docs/06–08`, `test_reports/` |

### Academic Integrity & AI-Assistance Disclosure
*The initial repository scaffold (code skeleton, tests, build scripts, and documentation drafts) was generated with an AI coding assistant. Each team member reviewed, executed, verified, modified, and assumed full intellectual responsibility for their committed files. The case-study literature verification, cloud architecture analysis, empirical benchmark execution, report authoring, and presentation defense were conducted independently by the team in compliance with course academic policy.*
