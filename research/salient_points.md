# Salient points: Shaadi.com case study → our prototype

---

| # | Real-world point (sourced) | Cloud concept | How our prototype reflects it (simplified) |
|---|---|---|---|
| **1** | Matchmaking is an algorithm-driven, compute-intensive workload; moving to AWS doubled the number of matchmaking algorithms tested at once [S2] | Elastic compute & rapid algorithmic experimentation | Scoring weights are explicit constants that are modular, transparent, and easy to adjust/test (`recommendation_service.py`) |
| **2** | Tens of millions of users and bursty, unpredictable traffic (e.g. COVID-19 +30% user surge, 2.5M daily interest requests) [S1, S5] | Scalability, elasticity, and traffic management | AWS Lambda scales out per incoming request; API Gateway HTTP API rate limiting (50 rps / burst 100) shields the backend |
| **3** | Transitioned monolithic systems to serverless, event-driven microservices for photo moderation and verification [S4] | Serverless compute (FaaS) and event choreography | Browser $\rightarrow$ API Gateway HTTP API triggers an on-demand Python 3.12 Lambda invocation, eliminating idle compute |
| **4** | Migrated high-throughput messaging from MySQL on EC2 to DynamoDB with provisioned capacity, cutting cost $\ge 60\%$ and peak latency 43–50% [S3] | Managed NoSQL databases, capacity tuning, and cost reduction | Abstract `ProfileRepository` interface decouples candidate retrieval, making DynamoDB a seamless drop-in backend |
| **5** | Amazon Redshift data warehouse analyzed **67 billion records** for business trends and analytics [S1, S7]; early serverless workloads achieved >80% cost savings [S7] | Big-data analytics, data warehousing, and serverless economics | Structured JSON application logs stream to Amazon CloudWatch, queryable via CloudWatch Logs Insights; cost model measures savings |
| **6** | Relational database optimizations achieved **40% migration speedup** and **55% savings on Aurora** [S7]; EBS `gp2` $\rightarrow$ `gp3` migration cut storage cost 25% [S5] | Proactive cost engineering and managed services optimization | Mathematical cost model (`cost_model.py`) calculates exact cost per 1,000 requests using empirical billed execution durations |
| **7** | Privacy and security of matrimonial candidate data is critical [S4] | Security, data governance, and least-privilege IAM | Strictly synthetic dataset (64 fictional profiles); zero PII; least-privilege IAM execution role (`AWSLambdaBasicExecutionRole` only); zero hard-coded secrets |

---

## What we deliberately do **not** claim

- We do not possess or replicate Shaadi.com's internal, proprietary production architecture beyond what is published in cited sources.
- Our rules-based compatibility scoring is **not** Shaadi.com's proprietary algorithm and is **not** machine learning; it is an explainable heuristic baseline designed for academic evaluation.
- Our latency, cold-start, and cost measurements represent our student prototype on AWS Lambda/API Gateway, not Shaadi.com's commercial platform.
