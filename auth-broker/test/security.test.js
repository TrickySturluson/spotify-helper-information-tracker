import test from "node:test";
import { generateKeyPairSync } from "node:crypto";
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
import {
  escapeHtml,
  handleRequest,
  rateLimit,
  githubAppJwt,
  assertNoConcurrentSpotifyJobs,
  exchangeForm,
  hasRequiredScopes,
  isAuthorizedOwner,
  OAuthStateStore,
  isSpotifyWorkflowPath,
  parseCookies,
  pkceChallenge,
  verifySpotifyIdentity,
} from "../src/index.js";

test("health endpoint is non-secret and bypasses OAuth configuration", async () => {
  const result = await handleRequest(new Request("https://broker.example/health"), {});
  assert.equal(result.status, 200);
  assert.deepEqual(await result.json(), { status: "ok", service: "shit-auth-broker" });
});

test("readiness fails closed unless broker config and Durable Object keyring are ready", async () => {
  const missing = await handleRequest(
    new Request("https://broker.example/ready"),
    { BROKER_BASE_URL: "https://broker.example" },
  );
  assert.equal(missing.status, 503);
  assert.deepEqual(await missing.json(), { status: "not_ready", service: "shit-auth-broker" });

  let probedUrl = "";
  const ready = await handleRequest(
    new Request("https://broker.example/ready"),
    {
      BROKER_BASE_URL: "https://broker.example",
      SPOTIFY_CLIENT_ID: "public-client-id",
      SPOTIFY_REFRESH_WORKFLOW_REFS: "approved-workflow-ref",
      SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS: "configured",
      AUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
      BROKER_REFRESH_RATE_LIMITER: { limit: async () => ({ success: true }) },
      SPOTIFY_CREDENTIAL_STORE: {
        idFromName: (name) => name,
        get: () => ({
          fetch: async (url) => {
            probedUrl = String(url);
            return Response.json({ status: "ready" });
          },
        }),
      },
    },
  );
  assert.equal(ready.status, 200);
  assert.deepEqual(await ready.json(), { status: "ready", service: "shit-auth-broker" });
  assert.equal(probedUrl, "https://spotify-credential.internal/ready");
});

test("readiness is rate limited and fails closed when the limiter is missing", async () => {
  const missing = await handleRequest(
    new Request("https://broker.example/ready"),
    {
      BROKER_BASE_URL: "https://broker.example",
      SPOTIFY_CLIENT_ID: "client",
      SPOTIFY_REFRESH_WORKFLOW_REFS: "approved",
      SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS: "configured",
      SPOTIFY_CREDENTIAL_STORE: { idFromName: (name) => name, get: () => ({ fetch: async () => Response.json({ status: "ready" }) }) },
    },
  );
  assert.equal(missing.status, 503);
  assert.deepEqual(await missing.json(), { status: "not_ready", service: "shit-auth-broker" });

  let calls = 0;
  const limited = await handleRequest(
    new Request("https://broker.example/ready"),
    { BROKER_BASE_URL: "https://broker.example", AUTH_RATE_LIMITER: { limit: async () => { calls += 1; return { success: false }; } }, BROKER_REFRESH_RATE_LIMITER: { limit: async () => ({ success: true }) } },
  );
  assert.equal(limited.status, 429);
  assert.equal(limited.headers.get("Retry-After"), "60");
  assert.deepEqual(await limited.json(), { status: "rate_limited", service: "shit-auth-broker" });
  assert.equal(calls, 1);
});

test("broker reports missing canonical base URL at a dedicated safe stage", async () => {
  const originalError = console.error;
  let diagnostic;
  console.error = (value) => { diagnostic = value; };
  try {
    const result = await handleRequest(new Request("https://broker.example/"), {});
    const body = await result.text();
    assert.equal(result.status, 200);
    assert.ok(body.includes("Diagnostic stage: broker.base_url_presence"));
    assert.doesNotMatch(body, /undefined|secret|token/i);
    assert.equal(diagnostic.stage, "broker.base_url_presence");
    assert.equal(diagnostic.error_class, "BrokerError");
  } finally {
    console.error = originalError;
  }
});

test("broker reports malformed canonical base URL at a dedicated safe stage", async () => {
  const originalError = console.error;
  let diagnostic;
  console.error = (value) => { diagnostic = value; };
  try {
    const result = await handleRequest(
      new Request("https://broker.example/"),
      { BROKER_BASE_URL: "not-a-url" },
    );
    const body = await result.text();
    assert.equal(result.status, 200);
    assert.ok(body.includes("Diagnostic stage: broker.base_url_parse"));
    assert.doesNotMatch(body, /not-a-url|secret|token/i);
    assert.equal(diagnostic.stage, "broker.base_url_parse");
    assert.equal(diagnostic.error_class, "BrokerError");
  } finally {
    console.error = originalError;
  }
});

test("Spotify callback reports a fixed safe stage when owner session validation fails", async () => {
  const originalError = console.error;
  let diagnostic;
  console.error = (value) => { diagnostic = value; };
  try {
    const result = await handleRequest(
      new Request("https://broker.example/spotify/callback"),
      {
        BROKER_BASE_URL: "https://broker.example",
        SPOTIFY_CLIENT_ID: "spotify-client",
        SPOTIFY_REDIRECT_URI: "https://broker.example/spotify/callback",
        GITHUB_APP_ID: "123456",
        GITHUB_APP_PRIVATE_KEY: "not-used-by-this-invalid-session-test",
        AUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
      },
    );
    const body = await result.text();
    assert.equal(result.status, 200);
    assert.ok(body.includes("Spotify authorization could not be verified"));
    assert.deepEqual(diagnostic, {
      event: "shit_auth_broker_request_failed",
      stage: "spotify_callback.state_validation",
      error_class: "BrokerError",
    });
  } finally {
    console.error = originalError;
  }
});

test("GitHub owner check is case-insensitive but rejects other identities", () => {
  assert.equal(isAuthorizedOwner("TrickySturluson"), true);
  assert.equal(isAuthorizedOwner("trickysturluson"), true);
  assert.equal(isAuthorizedOwner("someone-else"), false);
  assert.equal(isAuthorizedOwner(null), false);
});

test("required Spotify scopes must all be granted", () => {
  const scopes = [
    "user-read-private",
    "user-library-read",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
  ].join(" ");
  assert.equal(hasRequiredScopes(scopes), true);
  assert.equal(hasRequiredScopes(scopes.replace("playlist-modify-public", "")), false);
  assert.equal(hasRequiredScopes(""), false);
  assert.equal(hasRequiredScopes(undefined), false);
});

test("cookie parser handles multiple values and ignores malformed fragments", () => {
  assert.deepEqual(parseCookies(null), {});
  assert.deepEqual(parseCookies("a=one; __Host-session=abc_def; broken; b=two=three"), {
    a: "one",
    "__Host-session": "abc_def",
    b: "two=three",
  });
});

test("Spotify rate limits use only a verified owner session, never a caller-supplied cookie", async () => {
  const validSessionId = "A".repeat(43);
  const keys = [];
  const env = {
    BROKER_REFRESH_RATE_LIMITER: { limit: async ({ key }) => { keys.push(key); return { success: true }; } },
    OAUTH_STATE: {
      idFromName: () => "state",
      get: () => ({
        fetch: async (_url, init) => {
          const input = await new Request("https://state.internal", init).json();
          if (input.key === `oauth:session:${validSessionId}`) {
            return new Response(JSON.stringify({ value: { login: "TrickySturluson" } }), { status: 200 });
          }
          return new Response("{}", { status: 404 });
        },
      }),
    },
  };

  await rateLimit(new Request("https://broker.example/spotify/start", {
    headers: { Cookie: "__Host-shit_session=" + "B".repeat(43) },
  }), env, "spotify-start");
  await rateLimit(new Request("https://broker.example/spotify/start", {
    headers: { Cookie: "__Host-shit_session=" + validSessionId },
  }), env, "spotify-start");

  assert.deepEqual(keys, ["spotify-start:anonymous", `spotify-start:${validSessionId}`]);
});

test("broker refresh rate limits separate client IPs and verified workflows", async () => {
  const keys = [];
  let sessionLookups = 0;
  const env = {
    AUTH_RATE_LIMITER: { limit: async ({ key }) => { keys.push(key); return { success: true }; } },
    OAUTH_STATE: {
      idFromName: () => "state",
      get: () => {
        sessionLookups += 1;
        throw new Error("OIDC rate limiting must not depend on a browser session");
      },
    },
  };
  const workflowRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-auth-health-check.yml@refs/heads/main";
  await rateLimit(new Request("https://broker.example/internal/spotify/refresh", { method: "POST" }), env, "broker-refresh-ip", "203.0.113.10");
  await rateLimit(new Request("https://broker.example/internal/spotify/refresh", { method: "POST" }), env, "broker-refresh-workflow", workflowRef);
  assert.deepEqual(keys, ["broker-refresh-ip:203.0.113.10", "broker-refresh-workflow:" + workflowRef]);
  assert.equal(sessionLookups, 0);
});

test("HTML output escapes untrusted text", () => {
  assert.equal(escapeHtml("<script>alert('x')</script>"), "&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt;");
});

test("PKCE challenge is SHA-256 base64url without padding", async () => {
  assert.equal(
    await pkceChallenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"),
    "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
  );
});


test("broker rejects requests sent to a non-canonical host", async () => {
  const result = await handleRequest(
    new Request("https://attacker.example/"),
    { BROKER_BASE_URL: "https://trusted.example" },
  );
  assert.equal(result.status, 400);
});


test("concurrency gate allows only explicitly audited non-Spotify workflows", () => {
  assert.equal(isSpotifyWorkflowPath(".github/workflows/spotify-daily-midnight-cycle.yml@refs/heads/main"), true);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/spotify-auth-health-check.yml@refs/heads/main"), true);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/great-migration.yml@refs/heads/main"), true);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/playlist-fit-preview.yml@refs/heads/main"), true);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/daily-curator-tests.yml@refs/heads/main"), false);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/deploy-mobile-auth-broker.yml@refs/heads/main"), false);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/public-repository-security.yml@refs/heads/main"), false);
  assert.equal(isSpotifyWorkflowPath(""), true);
  assert.equal(isSpotifyWorkflowPath("unexpected/path"), true);
});


test("authorization landing page supports phone and desktop browsers without third-party scripts", async () => {
  const result = await handleRequest(
    new Request("https://trusted.example/"),
    { BROKER_BASE_URL: "https://trusted.example" },
  );
  const body = await result.text();
  assert.equal(result.status, 200);
  assert.equal(result.headers.get("cache-control"), "no-store");
  assert.match(body, /Continue with GitHub/);
  assert.match(body, /phone or desktop/);
  assert.doesNotMatch(body, /<script|https:\/\//i);
});


class MemoryDurableStorage {
  constructor() { this.values = new Map(); this.alarmAt = null; }
  async get(key) { return this.values.get(key); }
  async put(key, value) { this.values.set(key, value); }
  async delete(key) { return this.values.delete(key); }
  async list({ prefix = "" } = {}) {
    return new Map([...this.values.entries()].filter(([key]) => key.startsWith(prefix)));
  }
  async getAlarm() { return this.alarmAt; }
  async setAlarm(value) { this.alarmAt = value; }
  async transaction(callback) {
    const before = new Map(this.values);
    try { return await callback(); }
    catch (error) { this.values = before; throw error; }
  }
}

async function callStateStore(store, path, body) {
  return store.fetch(new Request("https://state.internal" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));
}

test("Durable Object consumes Spotify state once and binds it to the session", async () => {
  const storage = new MemoryDurableStorage();
  const store = new OAuthStateStore({ storage });
  const state = "state-one";
  const stateKey = "oauth:spotify-state:" + state;
  const activeKey = "oauth:spotify-active:session-one";
  await callStateStore(store, "/put-spotify", {
    key: stateKey,
    value: { sessionId: "session-one", verifier: "pkce-verifier" },
    activeKey,
    activeValue: state,
    ttl: 300,
  });

  const wrongSession = await callStateStore(store, "/consume-spotify", {
    key: stateKey, activeKey, sessionId: "other-session", expectedState: state,
  });
  assert.equal(wrongSession.status, 404);

  const consumed = await callStateStore(store, "/consume-spotify", {
    key: stateKey, activeKey, sessionId: "session-one", expectedState: state,
  });
  assert.equal(consumed.status, 200);
  assert.deepEqual((await consumed.json()).value, {
    sessionId: "session-one",
    verifier: "pkce-verifier",
  });

  const replay = await callStateStore(store, "/consume-spotify", {
    key: stateKey, activeKey, sessionId: "session-one", expectedState: state,
  });
  assert.equal(replay.status, 404);
});

test("Durable Object expires and cleans abandoned OAuth records", async () => {
  const storage = new MemoryDurableStorage();
  const store = new OAuthStateStore({ storage });
  await storage.put("oauth:expired", { value: "pending", expiresAt: Date.now() - 1 });
  await storage.put("oauth:live", { value: "pending", expiresAt: Date.now() + 60_000 });
  await store.alarm();
  assert.equal(await storage.get("oauth:expired"), undefined);
  assert.ok(await storage.get("oauth:live"));
  assert.ok(storage.alarmAt > Date.now());
});


test("deployment workflow injects every public runtime variable without dashboard drift", async () => {
  const config = await readFile(new URL("../wrangler.toml", import.meta.url), "utf8");
  const workflow = await readFile(new URL("../../.github/workflows/deploy-mobile-auth-broker.yml", import.meta.url), "utf8");
  assert.match(config, /name = "BROKER_REFRESH_RATE_LIMITER"/);
  assert.match(config, /simple = \\{ limit = 60, period = 60 \\}/);
  assert.doesNotMatch(config, /^\[vars\]/m);
  for (const name of [
    "BROKER_BASE_URL",
    "GITHUB_APP_CLIENT_ID",
    "GITHUB_APP_ID",
    "GITHUB_APP_REDIRECT_URI",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_REDIRECT_URI",
    "SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION",
    "SPOTIFY_REFRESH_WORKFLOW_REFS",
  ]) {
    if (name !== "SPOTIFY_REFRESH_WORKFLOW_REFS") {
      const sourceVariable = ({ GITHUB_APP_CLIENT_ID: "BROKER_GH_APP_CLIENT_ID", GITHUB_APP_ID: "BROKER_GH_APP_ID", GITHUB_APP_REDIRECT_URI: "BROKER_GH_APP_REDIRECT_URI" })[name] || name;
      assert.match(workflow, new RegExp("vars\\." + sourceVariable), name + " must come from a GitHub Actions variable");
    }
    assert.ok(workflow.includes('--var "' + name + ':'), name + ' must be passed to Wrangler');
  }
  const allowlistMatch = workflow.match(/expected_workflow_refs="([^"]+)"/);
  assert.ok(allowlistMatch, "deployment workflow must generate the exact OIDC workflow allowlist");
  const workflowRefs = allowlistMatch[1].split(",");
  assert.equal(workflowRefs.length, 9, "only the nine inventoried Spotify consumers are allowlisted");
  assert.ok(workflowRefs.every((ref) => ref.endsWith("@refs/heads/main")));
  assert.ok(workflowRefs.every((ref) => !ref.includes("*")));
  assert.match(workflow, /SPOTIFY_REFRESH_WORKFLOW_REFS=\$expected_workflow_refs/);
  assert.match(workflow, /BROKER_BASE_URL must use HTTPS/);
  assert.match(workflow, /GitHub callback URI must match BROKER_BASE_URL/);
  assert.match(workflow, /Spotify callback URI must match BROKER_BASE_URL/);
});


test("Worker observability redacts OAuth callback query strings", async () => {
  const config = await readFile(new URL("../wrangler.toml", import.meta.url), "utf8");
  const start = config.indexOf("[observability]\n");
  assert.ok(start >= 0, "Worker observability configuration must be explicit");
  const nextSection = config.indexOf("\n[", start + 1);
  const observability = config.slice(start, nextSection < 0 ? undefined : nextSection);
  assert.match(observability, /^enabled = true$/m);
  assert.match(observability, /^redact_query_string = true$/m,
    "OAuth code and state query parameters must be removed from observability URLs");
  const logsStart = config.indexOf("[observability.logs]");
  assert.ok(logsStart > start);
  assert.match(config.slice(logsStart), /^invocation_logs = true$/m);
});


test("broker source uses central encrypted storage and never writes a refresh-token secret", async () => {
  const source = await readFile(new URL("../src/index.js", import.meta.url), "utf8");
  assert.match(source, /const AUTH_WORKFLOW = "spotify-auth-health-check\.yml"/);
  assert.match(source, /authorizeCentralCredential\(env, tokenData\.refresh_token, spotifyIdentity\.id\)/);
  assert.match(source, /actions\/workflows\/\$\{AUTH_WORKFLOW\}\/dispatches/);
  assert.doesNotMatch(source, /actions\/secrets|SPOTIFY_REFRESH_TOKEN|saveRefreshToken/);
  assert.doesNotMatch(source, /\/v1\/playlists|\/playlists\/|playlist-items/i);
  assert.doesNotMatch(source, /console\.(?:log|info|warn)/);
  assert.match(
    source,
    /console\.error\(\{ event: "shit_auth_broker_request_failed", stage: diagnosticStage, error_class:/,
  );
  assert.match(source, /isAuthorizedOwner\(user\.login\)/);
  assert.doesNotMatch(source, /env\.GITHUB_OWNER/);
});


test("Spotify account identity is verified before central credential initialization", async () => {
  let calledUrl = "";
  let authorization = "";
  const identity = await verifySpotifyIdentity("short-lived-access-token", async (url, options) => {
    calledUrl = url;
    authorization = options.headers.Authorization;
    return new Response(JSON.stringify({ id: "spotify-account-id", display_name: "Example Listener" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  assert.equal(calledUrl, "https://api.spotify.com/v1/me");
  assert.equal(authorization, "Bearer short-lived-access-token");
  assert.deepEqual(identity, { id: "spotify-account-id", displayName: "Example Listener" });
});

test("Spotify identity verification fails closed on non-200 or missing identity", async () => {
  await assert.rejects(
    verifySpotifyIdentity("access-token", async () => new Response("", { status: 401 })),
    /Spotify account verification failed/,
  );
  await assert.rejects(
    verifySpotifyIdentity("access-token", async () => new Response(JSON.stringify({ display_name: "No ID" }), { status: 200 })),
    /verifiable account identity/,
  );
});


test("clean completion URL consumes one-time non-secret authorization summary", async () => {
  const resultId = "abcdefghijklmnopqrstuvwxyzABCDEF";
  let consumed = false;
  const env = {
    BROKER_BASE_URL: "https://trusted.example",
    OAUTH_STATE: {
      idFromName: () => "state",
      get: () => ({
        fetch: async (url, init) => {
          const request = new Request(url, init);
          const input = await request.json();
          if (input.key !== "oauth:result:" + resultId || consumed) {
            return new Response("{}", { status: 404 });
          }
          consumed = true;
          return new Response(JSON.stringify({
            value: {
              spotifyIdentity: { id: "spotify-id-123", displayName: "Example Listener" },
              verificationStarted: true,
            },
          }), { status: 200, headers: { "Content-Type": "application/json" } });
        },
      }),
    },
    AUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
  };
  const first = await handleRequest(new Request("https://trusted.example/complete?result=" + resultId), env);
  const body = await first.text();
  assert.equal(first.status, 200);
  assert.match(body, /Example Listener/);
  assert.match(body, /spotify-id-123/);
  assert.match(body, /read-only authentication check/);

  const replay = await handleRequest(new Request("https://trusted.example/complete?result=" + resultId), env);
  assert.match(await replay.text(), /expired or was already used/);
});

test("GitHub App JWT builder signs a valid RS256 token from PKCS1 PEM", async () => {
  const { privateKey, publicKey } = generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: { type: "spki", format: "pem" },
    privateKeyEncoding: { type: "pkcs1", format: "pem" },
  });
  const jwt = await githubAppJwt({ GITHUB_APP_ID: "123456", GITHUB_APP_PRIVATE_KEY: privateKey });
  const parts = jwt.split(".");
  assert.equal(parts.length, 3);
  const header = JSON.parse(Buffer.from(parts[0], "base64url").toString("utf8"));
  const payload = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8"));
  assert.deepEqual(header, { alg: "RS256", typ: "JWT" });
  assert.equal(payload.iss, "123456");
  assert.ok(payload.exp > payload.iat);

  const publicDer = Buffer.from(publicKey.replace(/-----BEGIN PUBLIC KEY-----|-----END PUBLIC KEY-----|\s/g, ""), "base64");
  const verifyKey = await crypto.subtle.importKey(
    "spki",
    publicDer,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const valid = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5",
    verifyKey,
    Buffer.from(parts[2], "base64url"),
    new TextEncoder().encode(parts[0] + "." + parts[1]),
  );
  assert.equal(valid, true);
});


test("workflow preflight checks every active state and blocks queued Spotify work", async () => {
  const originalFetch = globalThis.fetch;
  const checked = [];
  globalThis.fetch = async (url) => {
    const status = new URL(url).searchParams.get("status");
    checked.push(status);
    const queued = status === "queued";
    return new Response(JSON.stringify({
      total_count: queued ? 1 : 0,
      workflow_runs: queued ? [{ path: ".github/workflows/spotify-playlist-manager.yml" }] : [],
    }), { status: 200, headers: { "Content-Type": "application/json" } });
  };
  try {
    await assert.rejects(
      assertNoConcurrentSpotifyJobs("installation-token"),
      /queued or running/,
    );
    assert.deepEqual(checked.sort(), ["in_progress", "pending", "queued", "requested", "waiting"]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("workflow preflight fails closed when GitHub run data is incomplete", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ total_count: 0 }), { status: 200 });
  try {
    await assert.rejects(
      assertNoConcurrentSpotifyJobs("installation-token"),
      /Could not safely inspect/,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("OAuth provider code exchange posts PKCE fields in the form body, not the URL", async () => {
  const originalFetch = globalThis.fetch;
  let captured;
  globalThis.fetch = async (url, options) => {
    captured = { url: String(url), options };
    return new Response(JSON.stringify({ access_token: "short-lived", refresh_token: "rotated-refresh-token", scope: "user-read-private" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  try {
    const result = await exchangeForm("https://accounts.spotify.com/api/token", {
      client_id: "spotify-client-id",
      grant_type: "authorization_code",
      code: "one-time-authorization-code",
      redirect_uri: "https://broker.example.workers.dev/spotify/callback",
      code_verifier: "pkce-verifier",
    });
    assert.equal(captured.url, "https://accounts.spotify.com/api/token");
    assert.equal(captured.options.method, "POST");
    assert.equal(captured.options.headers["Content-Type"], "application/x-www-form-urlencoded");
    const body = new URLSearchParams(captured.options.body);
    assert.equal(body.get("code"), "one-time-authorization-code");
    assert.equal(body.get("code_verifier"), "pkce-verifier");
    assert.equal(body.get("redirect_uri"), "https://broker.example.workers.dev/spotify/callback");
    assert.equal(result.refresh_token, "rotated-refresh-token");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OAuth provider rejection returns a generic error without provider response details", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ error: "invalid_grant", error_description: "sensitive provider detail" }), {
    status: 400,
    headers: { "Content-Type": "application/json" },
  });
  try {
    await assert.rejects(
      exchangeForm("https://accounts.spotify.com/api/token", { grant_type: "authorization_code" }),
      (error) => {
        assert.match(error.message, /authorization provider rejected/);
        assert.doesNotMatch(error.message, /invalid_grant|sensitive provider detail/);
        return true;
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
