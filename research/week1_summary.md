# Week 1 Research Summary — Shaadi.com Cloud Computing Case Study

**Course:** IT457 Cloud Computing  
**Group Number:** 49  
**Group Members:**
- Bhaumik Luhar (202301468)
- Sheel Shah (202301420)
- Nakul Patel (202301261)

---

## 1. Problem and Research Focus

We are studying how Shaadi.com uses Amazon Web Services (AWS) to support large-scale matchmaking, analytics, and growing user demand. The focus is the relationship between cloud architecture, distributed data processing, machine learning, and operating cost. This research guides our hands-on serverless recommendation exercise.

Matchmaking represents an intensive search-and-ranking problem over millions of profiles subject to strict user preferences, bursty diurnal traffic, and stringent latency demands. Operating this at scale requires examining how Shaadi.com transitioned from on-premise infrastructure to elastic cloud services and modern serverless architectures.

---

## 2. Key Findings & Sources

Primary sources identified during Week 1 include Amazon's official Mumbai Region launch announcement, the AWS News Blog, Shaadi.com's engineering blog (*Tech Shaadi*), and the AWS Database Blog [1–4] (mapped to `research/sources.md` [S1–S7]):

1. **Foundational AWS Infrastructure (2014–2016):**
   - Shaadi.com moved core operations to AWS, utilizing **Amazon EC2** for compute, **Amazon S3** for media storage, **Amazon SNS** and **Amazon SES** for messaging and notifications, **Amazon ElastiCache** for sub-millisecond caching, and **Amazon Redshift** as the central data warehouse [S1, S7].
   - Early adoption of serverless and NoSQL primitives: AWS documented early workloads leveraging **AWS Lambda** and **Amazon DynamoDB** [S1, S7].

2. **Reported Performance, Scale, and Cost Outcomes:**
   - **Data Scale:** Amazon reported in 2016 that Shaadi.com's corporate Redshift data warehouse analyzed **67 billion records** for business trends and reporting [S7].
   - **User Impact:** AWS startup profiles reported that Shaadi.com had helped **over 4 million people** find matches and touched over 35 million lives [S1]. *(Note: As clarified by our team, these citations do not establish that a single ML model produced 4 million matches directly from 67 billion records).*
   - **Migration Speed & Database Savings:** Amazon's announcement reported a **40% reduction in database migration time**, **55% cost savings** for databases migrated to Amazon Aurora, and a **50% improvement in website performance** [S7].
   - **Serverless Savings:** Amazon cited **over 80% cost savings** for specific workloads migrated to AWS Lambda and DynamoDB [S7].
   - **DynamoDB Optimization (2022):** Switching DynamoDB from on-demand capacity to provisioned capacity with auto-scaling yielded **at least 60% cost savings** on messaging tables, while `GetMessages` API latency improved **43% to 50% at peak** (p50–p95) [S3].
   - **Storage Cost Optimization (2021):** Upgrading EBS storage from `gp2` to `gp3` reduced monthly EBS spend by **25%** amidst a 37.44% traffic surge during COVID-19 lockdowns [S5].

3. **Modern Event-Driven Microservices Architecture (2022):**
   - Shaadi.com transitioned a legacy monolithic "Photo SaaS" platform into an asynchronous, event-driven microservice system [S4].
   - **Services involved:** Amazon API Gateway, AWS Lambda, Amazon S3, AWS Step Functions, Amazon EventBridge, Amazon Cognito, and Amazon Rekognition combined with custom internal computer-vision models [S4].

---

## 3. Architecture Breakdown: The Photo-Review Pipeline

The 2022 modern workload documented by *Tech Shaadi* illustrates how Shaadi.com structures event-driven serverless pipelines across Virtual Private Clouds (VPCs):

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

*This real-world pipeline demonstrates loose coupling, asynchronous event routing via EventBridge, stateful orchestration via Step Functions, and serverless compute via Lambda.*

---

## 4. Cloud Computing Concepts Identified

| Concept | Manifestation in Shaadi.com Case Study |
|---|---|
| **Elasticity & Auto Scaling** | EC2 Auto Scaling groups and EBS dynamic volume modification during traffic surges (COVID-19 +30% users) [S5]. |
| **Serverless Computing (FaaS)** | AWS Lambda for execution without provisioning servers, yielding >80% cost reduction on specific tasks [S7]. |
| **Event-Driven Choreography** | Amazon EventBridge distributing fine-grained domain events to AWS Step Functions workflows [S4]. |
| **Managed NoSQL Databases** | Amazon DynamoDB replacing self-managed MySQL on EC2 for high-throughput messaging, cutting costs by ≥60% [S3]. |
| **Cloud Data Warehousing** | Amazon Redshift analyzing 67 billion records for enterprise reporting and business analytics [S1, S7]. |
| **AI/ML as a Cloud Service** | Amazon Rekognition integrated into photo moderation pipelines alongside proprietary computer-vision models [S4]. |
| **Cost Optimization Engineering** | Shifting from DynamoDB on-demand to provisioned mode [S3] and EBS gp2 to gp3 [S5] to proactively curb cloud spend. |

---

## 5. Planned Hands-On Student Exercise

To connect these cloud concepts to practice, our team will construct and benchmark an academic serverless prototype:
- **Frontend:** Responsive client interface hosted on a static web server.
- **API Tier:** Amazon API Gateway (HTTP API v2) providing HTTPS routing, CORS, and rate limiting.
- **Compute Tier:** AWS Lambda function (Python 3.12, 512 MB) running FastAPI adapted via Mangum.
- **Matchmaking Engine:** Transparent, explainable weighted similarity heuristic evaluating age, location, education, and interests across synthetic candidate profiles (strictly rules-based, not proprietary ML).
- **Measurement Goals:** Measure cold vs. warm invocation latency, response percentiles (p50, p90, p95), error rates under concurrency (1–50 virtual users via k6), and empirical cost per 1,000 requests.

---

## 6. Primary References

- **[1]** Amazon Web Services, *"Amazon Web Services Announces New Cloud Region in India"*, Press Release, June 2016. (Source `[S7]`)
- **[2]** Jeff Barr, *"Hot Startups on AWS – June 2016 – Shaadi.com, Capillary, Mondo"*, AWS News Blog, 6 July 2016. (Source `[S1]`)
- **[3]** Nivedita Sood, *"Shaadi.com's approach to transitioning from monolith to microservices"*, Tech Shaadi Blog, 10 June 2022. (Source `[S4]`)
- **[4]** Vatsal Shah & Sanket Shah, *"How Shaadi.com reduced costs and improved performance with DynamoDB"*, AWS Database Blog, 19 May 2022. (Source `[S3]`)

---

## 7. Group 49 Member Contributions (Week 1)

| Member | Student ID | Primary Focus in Week 1 |
|---|---|---|
| **Bhaumik Luhar** | 202301468 | Led case-study literature review, compiled 2016 & 2022 AWS publications, analyzed the photo-review microservices architecture, and established verification methodology. |
| **Sheel Shah** | 202301420 | Investigated serverless compute patterns (Lambda, API Gateway), evaluated Python frameworks for serverless packaging, and scoped the recommendation service contract. |
| **Nakul Patel** | 202301261 | Researched performance measurement methodologies, k6 load testing on serverless endpoints, CloudWatch cold-start metrics, and AWS pricing models. |
