/*
 * Frontend configuration - the ONLY place you need to change the API URL.
 *
 * Local backend (uvicorn):      http://localhost:8000
 * Local SAM (sam local start-api): http://localhost:3000
 * AWS (after `sam deploy`):     the "ApiBaseUrl" stack output, e.g.
 *                               https://abc123.execute-api.ap-south-1.amazonaws.com
 *
 * You can also override it without editing this file by opening:
 *   index.html?api=https://abc123.execute-api.ap-south-1.amazonaws.com
 */
window.APP_CONFIG = {
  // Deployed dev stack (shaadi-recommendation-dev, ap-south-1). For local work use
  // http://localhost:8000, or open index.html?api=http://localhost:8000
  API_BASE_URL: "https://tkylvibnsi.execute-api.ap-south-1.amazonaws.com",
  REQUEST_TIMEOUT_MS: 10000,
};
