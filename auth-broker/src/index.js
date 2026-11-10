import { SpotifyRefreshLease, verifyActionsOidc } from "./refresh-lock.js";
import { SpotifyCredentialStore } from "./credential-store.js";
export { SpotifyRefreshLease, SpotifyCredentialStore };

const OWNER = "TrickySturluson";
const REPOSITORY = "spotify-helper-information-tracker";
const AUTH_WORKFLOW = "spotify-auth-health-check.yml";
const REQUIRED_SCOPES = [
  "user-read-private",
  "user-library-read",
  "playlist-read-private",
  "playlist-read-collaborative",
  "playlist-modify-private",
  "playlist-modify-public",
];
const SESSION_TTL = 900;
const OAUTH_TTL = 300;

class BrokerError extends Error {}

function base64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function decodeBase64(value) {
  const binary = atob(value);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function randomValue(bytes = 32) {
  const value = new Uint8Array(bytes);
  crypto.getRandomValues(value);
  return base64Url(value);
}

async function sha256(value) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
}

export async function pkceChallenge(verifier) {
  return base64Url(await sha256(verifier));
}

export function parseCookies(header = "") {
  const result = {};
  for (const part of String(header || "").split(";")) {
    const index = part.indexOf("=");
    if (index < 1) continue;
    const key = part.slice(0, index).trim();
    const value = part.slice(index + 1).trim();
    if (key) result[key] = value;
  }
  return result;
}

export function isAuthorizedOwner(login, expected = OWNER) {
  return typeof login === "string" && login.toLowerCase() === expected.toLowerCase();
}

export function hasRequiredScopes(scope) {
  if (typeof scope !== "string") return false;
  const granted = new Set(scope.split(/\s+/).filter(Boolean));
  return REQUIRED_SCOPES.every((item) => granted.has(item));
}

function cookie(name, value, maxAge) {
  return `${name}=${value}; Path=/; Max-Age=${maxAge}; Secure; HttpOnly; SameSite=Lax`;
}

function clearCookie(name) {
  return cookie(name, "", 0);
}

function response(body, status = 200, headers = {}) {
  const output = new Headers(headers);
  output.set("X-Content-Type-Options", "nosniff");
  output.set("Referrer-Policy", "no-referrer");
  output.set("X-Frame-Options", "DENY");
  output.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  output.set("Cache-Control", "no-store");
  output.set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
  output.set("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
  return new Response(body, { status, headers: output });
}

function page(title, message, link = null) {
  const safeTitle = escapeHtml(title);
  const safeMessage = escapeHtml(message);
  const linkHtml = link
    ? `<p><a href="${escapeHtml(link.href)}">${escapeHtml(link.label)}</a></p>`
    : "";
  return response(
    `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${safeTitle}</title><body><main><h1>${safeTitle}</h1><p>${safeMessage}</p>${linkHtml}</main></body></html>`,
    200,
    { "Content-Type": "text/html; charset=utf-8" },
  );
}

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function redirect(url, headers = {}) {
  return response(null, 302, { Location: url, ...headers });
}

export async function rateLimit(request, env, route, actorOverride = null) {
  if (!env.AUTH_RATE_LIMITER) throw new BrokerError("Rate limiter is not configured.");
  // Never trust a caller-supplied cookie as a rate-limit identity. Resolve the
  // session against server-side state first; invalid/missing cookies share the
  // anonymous bucket, while only a verified owner session gets its own bucket.
  // Internal OIDC routes may pass a verified workflow identity after JWT validation.
  const session = actorOverride === null && route.startsWith("spotify-") ? await getSession(request, env) : null;
  const actor = actorOverride ?? (session ? session.id : "anonymous");
  const result = await env.AUTH_RATE_LIMITER.limit({ key: `${route}:${actor}` });
  if (!result.success) throw new BrokerError("Too many attempts.");
}

function stateStub(env) {
  if (!env.OAUTH_STATE) throw new BrokerError("Strongly consistent OAuth state storage is not configured.");
  return env.OAUTH_STATE.get(env.OAUTH_STATE.idFromName("shit-mobile-oauth-state"));
}

async function stateCall(env, operation, payload) {
  const result = await stateStub(env).fetch("https://oauth-state.internal/" + operation, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (result.status === 404) return null;
  if (!result.ok) throw new BrokerError("Secure OAuth state storage failed.");
  const data = await result.json();
  return data.value === undefined ? true : data.value;
}

async function stateGet(env, key) { return stateCall(env, "get", { key }); }
async function statePut(env, key, value, ttl) { return stateCall(env, "put", { key, value, ttl }); }
async function stateDelete(env, key) { return stateCall(env, "delete", { key }); }
async function stateConsume(env, key) { return stateCall(env, "consume", { key }); }
async function statePutSpotify(env, key, value, activeKey, activeValue, ttl) {
  return stateCall(env, "put-spotify", { key, value, activeKey, activeValue, ttl });
}
async function stateConsumeSpotify(env, key, activeKey, sessionId, expectedState) {
  return stateCall(env, "consume-spotify", { key, activeKey, sessionId, expectedState });
}

export class OAuthStateStore {
  constructor(ctx) { this.ctx = ctx; }

  async scheduleCleanup(expiresAt) {
    const current = await this.ctx.storage.getAlarm();
    if (!current || expiresAt < current) await this.ctx.storage.setAlarm(expiresAt);
  }

  async fetch(request) {
    if (request.method !== "POST") return new Response("Not found.", { status: 404 });
    const input = await request.json();
    const storage = this.ctx.storage;
    const now = Date.now();
    const path = new URL(request.url).pathname;

    if (path === "/put" || path === "/put-spotify") {
      const ttl = Math.max(1, Math.min(Number(input.ttl) || 1, SESSION_TTL));
      const expiresAt = now + ttl * 1000;
      await storage.transaction(async () => {
        await storage.put(input.key, { value: input.value, expiresAt });
        if (path === "/put-spotify") await storage.put(input.activeKey, { value: input.activeValue, expiresAt });
      });
      await this.scheduleCleanup(expiresAt);
      return Response.json({ ok: true });
    }

    if (path === "/get") {
      const record = await storage.get(input.key);
      if (!record || record.expiresAt <= now) {
        if (record) await storage.delete(input.key);
        return Response.json({}, { status: 404 });
      }
      return Response.json({ value: record.value });
    }

    if (path === "/delete") {
      await storage.delete(input.key);
      return Response.json({ ok: true });
    }

    if (path === "/consume" || path === "/consume-spotify") {
      const value = await storage.transaction(async () => {
        const record = await storage.get(input.key);
        if (!record || record.expiresAt <= now) {
          if (record) await storage.delete(input.key);
          return null;
        }
        if (path === "/consume-spotify") {
          const active = await storage.get(input.activeKey);
          if (!active || active.expiresAt <= now || active.value !== input.expectedState || record.value.sessionId !== input.sessionId) return null;
          await storage.delete(input.activeKey);
        }
        await storage.delete(input.key);
        return record.value;
      });
      return value === null ? Response.json({}, { status: 404 }) : Response.json({ value });
    }

    return new Response("Not found.", { status: 404 });
  }

  async alarm() {
    const entries = await this.ctx.storage.list({ prefix: "oauth:" });
    const now = Date.now();
    let nextExpiry = null;
    for (const [key, record] of entries) {
      if (!record || record.expiresAt <= now) await this.ctx.storage.delete(key);
      else if (nextExpiry === null || record.expiresAt < nextExpiry) nextExpiry = record.expiresAt;
    }
    if (nextExpiry !== null) await this.ctx.storage.setAlarm(nextExpiry);
  }
}
async function getSession(request, env) {
  const id = parseCookies(request.headers.get("Cookie"))["__Host-shit_session"];
  if (!id || !/^[A-Za-z0-9_-]{40,}$/.test(id)) return null;
  const session = await stateGet(env, `oauth:session:${id}`);
  if (!session) return null;
  if (!isAuthorizedOwner(session.login)) return null;
  return { id, login: session.login };
}

function requireEnv(env, names) {
  for (const name of names) {
    if (!String(env[name] || "").trim()) throw new BrokerError("Authorization service is not configured.");
  }
}

export async function exchangeForm(url, fields, headers = {}) {
  const result = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json", ...headers },
    body: new URLSearchParams(fields),
  });
  if (!result.ok) throw new BrokerError("An authorization provider rejected the request.");
  const data = await result.json();
  if (data.error) throw new BrokerError("An authorization provider rejected the request.");
  return data;
}

async function githubApi(path, token, method = "GET", body = undefined) {
  const result = await fetch(`https://api.github.com${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "SHIT-Mobile-Authorization-Broker",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!result.ok) throw new BrokerError("GitHub could not complete the secure credential update.");
  return result.status === 204 ? null : result.json();
}

function derLength(length) {
  if (length < 128) return Uint8Array.of(length);
  const bytes = [];
  let value = length;
  while (value > 0) {
    bytes.unshift(value & 255);
    value >>= 8;
  }
  return Uint8Array.of(0x80 | bytes.length, ...bytes);
}

function der(tag, content) {
  const length = derLength(content.length);
  const result = new Uint8Array(1 + length.length + content.length);
  result[0] = tag;
  result.set(length, 1);
  result.set(content, 1 + length.length);
  return result;
}

function concat(...parts) {
  const result = new Uint8Array(parts.reduce((sum, part) => sum + part.length, 0));
  let offset = 0;
  for (const part of parts) {
    result.set(part, offset);
    offset += part.length;
  }
  return result;
}

function pkcs8PrivateKey(pem) {
  const isPkcs1 = pem.includes("BEGIN RSA PRIVATE KEY");
  const raw = pem.replace(/-----BEGIN [^-]+-----/g, "").replace(/-----END [^-]+-----/g, "").replace(/\s/g, "");
  const pkcs1 = decodeBase64(raw);
  if (!isPkcs1) return pkcs1;
  // PKCS#8 wrapper for rsaEncryption OID 1.2.840.113549.1.1.1.
  const algorithm = Uint8Array.from([0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00]);
  return der(0x30, concat(Uint8Array.of(0x02, 0x01, 0x00), algorithm, der(0x04, pkcs1)));
}

export async function githubAppJwt(env) {
  const pem = String(env.GITHUB_APP_PRIVATE_KEY || "");
  const key = await crypto.subtle.importKey(
    "pkcs8",
    pkcs8PrivateKey(pem),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const now = Math.floor(Date.now() / 1000);
  const header = base64Url(new TextEncoder().encode(JSON.stringify({ alg: "RS256", typ: "JWT" })));
  const payload = base64Url(new TextEncoder().encode(JSON.stringify({
    iat: now - 60,
    exp: now + 540,
    iss: String(env.GITHUB_APP_ID),
  })));
  const signingInput = `${header}.${payload}`;
  const signature = new Uint8Array(await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    key,
    new TextEncoder().encode(signingInput),
  ));
  return `${signingInput}.${base64Url(signature)}`;
}

async function installationToken(env, setDiagnosticStage = () => {}) {
  setDiagnosticStage("spotify_callback.github_app_jwt");
  const jwt = await githubAppJwt(env);
  setDiagnosticStage("spotify_callback.github_installation_lookup");
  const installation = await githubApi(`/repos/${OWNER}/${REPOSITORY}/installation`, jwt);
  if (!installation?.id) throw new BrokerError("GitHub App is not installed on the SHIT repository.");
  setDiagnosticStage("spotify_callback.github_installation_token_creation");
  const token = await githubApi(
    `/app/installations/${installation.id}/access_tokens`,
    jwt,
    "POST",
    {
      repositories: [REPOSITORY],
      permissions: { actions: "write" },
    },
  );
  if (!token?.token) throw new BrokerError("GitHub App installation token was not issued.");
  return token.token;
}

const SAFE_CONCURRENT_WORKFLOWS = new Set([
  "babel-ai-continuation.yml",
  "daily-curator-tests.yml",
  "deploy-mobile-auth-broker.yml",
  "library-freshness-review.yml",
  "mobile-auth-broker-tests.yml",
  "public-repository-security.yml",
]);

// Fail closed: only workflows explicitly audited as not using Spotify credentials
// may overlap reauthorization. Unknown/missing workflow paths are treated as unsafe.
export function isSpotifyWorkflowPath(path) {
  const value = String(path || "");
  const marker = ".github/workflows/";
  const markerIndex = value.indexOf(marker);
  if (markerIndex < 0) return true;
  const remainder = value.slice(markerIndex + marker.length);
  const workflowFile = remainder.split("@")[0].split("/")[0];
  if (!workflowFile.endsWith(".yml") && !workflowFile.endsWith(".yaml")) return true;
  return !SAFE_CONCURRENT_WORKFLOWS.has(workflowFile.toLowerCase());
}

export async function assertNoConcurrentSpotifyJobs(token) {
  const activeStatuses = ["queued", "in_progress", "requested", "waiting", "pending"];
  const responses = await Promise.all(activeStatuses.map((status) =>
    githubApi(
      `/repos/${OWNER}/${REPOSITORY}/actions/runs?status=${status}&per_page=100`,
      token,
    )
  ));
  const active = [];
  for (const runs of responses) {
    if (!runs || typeof runs.total_count !== "number" || !Array.isArray(runs.workflow_runs)) {
      throw new BrokerError("Could not safely inspect active GitHub Actions runs; authorization was stopped.");
    }
    if (runs.total_count > 100) {
      throw new BrokerError("Too many active GitHub Actions runs to safely authorize. Wait and retry.");
    }
    active.push(...runs.workflow_runs.filter((run) => isSpotifyWorkflowPath(run.path)));
  }
  if (active.length) {
    throw new BrokerError("A Spotify-related GitHub workflow is queued or running. Wait for it to finish before reauthorizing.");
  }
}

function authorizationSavedMessage(spotifyIdentity, verificationStarted) {
  const account = `${spotifyIdentity.displayName || "Spotify user"} (ID ${spotifyIdentity.id})`;
  return verificationStarted
    ? `Spotify account verified: ${account}. Your refresh credential is encrypted in the central SHIT authentication broker. SHIT has started a read-only authentication check. No playlist was unlocked or changed.`
    : `Spotify account verified: ${account}. Your refresh credential is encrypted in the central SHIT authentication broker, but the read-only check could not be started. Open Actions and run the Spotify Auth Health Check manually. No playlist was unlocked or changed.`;
}

async function authorizeCentralCredential(env, refreshToken, accountId) {
  if (!env.SPOTIFY_CREDENTIAL_STORE || !String(env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS || "").trim()) {
    throw new BrokerError("Central Spotify credential storage is not configured; no credential was saved.");
  }
  const stub = env.SPOTIFY_CREDENTIAL_STORE.get(env.SPOTIFY_CREDENTIAL_STORE.idFromName("spotify-primary"));
  const result = await stub.fetch("https://spotify-credential.internal/authorize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accountId, refreshToken }),
  });
  if (!result.ok) {
    throw new BrokerError("Central Spotify credential storage rejected this authorization. No existing credential was overwritten.");
  }
  return result.json();
}

async function dispatchAuthHealthCheck(token) {
  try {
    await githubApi(`/repos/${OWNER}/${REPOSITORY}/actions/workflows/${AUTH_WORKFLOW}/dispatches`, token, "POST", { ref: "main" });
    return true;
  } catch {
    return false;
  }
}

export async function verifySpotifyIdentity(accessToken, fetchImpl = fetch) {
  if (typeof accessToken !== "string" || !accessToken) {
    throw new BrokerError("Spotify did not issue a usable access token.");
  }
  const result = await fetchImpl("https://api.spotify.com/v1/me", {
    headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
  });
  if (!result.ok) throw new BrokerError("Spotify account verification failed; no credential was saved.");
  const profile = await result.json();
  if (!profile || typeof profile.id !== "string" || !profile.id) {
    throw new BrokerError("Spotify did not return a verifiable account identity; no credential was saved.");
  }
  return {
    id: profile.id,
    displayName: typeof profile.display_name === "string" ? profile.display_name : "",
  };
}

async function githubLoginCallback(request, env, url) {
  const cookies = parseCookies(request.headers.get("Cookie"));
  const state = url.searchParams.get("state") || "";
  const code = url.searchParams.get("code") || "";
  if (!state || state !== cookies["__Host-shit_gh_state"] || !code) {
    throw new BrokerError("GitHub sign-in could not be verified. Start again.");
  }
  const stateKey = `oauth:github-state:${state}`;
  const stateValue = await stateConsume(env, stateKey);
  if (!stateValue || typeof stateValue.verifier !== "string") throw new BrokerError("GitHub sign-in expired. Start again.");
  const tokenData = await exchangeForm("https://github.com/login/oauth/access_token", {
    client_id: env.GITHUB_APP_CLIENT_ID,
    client_secret: env.GITHUB_APP_CLIENT_SECRET,
    code,
    redirect_uri: env.GITHUB_APP_REDIRECT_URI,
    code_verifier: stateValue.verifier,
  });
  if (!tokenData.access_token) throw new BrokerError("GitHub sign-in failed.");
  const userResponse = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${tokenData.access_token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "SHIT-Mobile-Authorization-Broker",
    },
  });
  if (!userResponse.ok) throw new BrokerError("GitHub identity could not be verified.");
  const user = await userResponse.json();
  if (!isAuthorizedOwner(user.login)) {
    throw new BrokerError("This GitHub account is not authorized to manage SHIT.");
  }
  const sessionId = randomValue(32);
  await statePut(env, `oauth:session:${sessionId}`, { login: user.login }, SESSION_TTL);
  return redirect(new URL("/spotify/start", env.BROKER_BASE_URL).toString(), {
    "Set-Cookie": cookie("__Host-shit_session", sessionId, SESSION_TTL),
  });
}

async function spotifyCallback(request, env, url, setDiagnosticStage = () => {}) {
  setDiagnosticStage("spotify_callback.session_lookup");
  const cookies = parseCookies(request.headers.get("Cookie"));
  const session = await getSession(request, env);
  setDiagnosticStage("spotify_callback.state_validation");
  const state = url.searchParams.get("state") || "";
  const code = url.searchParams.get("code") || "";
  if (!session || !state || state !== cookies["__Host-shit_spotify_state"] || !code) {
    throw new BrokerError("Spotify authorization could not be verified. Start again.");
  }
  setDiagnosticStage("spotify_callback.state_consumption");
  const key = `oauth:spotify-state:${state}`;
  const activeKey = `oauth:spotify-active:${session.id}`;
  const stateData = await stateConsumeSpotify(env, key, activeKey, session.id, state);
  if (!stateData) throw new BrokerError("Spotify authorization expired, was replayed, or was superseded. Start again.");
  const githubToken = await installationToken(env, setDiagnosticStage);
  setDiagnosticStage("spotify_callback.concurrent_workflow_check");
  await assertNoConcurrentSpotifyJobs(githubToken);
  setDiagnosticStage("spotify_callback.spotify_code_exchange");
  const tokenData = await exchangeForm("https://accounts.spotify.com/api/token", {
    client_id: env.SPOTIFY_CLIENT_ID,
    grant_type: "authorization_code",
    code,
    redirect_uri: env.SPOTIFY_REDIRECT_URI,
    code_verifier: stateData.verifier,
  });
  setDiagnosticStage("spotify_callback.scope_validation");
  if (!hasRequiredScopes(tokenData.scope)) {
    throw new BrokerError("Spotify did not grant every permission required by SHIT. Start again and approve all requested permissions.");
  }
  setDiagnosticStage("spotify_callback.spotify_identity_verification");
  const spotifyIdentity = await verifySpotifyIdentity(tokenData.access_token);
  // Hand the long-lived credential directly to the encrypted Durable Object.
  // It is never written to a GitHub Actions secret or returned to the browser.
  setDiagnosticStage("spotify_callback.central_credential_write");
  await authorizeCentralCredential(env, tokenData.refresh_token, spotifyIdentity.id);
  setDiagnosticStage("spotify_callback.health_workflow_dispatch");
  const verificationStarted = await dispatchAuthHealthCheck(githubToken);
  // Keep the callback URL (which contains a one-time authorization code) out
  // of the final browser address bar. Store only the non-secret result summary.
  setDiagnosticStage("spotify_callback.completion_state_storage");
  const resultId = randomValue(24);
  try {
    await statePut(env, `oauth:result:${resultId}`, { spotifyIdentity, verificationStarted }, 120);
  } catch {
    // The credential is already persisted. If the transient completion record
    // cannot be written, show the accurate saved state rather than a false failure.
    return page(
      "Spotify authorization saved",
      authorizationSavedMessage(spotifyIdentity, verificationStarted),
      { href: `https://github.com/${OWNER}/${REPOSITORY}/actions/workflows/${AUTH_WORKFLOW}`, label: "View SHIT authentication check" },
    );
  }
  // The session contains no provider credential and expires automatically.
  // Cleanup is best-effort because the browser cookie is cleared on this response.
  setDiagnosticStage("spotify_callback.session_cleanup");
  try { await stateDelete(env, `oauth:session:${session.id}`); } catch {}
  setDiagnosticStage("spotify_callback.completion_redirect");
  return redirect(new URL(`/complete?result=${resultId}`, env.BROKER_BASE_URL).toString());
}

async function handleRefreshLock(request, env, url) {
  if (request.method !== "POST") return response("Not found.", 404);
  if (!env.SPOTIFY_REFRESH_LEASE || !String(env.REFRESH_LOCK_WORKFLOW_REFS || "").trim()) {
    return response(JSON.stringify({ error: "lock_unavailable" }), 503, { "Content-Type": "application/json" });
  }
  await rateLimit(request, env, "refresh-lock");
  const authorization = request.headers.get("Authorization") || "";
  const match = authorization.match(/^Bearer ([A-Za-z0-9._-]+)$/);
  if (!match) return response(JSON.stringify({ error: "unauthorized" }), 401, { "Content-Type": "application/json" });
  const length = Number(request.headers.get("Content-Length") || 0);
  if (length > 2048 || !request.headers.get("Content-Type")?.toLowerCase().startsWith("application/json")) {
    return response(JSON.stringify({ error: "invalid_request" }), 400, { "Content-Type": "application/json" });
  }
  let rawBody;
  try { rawBody = await request.text(); } catch {
    return response(JSON.stringify({ error: "invalid_request" }), 400, { "Content-Type": "application/json" });
  }
  if (rawBody.length > 2048) return response(JSON.stringify({ error: "invalid_request" }), 413, { "Content-Type": "application/json" });
  let body;
  try { body = JSON.parse(rawBody); } catch {
    return response(JSON.stringify({ error: "invalid_request" }), 400, { "Content-Type": "application/json" });
  }
  let identity;
  try {
    const allowed = String(env.REFRESH_LOCK_WORKFLOW_REFS).split(",").map((item) => item.trim()).filter(Boolean);
    identity = await verifyActionsOidc(match[1], { allowedWorkflowRefs: allowed });
  } catch {
    return response(JSON.stringify({ error: "unauthorized" }), 401, { "Content-Type": "application/json" });
  }
  const owner = identity.workflowRef + ":" + identity.runId + ":" + identity.runAttempt;
  const operation = url.pathname.slice("/internal/refresh-lock/".length);
  if (!["acquire", "renew", "release"].includes(operation)) {
    return response(JSON.stringify({ error: "not_found" }), 404, { "Content-Type": "application/json" });
  }
  const stub = env.SPOTIFY_REFRESH_LEASE.get(env.SPOTIFY_REFRESH_LEASE.idFromName("spotify-refresh-token"));
  const result = await stub.fetch("https://refresh-lease.internal/" + operation, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, owner }),
  });
  const output = await result.text();
  return response(output, result.status, { "Content-Type": "application/json" });
}


async function handleBrokerRefresh(request, env) {
  if (request.method !== "POST") return response("Not found.", 404, { "Content-Type": "text/plain; charset=utf-8" });
  if (!env.SPOTIFY_CREDENTIAL_STORE || !String(env.SPOTIFY_REFRESH_WORKFLOW_REFS || "").trim()) {
    return response(JSON.stringify({ error: "credential_store_unavailable" }), 503, { "Content-Type": "application/json" });
  }
  // Apply an edge-level per-client-IP limit before expensive JWT/JWKS work.
  // CF-Connecting-IP is supplied by Cloudflare; never trust X-Forwarded-For.
  const clientIp = request.headers.get("CF-Connecting-IP") || "unknown";
  await rateLimit(request, env, "broker-refresh-ip", clientIp);
  const authorization = request.headers.get("Authorization") || "";
  const match = authorization.match(/^Bearer ([A-Za-z0-9._-]+)$/);
  if (!match) return response(JSON.stringify({ error: "unauthorized" }), 401, { "Content-Type": "application/json" });
  const contentType = request.headers.get("Content-Type") || "";
  if (!contentType.toLowerCase().startsWith("application/json")) {
    return response(JSON.stringify({ error: "invalid_request" }), 415, { "Content-Type": "application/json" });
  }
  const length = Number(request.headers.get("Content-Length") || 0);
  if (length > 2048) return response(JSON.stringify({ error: "invalid_request" }), 413, { "Content-Type": "application/json" });
  let input;
  try {
    const raw = await request.text();
    if (raw.length > 2048) return response(JSON.stringify({ error: "invalid_request" }), 413, { "Content-Type": "application/json" });
    input = JSON.parse(raw);
  } catch {
    return response(JSON.stringify({ error: "invalid_request" }), 400, { "Content-Type": "application/json" });
  }
  if (!input || typeof input.operationId !== "string" || !/^[A-Za-z0-9_-]{32,128}$/.test(input.operationId)) {
    return response(JSON.stringify({ error: "invalid_request" }), 400, { "Content-Type": "application/json" });
  }
  if (input.forceRefresh !== undefined && typeof input.forceRefresh !== "boolean") {
    return response(JSON.stringify({ error: "invalid_request" }), 400, { "Content-Type": "application/json" });
  }
  let verifiedClaims;
  try {
    const allowed = String(env.SPOTIFY_REFRESH_WORKFLOW_REFS).split(",").map((item) => item.trim()).filter(Boolean);
    verifiedClaims = await verifyActionsOidc(match[1], { allowedWorkflowRefs: allowed, audience: "shit-spotify-refresh" });
  } catch {
    return response(JSON.stringify({ error: "unauthorized" }), 401, { "Content-Type": "application/json" });
  }
  const authHealthWorkflowRef = `${OWNER}/${REPOSITORY}/.github/workflows/spotify-auth-health-check.yml@refs/heads/main`;
  if (input.forceRefresh === true && verifiedClaims.workflowRef !== authHealthWorkflowRef) {
    return response(JSON.stringify({ error: "force_refresh_not_allowed" }), 403, { "Content-Type": "application/json" });
  }
  // Rate-limit only after OIDC verification and isolate buckets by the verified
  // workflow_ref. Anonymous traffic cannot exhaust a shared bucket for all jobs.
  await rateLimit(request, env, "broker-refresh", verifiedClaims.workflowRef);
  const stub = env.SPOTIFY_CREDENTIAL_STORE.get(env.SPOTIFY_CREDENTIAL_STORE.idFromName("spotify-primary"));
  const result = await stub.fetch("https://spotify-credential.internal/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ operationId: input.operationId, forceRefresh: input.forceRefresh === true }),
  });
  const output = await result.text();
  const headers = { "Content-Type": "application/json" };
  const retryAfter = result.headers.get("Retry-After");
  if (retryAfter && retryAfter.length <= 128 && !/[\r\n]/.test(retryAfter) && (/^\d{1,8}$/.test(retryAfter) || Number.isFinite(Date.parse(retryAfter)))) headers["Retry-After"] = retryAfter;
  return response(output, result.status, headers);
}

export async function handleRequest(request, env) {
  const url = new URL(request.url);
  let diagnosticStage = "request.initialization";
  try {
    // Non-secret liveness endpoint for deployment verification. It deliberately
    // bypasses OAuth configuration checks and reveals no credential/config values.
    if (url.pathname === "/health" && request.method === "GET") {
      return response(
        JSON.stringify({ status: "ok", service: "shit-auth-broker" }),
        200,
        { "Content-Type": "application/json; charset=utf-8" },
      );
    }
    if (url.pathname === "/ready" && request.method === "GET") {
      if (!env.AUTH_RATE_LIMITER) {
        return response(
          JSON.stringify({ status: "not_ready", service: "shit-auth-broker" }),
          503,
          { "Content-Type": "application/json; charset=utf-8" },
        );
      }
      const readinessLimit = await env.AUTH_RATE_LIMITER.limit({ key: "readiness:anonymous" });
      if (!readinessLimit.success) {
        return response(
          JSON.stringify({ status: "rate_limited", service: "shit-auth-broker" }),
          429,
          { "Content-Type": "application/json; charset=utf-8", "Retry-After": "60" },
        );
      }
      if (
        !env.SPOTIFY_CREDENTIAL_STORE ||
        !String(env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS || "").trim() ||
        !String(env.SPOTIFY_REFRESH_WORKFLOW_REFS || "").trim() ||
        !String(env.SPOTIFY_CLIENT_ID || "").trim()
      ) {
        return response(
          JSON.stringify({ status: "not_ready", service: "shit-auth-broker" }),
          503,
          { "Content-Type": "application/json; charset=utf-8" },
        );
      }
      try {
        const stub = env.SPOTIFY_CREDENTIAL_STORE.get(env.SPOTIFY_CREDENTIAL_STORE.idFromName("spotify-primary"));
        const probe = await stub.fetch("https://spotify-credential.internal/ready");
        if (!probe.ok) throw new Error("credential store unavailable");
        const result = await probe.json();
        if (result.status !== "ready") throw new Error("credential store unavailable");
        return response(
          JSON.stringify({ status: "ready", service: "shit-auth-broker" }),
          200,
          { "Content-Type": "application/json; charset=utf-8" },
        );
      } catch {
        return response(
          JSON.stringify({ status: "not_ready", service: "shit-auth-broker" }),
          503,
          { "Content-Type": "application/json; charset=utf-8" },
        );
      }
    }
    diagnosticStage = "broker.base_url_presence";
    requireEnv(env, ["BROKER_BASE_URL"]);
    diagnosticStage = "broker.base_url_parse";
    let canonicalOrigin;
    try {
      canonicalOrigin = new URL(String(env.BROKER_BASE_URL).trim());
    } catch {
      throw new BrokerError("The authorization service base URL is invalid.");
    }
    diagnosticStage = "broker.canonical_host_check";
    if (canonicalOrigin.protocol !== "https:" || url.origin !== canonicalOrigin.origin) {
      return response("Invalid host.", 400, { "Content-Type": "text/plain; charset=utf-8" });
    }
    diagnosticStage = "broker.route_dispatch";
    if (url.pathname.startsWith("/internal/refresh-lock/")) return await handleRefreshLock(request, env, url);
    if (url.pathname === "/internal/spotify/refresh") return await handleBrokerRefresh(request, env);

    if (url.pathname === "/" && request.method === "GET") {
      return page("SHIT Spotify authorization", "Use this secure browser flow from a phone or desktop. Sign in with the repository owner account, then approve Spotify. This process never edits playlists.", {
        href: "/auth/github/start",
        label: "Continue with GitHub",
      });
    }

    if (url.pathname === "/auth/github/start" && request.method === "GET") {
      await rateLimit(request, env, "github-start");
      requireEnv(env, ["GITHUB_APP_CLIENT_ID", "GITHUB_APP_REDIRECT_URI"]);
      const state = randomValue(24);
      const verifier = randomValue(64);
      const challenge = await pkceChallenge(verifier);
      await statePut(env, `oauth:github-state:${state}`, { verifier }, OAUTH_TTL);
      const target = new URL("https://github.com/login/oauth/authorize");
      target.search = new URLSearchParams({
        client_id: env.GITHUB_APP_CLIENT_ID,
        redirect_uri: env.GITHUB_APP_REDIRECT_URI,
        state,
        code_challenge_method: "S256",
        code_challenge: challenge,
      });
      return redirect(target.toString(), { "Set-Cookie": cookie("__Host-shit_gh_state", state, OAUTH_TTL) });
    }

    if (url.pathname === "/auth/github/callback" && request.method === "GET") {
      await rateLimit(request, env, "github-callback");
      requireEnv(env, ["GITHUB_APP_CLIENT_ID", "GITHUB_APP_CLIENT_SECRET", "GITHUB_APP_REDIRECT_URI"]);
      const result = await githubLoginCallback(request, env, url);
      result.headers.append("Set-Cookie", clearCookie("__Host-shit_gh_state"));
      return result;
    }

    if (url.pathname === "/spotify/start" && request.method === "GET") {
      await rateLimit(request, env, "spotify-start");
      requireEnv(env, ["SPOTIFY_CLIENT_ID", "SPOTIFY_REDIRECT_URI", "GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY"]);
      const session = await getSession(request, env);
      if (!session) return redirect("/auth/github/start");
      // Do not send the user into Spotify consent while a Spotify workflow is active.
      const githubToken = await installationToken(env);
      await assertNoConcurrentSpotifyJobs(githubToken);
      const verifier = randomValue(64);
      const state = randomValue(24);
      const challenge = await pkceChallenge(verifier);
      await statePutSpotify(
        env,
        `oauth:spotify-state:${state}`,
        { sessionId: session.id, verifier },
        `oauth:spotify-active:${session.id}`,
        state,
        OAUTH_TTL,
      );
      const target = new URL("https://accounts.spotify.com/authorize");
      target.search = new URLSearchParams({
        client_id: env.SPOTIFY_CLIENT_ID,
        response_type: "code",
        redirect_uri: env.SPOTIFY_REDIRECT_URI,
        scope: REQUIRED_SCOPES.join(" "),
        state,
        code_challenge_method: "S256",
        code_challenge: challenge,
      });
      return redirect(target.toString(), { "Set-Cookie": cookie("__Host-shit_spotify_state", state, OAUTH_TTL) });
    }

    if (url.pathname === "/spotify/callback" && request.method === "GET") {
      diagnosticStage = "spotify_callback.rate_limit";
      await rateLimit(request, env, "spotify-callback");
      diagnosticStage = "spotify_callback.configuration";
      requireEnv(env, ["SPOTIFY_CLIENT_ID", "SPOTIFY_REDIRECT_URI", "GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY"]);
      const result = await spotifyCallback(request, env, url, (stage) => { diagnosticStage = stage; });
      result.headers.append("Set-Cookie", clearCookie("__Host-shit_spotify_state"));
      result.headers.append("Set-Cookie", clearCookie("__Host-shit_session"));
      return result;
    }

    if (url.pathname === "/complete" && request.method === "GET") {
      await rateLimit(request, env, "complete");
      const resultId = url.searchParams.get("result") || "";
      if (!/^[A-Za-z0-9_-]{30,}$/.test(resultId)) {
        return page("Authorization result unavailable", "Start a new authorization from the SHIT Spotify authorization page.", { href: "/", label: "Start again" });
      }
      const result = await stateConsume(env, `oauth:result:${resultId}`);
      if (!result || !result.spotifyIdentity) {
        return page("Authorization result expired", "The one-time completion link has expired or was already used. Your saved credential is not affected.", { href: "/", label: "Return to SHIT authorization" });
      }
      return page(
        "Spotify authorization saved",
        authorizationSavedMessage(result.spotifyIdentity, result.verificationStarted),
        { href: `https://github.com/${OWNER}/${REPOSITORY}/actions/workflows/${AUTH_WORKFLOW}`, label: "View SHIT authentication check" },
      );
    }

    return response("Not found.", 404, { "Content-Type": "text/plain; charset=utf-8" });
  } catch (error) {
    // Log only a fixed diagnostic stage and error class. Never log exception text,
    // provider responses, OAuth codes, tokens, cookies, state values, or request URLs.
    const expected = error instanceof BrokerError;
    console.error({ event: "shit_auth_broker_request_failed", stage: diagnosticStage, error_class: expected ? "BrokerError" : "UnexpectedError" });
    const message = expected
      ? `${error.message} Diagnostic stage: ${diagnosticStage}.`
      : `The authorization service encountered an unexpected error. Diagnostic stage: ${diagnosticStage}.`;
    return page("Authorization not completed", message, { href: "/", label: "Start again" });
  }
}

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  },
};


// FILE OVERVIEW
// Purpose: SHIT-wide OAuth recovery broker and OIDC-authenticated refresh prototype.
// Runtime: Cloudflare Worker with transactional OAuth state, refresh coordination, credential storage and rate limiting.
// Credentials: GitHub App credentials and (future, not yet configured) credential-store encryption key are Worker secrets.
// Side effects: Owner-consented OAuth stores credentials only in the encrypted Durable Object and dispatches read-only auth health;
//               OIDC refresh route returns only a short-lived access token after encrypted credential commit.
// Safety: Exact GitHub owner/workflow identity, PKCE, one-time state, AES-GCM credential records,
//         no token logging, no refresh-token return, no playlist endpoints or writes.
// Status: Credential-store/OIDC route are draft prototypes; not deployed or enabled.
// Related: auth-broker/README.md, project/goals/mobile-cloud-operation/ROADMAP.md.
