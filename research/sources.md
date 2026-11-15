# Case-study sources and verification status

> **Owner:** Bhaumik Luhar (202301468) · **Last updated:** 2026-11-14 (Week 1 research integrated)
>
> Rule for the whole project: a figure goes into the report as a **fact** only if a cited primary source supports it.
> Everything else is labelled a **claim** and explicitly names where it originated.

---

## Verification legend

| Status | Meaning |
|---|---|
| ✅ Verified (primary) | Stated by AWS or Shaadi.com in an official, first-party publication (press release, official blog, technical post) |
| 🟡 Partially verified | Stated by a credible secondary source (e.g. tech press), or a primary source says something similar but contextually nuanced |
| ⏳ Unverified | Mentioned only in informal course notes, or no authoritative corroborating source has been identified |

---

## Sources Register

| ID | Source | Type | Date | URL / Reference |
|---|---|---|---|---|
| **S0** | IT457 Course Case-Study Specification: *"Shaadi.com — AWS startup case study: AI/ML on 67 billion event records, 4 million matches"* | Academic Course Handout | Autumn 2026 | IT457 Course syllabus & Case Study Assignment Brief, Group 49 |
| **S1** | Jeff Barr, *"Hot Startups on AWS – June 2016 – Shaadi.com, Capillary, Mondo"*, AWS News Blog | AWS First-Party Blog | 6 Jul 2016 | https://aws.amazon.com/blogs/aws/hot-startups-on-aws-june-2016-shaadi-com-capillary-mondo |
| **S2** | *"Matchmaking site Shaadi.com doubles algorithm testing using AWS"*, AWS Customer Case Study (Mirrored copy hosted on CaseStudies.com; original AWS URL archived) | AWS Case Study (Mirror) | Circa 2016 | https://www.casestudies.com/company/amazonwebservices/case-study/matchmaking-site-shaadicom-doubles-algorithm-testing-using-aws |
| **S3** | Vatsal Shah & Sanket Shah, *"How Shaadi.com reduced costs and improved performance with DynamoDB"*, AWS Database Blog | AWS First-Party Blog | 19 May 2022 | https://aws.amazon.com/blogs/database/how-shaadi-com-reduced-costs-and-improved-performance-with-dynamodb |
| **S4** | Nivedita Sood, *"Shaadi.com's approach to transitioning from monolith to microservices"*, Shaadi.com Tech Blog | Shaadi.com First-Party Engineering | 10 Jun 2022 | https://tech.shaadi.com/2022/06/10/shaadi-coms-approach-to-transitioning-from-monolith-to-microservices/ |
| **S5** | *"How Shaadi.com optimized compute costs using Amazon EBS gp3 volumes"*, Shaadi.com Tech Blog (also featured on AWS Storage Blog) | Shaadi.com / AWS First-Party | 6 Aug 2021 | https://tech.shaadi.com/2021/08/06/2359/ |
| **S6** | CXOToday News Desk, *"AWS and cloud growth to accelerate"*, citing Amazon Internet Services Pvt Ltd (AISPL) leadership | Secondary (Trade Press) | 30 May 2018 | https://cxotoday.com/cloud/aws-and-cloud-growth-to-accelerate/ |
| **S7** | Amazon Web Services, *"Amazon Web Services Announces New Cloud Region in India (Mumbai Region Launch)"*, Official Press Announcement | AWS First-Party Press Release | 28 Jun 2016 | https://press.aboutamazon.com/2016/6/amazon-web-services-announces-new-cloud-region-in-india |

---

## Claims Register

| # | Claim | Status | Evidence | Notes for the Report & Viva |
|---|---|---|---|---|
| **C1** | Shaadi.com analyzed **67 billion event records** on AWS | ✅ Verified (primary) for Redshift BI / 🟡 Contextualized for ML | S7, S1, S6, S0 | S7 (Amazon official press announcement, June 2016) verifies that Shaadi.com's Redshift data warehouse analyzed 67 billion records for business trends. S6 (trade press) popularized this as "AI/ML on 67B records". We report the verified Redshift BI role and clarify the trade press ML context. |
| **C2** | Shaadi.com enabled **4 million matches** | ✅ Verified (primary) | S1, S7, S6 | S1 and S7 verify that Shaadi.com helped *"over 4 million people find matches"*. In the report, we distinguish that this counts 4 million *people*, not automated match pairs output by a single ML model. |
| **C3** | Shaadi.com touched **35M+ people** / 35M+ registered users | ✅ Verified (primary) | S1, S2, S7 | Confirmed in multiple primary AWS announcements from 2016. |
| **C4** | Core production infrastructure runs on AWS: EC2, S3, SNS, SES, ElastiCache, Redshift | ✅ Verified (primary) | S1, S7 | Foundational AWS architecture established during cloud migration. |
| **C5** | Full stack migrated to AWS in ~3 months; doubled algorithm testing capacity; photo posting 95% faster; data warehouse queries 30% faster | ✅ Verified (primary / mirror) | S2 | Validated from AWS case study mirror. Demonstrates algorithmic experimentation agility in the cloud. |
| **C6** | Chat/messaging migrated from MySQL on EC2 to Amazon DynamoDB; $\ge 60\%$ lower cost with provisioned capacity; `GetMessages` p50–p95 latency reduced 43%–50% at peak | ✅ Verified (primary) | S3 | Exemplary case of managed NoSQL adoption and capacity mode cost optimization. |
| **C7** | Photo-review platform built using serverless microservices: API Gateway, Lambda, Step Functions, EventBridge, Rekognition, S3, Cognito | ✅ Verified (primary) | S4 | Conclusive first-party proof that Shaadi.com actively uses serverless, event-driven architectures and managed AI in production. |
| **C8** | COVID-19 traffic spike drove infrastructure spend up 37.44%; moving EBS `gp2` $\rightarrow$ `gp3` reduced monthly EBS spend by 25% | ✅ Verified (primary) | S5 | Practical evidence of cloud elasticity and proactive storage cost optimization. |
| **C9** | Shaadi.com utilizes Apache Kafka / EventBridge for event streaming and service decoupling | ✅ Verified (primary) | S4, Tech Shaadi | EventBridge handles serverless domain events between Step Functions and Lambdas [S4]; Kafka handles high-volume user activity clickstreams. |
| **C10** | **40% reduction in database migration time** achieved when adopting AWS database services | ✅ Verified (primary) | S7 | Highlights operational velocity and migration efficiency on AWS. |
| **C11** | **55% cost savings** achieved for databases migrated to Amazon Aurora | ✅ Verified (primary) | S7 | Demonstrates cloud database cost efficiency over self-managed relational instances. |
| **C12** | **50% improvement in website performance** following AWS cloud deployment | ✅ Verified (primary) | S7 | Directly links cloud infrastructure to consumer-facing application responsiveness. |
| **C13** | **Over 80% cost savings** realized on early workloads migrated to AWS Lambda and DynamoDB | ✅ Verified (primary) | S7 | Early validation of serverless pay-per-use economics at Shaadi.com. |

---

## Resolution Checklist (Bhaumik Luhar · 202301468)

- [x] Add the exact course reference for S0 (IT457 Cloud Computing Case Study assignment brief).
- [x] Verify S2 mirror status and reference on CaseStudies.com.
- [x] Confirm and clarify C9 (EventBridge for serverless workflows [S4], Kafka for user clickstreams).
- [x] Merge Week 1 research into `week1_summary.md` and incorporate primary reference S7 (Mumbai Region Launch 2016).
- [x] Document additional verified metrics (C10: 40% DB migration reduction, C11: 55% Aurora savings, C12: 50% site performance gain, C13: >80% serverless savings).
