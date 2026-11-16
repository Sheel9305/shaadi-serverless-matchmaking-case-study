// Load-test scenarios for k6 (https://k6.io). Kept deliberately small so a
// student AWS account is never flooded. Values mirror ../configs/scenarios.json.
//
// Each scenario is a constant number of virtual users (VUs) looping for a fixed
// duration. A VU sends one request, then sleeps THINK_TIME seconds.

export const SCENARIOS = {
  smoke: { vus: 1, duration: "15s" },
  vu1: { vus: 1, duration: "30s" },
  vu10: { vus: 10, duration: "30s" },
  vu25: { vus: 25, duration: "30s" },
  vu50: { vus: 50, duration: "30s" },
};

export function buildOptions(name) {
  const s = SCENARIOS[name];
  if (!s) {
    throw new Error(`Unknown SCENARIO "${name}". Use one of: ${Object.keys(SCENARIOS).join(", ")}`);
  }
  return {
    scenarios: {
      [name]: {
        executor: "constant-vus",
        vus: Number(__ENV.VUS || s.vus),
        duration: __ENV.DURATION || s.duration,
        gracefulStop: "5s",
      },
    },
    // Report the percentiles required by the experiment plan.
    summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"],
    thresholds: {
      http_req_failed: ["rate<0.01"],    // < 1 % errors
      http_req_duration: ["p(95)<1000"], // p95 under 1 s (generous for cold starts)
    },
  };
}
