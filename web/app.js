/* Cognito Hosted UI Authorization Code + PKCE (no build step, no secret).
   Flows: sign-up/sign-in (redirect), sign-out (logout endpoint), reset
   (Hosted UI forgotPassword link), token exchange, JWT fetch to API. */
(function () {
  "use strict";
  const cfg = window.APP_CONFIG || {};
  const $ = (id) => document.getElementById(id);
  const statusEl = $("status"), outEl = $("output"), tokenEl = $("token");

  const required = ["cognitoDomain", "userPoolClientId", "apiEndpoint", "redirectUri"];
  const missing = required.filter((k) => !cfg[k] || String(cfg[k]).includes("REPLACE_ME"));

  function b64url(buf) {
    return btoa(String.fromCharCode(...new Uint8Array(buf)))
      .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  async function pkcePair() {
    const v = b64url(crypto.getRandomValues(new Uint8Array(32)));
    const c = b64url(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(v)));
    return { verifier: v, challenge: c };
  }
  const domain = () => `https://${cfg.cognitoDomain}`;
  const loginUrl = (p) =>
    `${domain()}/oauth2/authorize?response_type=code&client_id=${encodeURIComponent(cfg.userPoolClientId)}` +
    `&redirect_uri=${encodeURIComponent(cfg.redirectUri)}&scope=${encodeURIComponent("openid email profile")}` +
    `&code_challenge=${encodeURIComponent(p.challenge)}&code_challenge_method=S256`;

  async function signIn() {
    const pair = await pkcePair();
    sessionStorage.setItem("pkce_verifier", pair.verifier);
    window.location.assign(loginUrl(pair));
  }
  function signOut() {
    sessionStorage.removeItem("id_token");
    sessionStorage.removeItem("access_token");
    window.location.assign(
      `${domain()}/logout?client_id=${encodeURIComponent(cfg.userPoolClientId)}` +
      `&logout_uri=${encodeURIComponent(cfg.redirectUri)}`
    );
  }
  async function exchangeCode(code) {
    const verifier = sessionStorage.getItem("pkce_verifier");
    if (!verifier) throw new Error("Missing PKCE verifier (stale session). Sign in again.");
    const res = await fetch(`${domain()}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: cfg.userPoolClientId,
        redirect_uri: cfg.redirectUri,
        code,
        code_verifier: verifier,
      }),
    });
    if (!res.ok) throw new Error(`Token exchange failed: ${res.status} ${await res.text()}`);
    const tok = await res.json();
    sessionStorage.setItem("id_token", tok.id_token);
    sessionStorage.setItem("access_token", tok.access_token || "");
    sessionStorage.removeItem("pkce_verifier");
    window.history.replaceState({}, document.title, cfg.redirectUri);
  }
  async function api(path, useAuth = true) {
    const headers = {};
    if (useAuth) {
      const t = sessionStorage.getItem("id_token");
      if (!t) throw new Error("Not signed in — click Sign in first.");
      headers.Authorization = `Bearer ${t}`;
    }
    const res = await fetch(`${cfg.apiEndpoint}${path}`, { headers });
    const text = await res.text();
    let body;
    try { body = JSON.parse(text); } catch { body = text; }
    return { status: res.status, body };
  }
  function refresh() {
    const t = sessionStorage.getItem("id_token");
    const signedIn = Boolean(t);
    $("btn-login").disabled = signedIn;
    $("btn-logout").disabled = !signedIn;
    $("btn-me").disabled = !signedIn;
    $("btn-admin").disabled = !signedIn;
    statusEl.textContent = signedIn ? "Signed in. JWT attached to /me and /admin calls." : "Not signed in.";
    tokenEl.textContent = t ? `${t.slice(0, 80)}… (len ${t.length})` : "(none)";
  }

  $("btn-login").onclick = signIn;
  $("btn-logout").onclick = signOut;
  $("link-reset").onclick = async (e) => {
    e.preventDefault();
    // Hosted UI exposes reset on the sign-in page ("Forgot password?").
    // Deep-link by starting login; user clicks Forgot password there.
    await signIn();
  };
  $("btn-health").onclick = async () => {
    try { outEl.textContent = JSON.stringify(await api("/health", false), null, 2); }
    catch (e) { outEl.textContent = `Error: ${e.message}`; }
  };
  $("btn-me").onclick = async () => {
    try { outEl.textContent = JSON.stringify(await api("/me"), null, 2); }
    catch (e) { outEl.textContent = `Error: ${e.message}`; }
  };
  $("btn-admin").onclick = async () => {
    try { outEl.textContent = JSON.stringify(await api("/admin"), null, 2); }
    catch (e) { outEl.textContent = `Error: ${e.message}`; }
  };

  (async function init() {
    if (missing.length) {
      statusEl.textContent = `Configure web/config.js first (missing: ${missing.join(", ")}).`;
      outEl.textContent = "Copy web/config.example.js to web/config.js and fill values from `terraform output`.";
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const err = params.get("error");
    if (err) {
      statusEl.textContent = `Auth error: ${err} — ${params.get("error_description") || ""}`;
    } else if (code) {
      try {
        await exchangeCode(code);
        statusEl.textContent = "Signed in.";
      } catch (e) {
        statusEl.textContent = `Sign-in failed: ${e.message}`;
      }
    }
    refresh();
  })();
})();
