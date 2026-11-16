// k6 load test for the matchmaking recommendation API.
//
// Usage (from the repository root):
//   k6 run -e BASE_URL=http://localhost:8000 -e SCENARIO=vu10 -e LABEL=local experiments/k6/load_test.js
//   k6 run -e BASE_URL=https://<api-id>.execute-api.<region>.amazonaws.com -e SCENARIO=vu10 -e LABEL=aws experiments/k6/load_test.js
//
// Environment variables:
//   BASE_URL    API base URL (no trailing slash)                     [required]
//   SCENARIO    smoke | vu1 | vu10 | vu25 | vu50                     [default: smoke]
//   LABEL       local | aws  (used in the output file name)          [default: local]
//   ENDPOINT    recommendations | health | mixed                     [default: recommendations]
//   THINK_TIME  seconds each VU waits between requests               [default: 1]
//   VUS / DURATION  override the scenario values
import http from "k6/http";
import { check, sleep } from "k6";
import { buildOptions, SCENARIOS } from "./scenarios.js";

const BASE_URL = (__ENV.BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
const SCENARIO = __ENV.SCENARIO || "smoke";
const LABEL = __ENV.LABEL || "local";
const ENDPOINT = __ENV.ENDPOINT || "recommendations";
const THINK_TIME = Number(__ENV.THINK_TIME || 1);

export const options = buildOptions(SCENARIO);

// Synthetic request bodies; rotated so the API does a little different work each time.
const PROFILES = [
  { user_id: "U001", age: 25, city: "Ahmedabad", education: "Engineering",
    interests: ["music", "travel", "technology"],
    preferences: { min_age: 23, max_age: 29, preferred_city: "Ahmedabad" } },
  { user_id: "U002", age: 30, city: "Mumbai", education: "Commerce",
    interests: ["movies", "cooking", "fitness"],
    preferences: { min_age: 26, max_age: 34, preferred_city: "Mumbai" } },
  { user_id: "U003", age: 28, city: "Pune", education: "Science",
    interests: ["reading", "hiking"], preferences: { min_age: 24, max_age: 34 } },
];
const HEADERS = { headers: { "Content-Type": "application/json" }, tags: { name: "POST /recommendations" } };

function callRecommendations() {
  const body = JSON.stringify(PROFILES[(__VU + __ITER) % PROFILES.length]);
  const res = http.post(`${BASE_URL}/recommendations`, body, HEADERS);
  check(res, {
    "status is 200": (r) => r.status === 200,
    "has recommendations": (r) => Array.isArray(r.json("recommendations")),
  });
}

function callHealth() {
  const res = http.get(`${BASE_URL}/health`, { tags: { name: "GET /health" } });
  check(res, { "health is 200": (r) => r.status === 200 });
}

export default function () {
  if (ENDPOINT === "health") callHealth();
  else if (ENDPOINT === "mixed" && __ITER % 5 === 0) callHealth();
  else callRecommendations();
  sleep(THINK_TIME);
}

// Write the raw k6 summary as JSON so experiments/analysis/collect_results.py can parse it.
export function handleSummary(data) {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const file = `experiments/results/raw/k6_${LABEL}_${SCENARIO}_${stamp}.json`;
  data.meta = { label: LABEL, scenario: SCENARIO, endpoint: ENDPOINT, base_url: BASE_URL,
    think_time_s: THINK_TIME,
    // Read from SCENARIOS/__ENV, not `options`: k6 v2 does not expose the exported options here.
    vus: Number(__ENV.VUS || SCENARIOS[SCENARIO].vus),
    duration: __ENV.DURATION || SCENARIOS[SCENARIO].duration };
  return {
    [file]: JSON.stringify(data, null, 2),
    stdout: `\nSaved k6 summary to ${file}\n`,
  };
}
