# Report outline (about 10 pages)

> Owner: Bhaumik Luhar (assembly), with sections from Sheel Shah and Nakul Patel · Target: about 10 A4 pages + references
> ⚠️ Fill results sections **only** with labelled real measurements. Placeholders are marked **⏳**.
> Figures live in [`reports/figures/`](figures/). Copy them from `docs/diagrams/rendered/` and `experiments/charts/`.

| # | Section | Pages | Lead | Content and sources | Figures / tables |
|---|---|---|---|---|---|
| 1 | **Title page** | — | Bhaumik | "Serverless Matchmaking Recommendations: A Shaadi.com Cloud Case Study", IT457 Cloud Computing, Group 49 (Bhaumik Luhar [202301468], Sheel Shah [202301420], Nakul Patel [202301261]), Autumn 2026 | — |
| 2 | **Abstract** | 0.25 | Bhaumik | 150–200 words: case, prototype, method, *real* key results, conclusion. Write it last. | — |
| 3 | **Introduction** | 0.5 | Bhaumik | Motivation, objectives, the two-part structure (real case vs. prototype), report roadmap | — |
| 4 | **Shaadi.com background** | 0.75 | Bhaumik | [docs/02 §2.1](../docs/02_case_study_analysis.md); scale figures with verification status | Table: claims register (from research/sources.md) |
| 5 | **Problem statement** | 0.5 | Bhaumik | Matchmaking as filtering and ranking at scale, bursty load, privacy, cost | — |
| 6 | **Cloud computing challenges** | 0.5 | Bhaumik | Elasticity, cost, data volume, ops burden, experimentation ([docs/02 §2.3](../docs/02_case_study_analysis.md)) | Table: challenge → cloud response → source |
| 7 | **AWS and cloud solution analysis** | 1 | Bhaumik | Services reported in public sources; DynamoDB, gp3, serverless photo pipeline; the 67B claim discussion | Fig: [case_study_overview](../docs/diagrams/rendered/case_study_overview.png) |
| 8 | **Architecture (proposed)** | 1 | Sheel | [docs/04](../docs/04_student_architecture.md) design decisions table | Fig: [student_architecture](../docs/diagrams/rendered/student_architecture.png), [deployment_architecture](../docs/diagrams/rendered/deployment_architecture.png) |
| 9 | **Student implementation** | 0.75 | Sheel | Components, API contract, synthetic data, event flow | Fig: [request_flow](../docs/diagrams/rendered/request_flow.png) |
| 10 | **Implementation details** | 1 | Sheel / Nakul | Scoring formula and weights, validation (400 vs. 422), handler and logging, SAM template, frontend | Fig: [recommendation_flow](../docs/diagrams/rendered/recommendation_flow.png); table of weights |
| 11 | **Testing methodology** | 0.75 | Nakul | Test categories (110 tests, 99% coverage), static checks, load-test design, result labels | Fig: [testing_workflow](../docs/diagrams/rendered/testing_workflow.png) |
| 12 | **Experimental results** | 1.5 | Nakul | 12a: **actual local** table and chart (available). 12b: **actual AWS** latency at 1/10/25/50 VUs. 12c: **actual AWS cold starts** (Init Duration about 1.1 s). 12d: local vs. AWS discussion | [local chart](../experiments/charts/local_latency_vs_vus.png); ⏳ aws charts |
| 13 | **Cost analysis** | 0.75 | Nakul | Formula, inputs (billed duration 12.593 ms, prices dated 2026-11-16), cost per 1,000 = $0.002510, discussion | Table from [docs/08](../docs/08_cost_analysis.md) |
| 14 | **Limitations** | 0.25 | all | No auth, synthetic data, not ML, short tests, single region, unverified claims | — |
| 15 | **Future improvements** | 0.25 | all | DynamoDB, EventBridge, Cognito, arm64, provisioned concurrency, CI/CD, ML experiment | — |
| 16 | **Conclusion** | 0.25 | Bhaumik | Answer the objectives with evidence | — |
| 17 | **References** | — | Bhaumik | IEEE style from [research/sources.md](../research/sources.md) + AWS docs | — |
| 18 | **Team contributions** | 0.25 | all | From [docs/09](../docs/09_team_contributions.md) + AI-assistance statement | Table |
| — | Appendix (optional) | — | — | API examples, Logs Insights queries, full test list | [timeline](../docs/diagrams/rendered/project_timeline.png), [github workflow](../docs/diagrams/rendered/github_workflow.png) |

## Placeholders to replace before submission

- [x] AWS latency table (`experiments/results/cloud_summary.md`)
- [x] AWS charts (`experiments/charts/aws_*.png`)
- [x] Cold-start results (`experiments/results/cold_start_results.csv`)
- [x] Cost per 1,000 requests with price-check date
- [x] Screenshots: frontend against the AWS URL (`reports/figures/frontend_*_aws.png`)
- [ ] ⏳ Screenshots: Lambda console, CloudWatch REPORT line (needs AWS console access)
- [x] Week 1 research content (`research/week1_summary.md`)
- [x] Member names and IDs (Group 49)

## Writing rules

- Every number has a source ([S#]) or a measurement label.
- Describe "Shaadi.com does X" only from sources. Describe "our prototype does Y" only from code.
- Never round away bad results. Report errors, outliers and failed runs honestly.
