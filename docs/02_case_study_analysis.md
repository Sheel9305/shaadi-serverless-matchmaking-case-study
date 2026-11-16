# 2. Shaadi.com case-study analysis

## 2.1 Background

Shaadi.com is one of the world's largest online matchmaking platforms, serving over 35 million members across the globe ✅ [S1, S2, S7]. Founded to modernize traditional matrimonial search, the platform pairs millions of users based on complex criteria including cultural background, education, location, profession, personal interests, and interactive behavioral signals. 

In June 2016, Amazon Web Services highlighted Shaadi.com as a premier enterprise startup running in the AWS Asia Pacific (Mumbai) Region, reporting that the platform had helped **over 4 million people find matches** ✅ [S1, S7].

---

## 2.2 Business Problem & Operational Scale

Matchmaking is fundamentally an **algorithmic search-and-ranking problem over people**. Unlike traditional retail e-commerce where items have static inventories, matchmaking requires **mutual compatibility** across dynamic, sensitive user preferences:

1. **Strict Preference Filtering:** For every user search or daily recommendation batch, the system must prune millions of candidate profiles against hard boundaries (age tolerances, geographic proximity, religious/community preferences, education level).
2. **Behavioral Ranking at Scale:** Surviving candidates must be ranked using high-dimensional compatibility scores incorporating implicit activity signals (profile views, photo clicks, invitations sent, invitation acceptances, chat responsiveness).
3. **Bursty and Unpredictable Demand:** Traffic experiences severe peaks during evening hours, weekends, festival seasons, and external events (such as the COVID-19 lockdowns, which caused a 30% surge in new user registrations and pushed daily interest requests from 1.8M to 2.5M ✅ [S5]).
4. **Trust, Safety, and Privacy:** Matrimonial platforms are high-trust environments. Every uploaded profile photo must be verified for authenticity, resolution, and community guidelines, while personal identifying information must remain strictly secured.

Before migrating to AWS, Shaadi.com operated on self-managed infrastructure and private cloud environments. This fixed-capacity footprint constrained algorithmic testing, caused database scaling bottlenecks, and imposed heavy administrative burdens 🟡 [S2].

---

## 2.3 Why Cloud Computing?

The transition to AWS provided elastic capacity, managed databases, and event-driven serverless architectures to resolve these business bottlenecks:

| Challenge / Need | AWS Cloud Solution | Empirical Outcome & Evidence |
|---|---|---|
| **Traffic surges & volume spikes** (COVID-19 surge: 1.8M $\rightarrow$ 2.5M daily interest requests) | Elastic compute (EC2 Auto Scaling) and dynamically resizable EBS volumes | Zero downtime; seamless scaling during 30%+ traffic surge ✅ [S5] |
| **Rising infrastructure expenses** (+37.44% spend during traffic spikes) | Next-generation storage optimization (Amazon EBS `gp2` $\rightarrow$ `gp3`) | **25% reduction in monthly storage costs** without downtime ✅ [S5] |
| **Relational database migration bottlenecks** | Managed database services (Amazon Aurora) | **40% reduction in database migration time** and **55% database cost savings** ✅ [S7] |
| **Messaging database bottlenecks & hot partitions** (MySQL on EC2) | Amazon DynamoDB with provisioned capacity & auto-scaling | **$\ge 60\%$ cost reduction**; **43%–50% latency drop** on `GetMessages` API at peak (p50–p95) ✅ [S3] |
| **Early serverless workloads** (on-demand scaling) | AWS Lambda & Amazon DynamoDB | **Over 80% cost savings** on migrated serverless tasks ✅ [S7] |
| **Slow, manual photo moderation & verification** | Serverless event-driven pipeline (API Gateway, Lambda, Step Functions, EventBridge, Rekognition) | Fully automated, asynchronous moderation; **95% reduction in photo posting time** ✅ [S4], 🟡 [S2] |
| **Algorithmic experimentation limitations** | On-demand cloud compute environments | **Doubled the number of matchmaking algorithms** tested concurrently ✅ [S2] |
| **Enterprise-scale analytics & BI** | Amazon Redshift cloud data warehouse | **Analyzed 67 billion records** for business trends and operational reporting ✅ [S1, S7] |
| **Overall consumer site responsiveness** | AWS Cloud infrastructure and local low-latency regions (Mumbai) | **50% overall site performance improvement** ✅ [S7] |

---

## 2.4 The AI/ML and 67 Billion Event Records Claim

Course materials highlight the figure: *"Shaadi.com used AWS AI/ML to analyse 67 billion event records and make 4 million matches."* 

Our verification process resolved the origin and technical meaning of this claim:
- **Verified Primary Source:** In Amazon's June 2016 Mumbai region launch announcement [S7] and AWS News Blog [S1], Amazon stated that Shaadi.com’s corporate **Amazon Redshift** data warehouse analyzed **67 billion records** for business trends and analytics. In the same context, AWS reported that Shaadi.com had helped **over 4 million people** find their life partners.
- **Secondary Trade Press Framing:** In May 2018, CXOToday [S6], reporting on comments by AWS leadership in India, merged these points into the phrasing that Shaadi.com used AI/ML on 67 billion event records to generate 4 million matches.
- **Academic Distinction:** We report this honestly. Amazon Redshift acted as the massive data warehouse analyzing 67 billion records for enterprise business intelligence, and Shaadi.com touched 35M+ lives helping 4M+ people find matches. The 4 million figure refers to **individual people** who found matches on the platform over years of operation, rather than pairs generated by an isolated machine-learning job.

---

## 2.5 Cloud Computing Concepts Illustrated

1. **Elasticity & On-Demand Compute:** Dynamic scaling of resources during diurnal and seasonal spikes without over-provisioning idle hardware [S5].
2. **Managed NoSQL & Capacity Engineering:** Moving away from self-managed relational database clusters on EC2 to Amazon DynamoDB with provisioned capacity auto-scaling to control cost and avoid hot partitions [S3].
3. **Serverless & Event-Driven Choreography:** Decoupling user uploads from backend processing using API Gateway, Lambda, EventBridge buses, and Step Functions state machines [S4].
4. **Cloud-Native Data Warehousing:** Centralizing billions of analytical event records in Amazon Redshift for high-speed OLAP queries [S1, S7].
5. **Managed Computer Vision & AI/ML:** Utilizing Amazon Rekognition alongside custom vision models for automated facial verification and moderation [S4].
6. **Continuous Cost Optimization:** Treating cost as a first-class architectural metric through EBS gp3 volume tuning and database right-sizing [S3, S5].

---

## 2.6 Lessons That Shaped Our Student Prototype

| Case-Study Lesson | Student Prototype Implementation |
|---|---|
| Matchmaking is compute-intensive and bursty | Serverless AWS Lambda function behind API Gateway HTTP API, scaling to zero with zero idle cost |
| Managed services reduce operational maintenance | Fully serverless stack: no servers to provision, patch, or configure |
| Cloud costs must be empirically validated | Formal cost model (`cost_model.py`) calculating cost per 1,000 requests from measured execution duration |
| Matchmaking ranking must be transparent and defensible | Explainable weighted compatibility scoring heuristic (Age, Location, Education, Interests) with deterministic tie-breaking |
| Matrimonial data requires strict governance | Exclusively synthetic candidate profiles; zero personal data; least-privilege IAM execution role |

---

## 2.7 Limitations of This Analysis

Public case studies and engineering blogs disclose specific, point-in-time architecture snapshots (2016–2022). Shaadi.com's proprietary matchmaking neural networks, live production database volumes, and internal network topologies remain confidential and are not reflected in public sources.
