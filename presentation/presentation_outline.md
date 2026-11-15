# Presentation outline (12 slides, about 10 minutes + Q&A)

> **Owner:** Bhaumik Luhar (202301468) · **Group:** 49 (Bhaumik Luhar [202301468], Sheel Shah [202301420], Nakul Patel [202301261]) · Each member presents their own part

| # | Slide | Speaker | Content | Visual |
|---|---|---|---|---|
| 1 | Title | Bhaumik Luhar | "Serverless Matchmaking Recommendations: A Shaadi.com Cloud Case Study", IT457, Group 49 | — |
| 2 | Shaadi.com in one slide | Bhaumik Luhar | Scale (35M+ people, 4M+ matched [S1, S7]); mutual search-and-ranking problem; why cloud is required | Key facts with verification icons |
| 3 | What AWS did for Shaadi.com | Bhaumik Luhar | DynamoDB (≥60% cheaper) [S3], serverless photo review [S4], Redshift 67B records [S1, S7], Aurora 55% savings [S7], gp3 storage cuts [S5] | [case_study_overview.png](../docs/diagrams/rendered/case_study_overview.png) |
| 4 | Verified facts vs. popular claims | Bhaumik Luhar | 67B records on Redshift BI (Mumbai 2016 release [S7]) vs. trade press "AI/ML on 67B records" [S6]; 4M people matched | Claims comparison table |
| 5 | Our prototype: goal and disclaimer | Sheel Shah | Synthetic data, rules-based, inspired by (not copying) the case | — |
| 6 | Architecture | Sheel Shah | Browser → HTTP API → Lambda → FastAPI → scoring; IAM; CloudWatch | [student_architecture.png](../docs/diagrams/rendered/student_architecture.png) |
| 7 | How a recommendation is scored | Sheel Shah | Filters + weights 30/25/15/30 + reasons | [recommendation_flow.png](../docs/diagrams/rendered/recommendation_flow.png) |
| 8 | **Live demo** | Nakul Patel | Health dot → U001 → no-match → invalid age (422) → raw JSON | Browser (AWS URL; fall back to localhost and say so) |
| 9 | Testing | Nakul Patel | 110 tests, 99% coverage, static checks, SAM lint | [testing_workflow.png](../docs/diagrams/rendered/testing_workflow.png) |
| 10 | Performance | Nakul Patel | Local table (actual) ⏳ vs. AWS table; cold-start count and Init Duration ⏳ | [local chart](../experiments/charts/local_latency_vs_vus.png) + ⏳ aws chart |
| 11 | Cost per 1,000 requests | Nakul Patel | Formula, measured billed duration ⏳, dated prices ⏳ | Cost table |
| 12 | Limitations, future work, team | All (Bhaumik, Sheel, Nakul) | Auth, real DB, ML experiment; who did what | [github_workflow.png](../docs/diagrams/rendered/github_workflow.png) |

**Rehearsal checklist:** each person rehearses with a timer · demo tested 1 hour before on the venue network · offline fallback (localhost + screenshots) ready · all members read [docs/10_viva_questions.md](../docs/10_viva_questions.md).
