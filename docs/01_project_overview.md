# 1. Project overview

> **Owner:** Bhaumik Luhar (202301468) · **Status:** Complete (Reviewed) · **Group:** 49 (IT457 Cloud Computing)

## 1.1 Purpose

This IT457 group project studies how **Shaadi.com**, a large online matchmaking service, uses Amazon Web Services. We then build a **small serverless prototype** that demonstrates the same cloud computing principles at classroom scale.

## 1.2 Two separate parts

| Part | Question it answers | Documents |
|---|---|---|
| **A. Real-world case study** | What does public evidence say about Shaadi.com's use of AWS, and why does a matchmaking company need the cloud? | [02](02_case_study_analysis.md), [03](03_real_world_architecture.md), [research/](../research/sources.md) |
| **B. Student prototype** | Can we build, deploy, test and measure an event-driven serverless recommendation API, and what do latency, cold starts and cost look like? | [04](04_student_architecture.md)–[08](08_cost_analysis.md) |

Part B is **inspired by** Part A. It is not a copy of Shaadi.com's system, whose internal design is not public.

## 1.3 What the prototype does

A user submits a profile (age, city, education, interests, preferences). `POST /recommendations` runs on AWS Lambda behind API Gateway and returns the top N **synthetic** candidates. Each candidate has a 0–100 compatibility score, a per-component breakdown, and plain-English reasons. `GET /health` reports service status.

## 1.4 Cloud computing concepts demonstrated

| Concept | Where |
|---|---|
| Serverless compute (FaaS) | AWS Lambda function `lambda_handler.handler` |
| Event-driven invocation | Each HTTP request is an API Gateway **event** that triggers Lambda |
| Elastic scaling | Lambda adds execution environments as concurrency grows; tested at 1–50 virtual users |
| Pay-per-use pricing | Cost model per 1,000 requests ([08](08_cost_analysis.md)) |
| Managed API front door | API Gateway HTTP API: routing, CORS, throttling |
| Observability | CloudWatch Logs, structured JSON logs, Logs Insights queries |
| Security | Least-privilege IAM role, no secrets in code, synthetic data only |
| Infrastructure as Code | AWS SAM `template.yaml` |

## 1.5 Scope and non-goals

- **In scope:** API, validation, explainable scoring, frontend, tests, IaC, local and AWS experiments, cost model.
- **Out of scope:** real user data, authentication, machine learning training, a production database, mobile apps.

## 1.6 Success criteria

1. All automated tests pass (currently 110/110 locally).
2. The stack deploys with `sam deploy` and the frontend works against the AWS URL.
3. Latency, concurrency and cold-start measurements are collected **on AWS** and clearly labelled.
4. Cost per 1,000 requests is calculated from measured duration and dated AWS prices.
5. Every team member can explain the whole system in the viva.
