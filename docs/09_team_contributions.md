# 9. Team contributions

> Shared document. Each member updates their own row **with what they actually did**, linking commits and PRs.
> The planned division is in [TEAM_TASKS.md](../TEAM_TASKS.md) and [CONTRIBUTION_MATRIX.md](../CONTRIBUTION_MATRIX.md). The process is in [GITHUB_WORKFLOW.md](../GITHUB_WORKFLOW.md).

## 9.1 Planned allocation (approximately equal)

| Member | Workstream | Branch | Primary ownership | Est. effort |
|---|---|---|---|---|
| Bhaumik Luhar (202301468) | Case study, documentation, architecture | `feature/case-study-architecture` | `research/`, `docs/` (01–05, 09, 10), `docs/diagrams/`, `reports/`, `presentation/` | ≈ 44 h (33%) |
| Sheel Shah (202301420) | Backend, API, serverless, infrastructure | `feature/serverless-backend` | `backend/`, `infrastructure/`, `pytest.ini`, `pyproject.toml` | ≈ 45 h (34%) |
| Nakul Patel (202301261) | Frontend, experiments, testing, deployment | `feature/frontend-experiments` | `frontend/`, `experiments/`, `docs/06–08`, `test_reports/`, `scripts/` | ≈ 44 h (33%) |

### Why this is balanced

- **Bhaumik** has many files, but they are writing-heavy. Source verification and the report are real research effort, and the report depends on everyone's output.
- **Sheel** has few files, but they are the most technically dense: correctness, tests, IaC, and the **first real AWS deployment**.
- **Nakul** spans UI plus measurement. The AWS experiments, cold-start analysis and cost model are new work that cannot be done until deployment.
- Each member makes about 5 milestone commits, and each reviews the other two (see the review table in the contribution matrix).

## 9.2 Dependencies

| Producer → consumer | Hand-over artefact | Due |
|---|---|---|
| Sheel → Nakul | API contract (`models.py`), local API | end of Week 2 |
| Sheel → Nakul | Deployed `ApiBaseUrl` | mid Week 4 |
| Nakul → Bhaumik | `local_summary.md`, `cloud_summary.md`, charts, cost table | end of Week 4 |
| Bhaumik → all | Verified source list, viva Q&A | Week 3 / Week 5 |

## 9.3 Actual contributions log (fill in honestly)

| Member | Commits (links) | PRs authored | PRs reviewed | Main deliverables | Notes |
|---|---|---|---|---|---|
| Bhaumik Luhar (202301468) | 5 milestone commits (`research/`, `docs/01-05,09,10`, `reports/`, `presentation/`) | `feature/case-study-architecture` $\rightarrow$ `main` | Nakul Patel (`feature/frontend-experiments`) | Week 1 research synthesis, sources register verification (`S0`–`S7`, `C1`–`C13`), case-study analysis (`docs/01`–`05`), report writing lead (`reports/`), presentation deck (`presentation/`), viva Q&A (`docs/10`) | Reconciled trade-press 67B claim with official AWS Mumbai 2016 launch announcement [S7]; documented 40% DB speedup, 55% Aurora, >80% serverless savings |
| Sheel Shah (202301420) | | | | | |
| Nakul Patel (202301261) | | | | | |

## 9.4 AI-assistance statement

_The initial repository scaffold (code, tests, scripts and document drafts) was generated with an AI coding assistant. Each member reviewed, ran, modified and is responsible for the files they committed. The research verification, AWS deployment, cloud measurements, report writing and presentation were carried out by the team._
