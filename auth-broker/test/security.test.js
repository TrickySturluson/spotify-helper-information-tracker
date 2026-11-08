import test from "node:test";
import assert from "node:assert/strict";
import {
  escapeHtml,
  handleRequest,
  hasRequiredScopes,
  isAuthorizedOwner,
  OAuthStateStore,
  isSpotifyWorkflowPath,
  parseCookies,
  pkceChallenge,
} from "../src/index.js";

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
  assert.deepEqual(parseCookies("a=one; __Host-session=abc_def; broken; b=two=three"), {
    a: "one",
    "__Host-session": "abc_def",
    b: "two=three",
  });
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


test("mobile landing page is local, no-store and contains no third-party script", async () => {
  const result = await handleRequest(
    new Request("https://trusted.example/"),
    { BROKER_BASE_URL: "https://trusted.example" },
  );
  const body = await result.text();
  assert.equal(result.status, 200);
  assert.equal(result.headers.get("cache-control"), "no-store");
  assert.match(body, /Continue with GitHub/);
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
