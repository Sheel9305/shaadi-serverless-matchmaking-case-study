/*
 * Match Recommender frontend (vanilla JS, no build step).
 * API base URL comes from config.js, or from ?api=... in the page URL.
 */
(function () {
  "use strict";

  const config = window.APP_CONFIG || {};
  const params = new URLSearchParams(window.location.search);
  const API_BASE_URL = (params.get("api") || config.API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
  const TIMEOUT_MS = config.REQUEST_TIMEOUT_MS || 10000;

  // Must match EDUCATION_CATEGORIES in backend/src/models.py
  const EDUCATION = ["Engineering", "Medicine", "Science", "Commerce", "Management", "Arts", "Law"];
  const SUGGESTED_INTERESTS = ["music", "travel", "technology", "reading", "cooking", "fitness", "movies",
    "photography", "dance", "cricket", "art", "yoga"];
  const WEIGHTS = { age: 30, location: 25, education: 15, interests: 30 };

  // Synthetic demo profiles (fictional).
  const PRESETS = {
    ahmedabad: { user_id: "U001", age: 25, city: "Ahmedabad", education: "Engineering",
      interests: ["music", "travel", "technology"],
      preferences: { min_age: 23, max_age: 29, preferred_city: "Ahmedabad" }, top_n: 5 },
    mumbai: { user_id: "U002", age: 30, city: "Mumbai", education: "Commerce",
      interests: ["movies", "cooking", "fitness"],
      preferences: { min_age: 26, max_age: 34, preferred_city: "Mumbai" }, top_n: 5 },
    strict: { user_id: "U003", age: 28, city: "Ahmedabad", education: "Science",
      interests: ["reading", "hiking"],
      preferences: { min_age: 24, max_age: 34, preferred_city: "Pune", city_required: true }, top_n: 5 },
    nomatch: { user_id: "U004", age: 65, city: "Delhi", education: "Arts",
      interests: ["art"], preferences: { min_age: 60, max_age: 70 }, top_n: 5 },
  };

  const $ = (id) => document.getElementById(id);
  const form = $("profile-form");
  const els = {
    user_id: $("user_id"), age: $("age"), city: $("city"), education: $("education"),
    interests: $("interests"), min_age: $("min_age"), max_age: $("max_age"),
    preferred_city: $("preferred_city"), preferred_education: $("preferred_education"),
    city_required: $("city_required"), top_n: $("top_n"),
  };

  // ---------- Setup ----------
  function populateSelects() {
    EDUCATION.forEach((e) => {
      els.education.add(new Option(e, e));
      els.preferred_education.add(new Option(e, e));
    });
  }

  function renderChips() {
    const box = $("interest-suggestions");
    box.replaceChildren();
    const current = parseInterests(els.interests.value);
    SUGGESTED_INTERESTS.forEach((name) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = name;
      chip.setAttribute("aria-pressed", String(current.includes(name)));
      chip.addEventListener("click", () => toggleInterest(name));
      box.appendChild(chip);
    });
  }

  function toggleInterest(name) {
    const list = parseInterests(els.interests.value);
    const next = list.includes(name) ? list.filter((i) => i !== name) : [...list, name];
    els.interests.value = next.join(", ");
    renderChips();
  }

  /** Split, trim, lowercase and de-duplicate the comma-separated interests. */
  function parseInterests(text) {
    const seen = new Set();
    return text.split(",").map((s) => s.trim().toLowerCase()).filter((s) => s && !seen.has(s) && seen.add(s));
  }

  function applyPreset(key) {
    const p = PRESETS[key];
    if (!p) return;
    els.user_id.value = p.user_id;
    els.age.value = p.age;
    els.city.value = p.city;
    els.education.value = p.education;
    els.interests.value = p.interests.join(", ");
    els.min_age.value = p.preferences.min_age;
    els.max_age.value = p.preferences.max_age;
    els.preferred_city.value = p.preferences.preferred_city || "";
    els.preferred_education.value = p.preferences.preferred_education || "";
    els.city_required.checked = Boolean(p.preferences.city_required);
    els.top_n.value = String(p.top_n);
    syncRangeLabels();
    renderChips();
    clearFormError();
  }

  function syncRangeLabels() {
    $("min_age_out").textContent = els.min_age.value;
    $("max_age_out").textContent = els.max_age.value;
  }

  // ---------- Request building & client-side checks ----------
  function buildPayload() {
    const preferences = {
      min_age: Number(els.min_age.value),
      max_age: Number(els.max_age.value),
    };
    if (els.preferred_city.value.trim()) preferences.preferred_city = els.preferred_city.value.trim();
    if (els.preferred_education.value) preferences.preferred_education = els.preferred_education.value;
    if (els.city_required.checked) preferences.city_required = true;

    return {
      user_id: els.user_id.value.trim(),
      age: els.age.value === "" ? null : Number(els.age.value),
      city: els.city.value.trim(),
      education: els.education.value,
      interests: parseInterests(els.interests.value),
      preferences,
      top_n: Number(els.top_n.value),
    };
  }

  /** Quick friendly checks. The API re-validates everything (never trust the client). */
  function clientErrors(p) {
    const errs = [];
    if (!/^[A-Za-z0-9_-]{1,20}$/.test(p.user_id)) errs.push("User ID: use 1–20 letters, digits, - or _.");
    if (!Number.isInteger(p.age) || p.age < 18 || p.age > 100) errs.push("Age: enter a whole number from 18 to 100.");
    if (p.city.length < 2) errs.push("City: enter at least 2 characters.");
    if (p.interests.length === 0) errs.push("Interests: add at least one interest.");
    if (p.interests.length > 10) errs.push("Interests: at most 10 interests.");
    if (p.preferences.min_age > p.preferences.max_age) errs.push("Preferences: min age must not exceed max age.");
    if (p.preferences.city_required && !p.preferences.preferred_city) errs.push("Preferences: choose a preferred city for the strict city filter.");
    return errs;
  }

  function showFormError(title, items) {
    const box = $("form-error");
    box.replaceChildren();
    const strong = document.createElement("strong");
    strong.textContent = title;
    box.appendChild(strong);
    if (items && items.length) {
      const ul = document.createElement("ul");
      items.forEach((t) => { const li = document.createElement("li"); li.textContent = t; ul.appendChild(li); });
      box.appendChild(ul);
    }
    box.hidden = false;
  }

  function clearFormError() {
    $("form-error").hidden = true;
    Object.values(els).forEach((el) => el.removeAttribute("aria-invalid"));
  }

  // ---------- Networking ----------
  async function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      clearTimeout(timer);
    }
  }

  async function checkHealth() {
    const dot = $("health-dot");
    const text = $("health-text");
    dot.className = "dot pending";
    text.textContent = "Checking API…";
    const t0 = performance.now();
    try {
      const res = await fetchWithTimeout(`${API_BASE_URL}/health`);
      const ms = Math.round(performance.now() - t0);
      const body = await res.json();
      if (res.ok && body.status === "healthy") {
        dot.className = "dot ok";
        text.textContent = `API healthy · ${body.environment} · ${body.profiles_loaded} profiles · ${ms} ms`;
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err) {
      dot.className = "dot down";
      text.textContent = `API unreachable (${err.name === "AbortError" ? "timeout" : err.message})`;
    }
  }

  async function submit(event) {
    event.preventDefault();
    clearFormError();
    const payload = buildPayload();
    const errs = clientErrors(payload);
    if (errs.length) {
      showFormError("Please fix the following:", errs);
      return;
    }

    setLoading(true);
    const t0 = performance.now();
    try {
      const res = await fetchWithTimeout(`${API_BASE_URL}/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const rtt = performance.now() - t0;
      const body = await res.json().catch(() => ({}));
      $("raw-json").textContent = JSON.stringify(body, null, 2);
      $("request-id").textContent = body.request_id ? `request_id: ${body.request_id}` : "";
      showMetrics(rtt, res.headers.get("X-Response-Time-Ms"), body.candidates_after_filters);

      if (!res.ok) {
        handleApiError(res.status, body);
        return;
      }
      renderResults(body);
    } catch (err) {
      const msg = err.name === "AbortError"
        ? `The API did not respond within ${TIMEOUT_MS / 1000} s.`
        : `Could not reach the API at ${API_BASE_URL}. Is the backend running and is CORS allowed?`;
      renderMessage(msg, true);
      $("metrics").hidden = true;
    } finally {
      setLoading(false);
    }
  }

  function handleApiError(status, body) {
    const error = body.error || {};
    const details = (error.details || []).map((d) => `${d.field}: ${d.message}`);
    (error.details || []).forEach((d) => {
      const key = d.field.split(".").pop();
      if (els[key]) els[key].setAttribute("aria-invalid", "true");
    });
    showFormError(`${status} ${error.code || "ERROR"} — ${error.message || "Request failed"}`, details);
    renderMessage(`The API rejected the request (HTTP ${status}). See the details above the button.`, true);
  }

  function setLoading(on) {
    const btn = $("submit-btn");
    btn.disabled = on;
    btn.classList.toggle("loading", on);
    btn.querySelector(".btn-label").textContent = on ? "Finding matches…" : "Generate recommendations";
    $("results-panel").setAttribute("aria-busy", String(on));
  }

  function showMetrics(rtt, serverMs, filtered) {
    $("metrics").hidden = false;
    $("m-rtt").textContent = `${Math.round(rtt)} ms`;
    $("m-server").textContent = serverMs ? `${Number(serverMs).toFixed(1)} ms` : "n/a";
    $("m-filtered").textContent = filtered ?? "–";
  }

  // ---------- Rendering ----------
  function renderMessage(text, isError) {
    const div = document.createElement("div");
    div.className = `message${isError ? " error" : ""}`;
    div.textContent = text;
    $("results").replaceChildren(div);
  }

  function scoreColor(score) {
    if (score >= 75) return "var(--good)";
    if (score >= 50) return "var(--gold)";
    return "var(--accent)";
  }

  function renderResults(body) {
    const list = body.recommendations || [];
    if (list.length === 0) {
      renderMessage(body.message || "No candidates matched your preferences.", false);
      return;
    }
    const tpl = $("card-template");
    const frag = document.createDocumentFragment();
    list.forEach((rec, idx) => {
      const node = tpl.content.firstElementChild.cloneNode(true);
      const ring = node.querySelector(".score-ring");
      ring.style.setProperty("--p", rec.compatibility_score);
      ring.style.setProperty("--c", scoreColor(rec.compatibility_score));
      ring.setAttribute("aria-label", `Compatibility ${rec.compatibility_score} out of 100`);
      node.querySelector(".score-value").textContent = rec.compatibility_score;
      node.querySelector(".cand-id").textContent = `Profile ${rec.candidate_id}`;
      node.querySelector(".rank").textContent = `#${idx + 1}`;
      node.querySelector(".meta").textContent = `${rec.age} yrs · ${rec.city} · ${rec.education}`;
      node.style.animationDelay = `${idx * 40}ms`;

      const ul = node.querySelector(".reasons");
      rec.reasons.forEach((r) => { const li = document.createElement("li"); li.textContent = r; ul.appendChild(li); });

      const bars = node.querySelector(".bars");
      Object.entries(WEIGHTS).forEach(([key, max]) => {
        const value = rec.score_breakdown[key];
        const bar = document.createElement("div");
        bar.className = "bar";
        bar.innerHTML = `<span></span><div class="bar-track"><div class="bar-fill"></div></div>`;
        bar.querySelector("span").textContent = `${key} ${Math.round(value)}/${max}`;
        bar.querySelector(".bar-fill").style.width = `${(value / max) * 100}%`;
        bars.appendChild(bar);
      });
      frag.appendChild(node);
    });
    $("results").replaceChildren(frag);
  }

  // ---------- Wire up ----------
  populateSelects();
  applyPreset("ahmedabad");
  $("api-url-label").textContent = `API: ${API_BASE_URL}`;
  $("preset").addEventListener("change", (e) => applyPreset(e.target.value));
  els.min_age.addEventListener("input", syncRangeLabels);
  els.max_age.addEventListener("input", syncRangeLabels);
  els.interests.addEventListener("input", renderChips);
  $("health-refresh").addEventListener("click", checkHealth);
  form.addEventListener("submit", submit);
  checkHealth();
})();
