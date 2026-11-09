import test from "node:test";
import assert from "node:assert/strict";
import { SpotifyCredentialStore, CREDENTIAL_OPERATION_TTL_MS } from "../src/credential-store.js";

class MemoryStorage {
  constructor() { this.values = new Map(); let tail = Promise.resolve(); this.tail = () => tail; }
  async get(key) { return this.values.get(key); }
  async put(key, value) { this.values.set(key, structuredClone(value)); }
  async transaction(callback) {
    const run = this.tail().then(async () => {
      const before = new Map(this.values);
      try {
        const txn = {
          get: async (key) => this.values.get(key),
          put: async (key, value) => this.values.set(key, structuredClone(value)),
        };
        return await callback(txn);
      } catch (error) {
        this.values = before;
        throw error;
      }
    });
    let tail = run.catch(() => {});
    this.tail = () => tail;
    return run;
  }
}
function setup() {
  const storage = new MemoryStorage();
  const key = Buffer.alloc(32, 7).toString("base64");
  const env = { SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS: JSON.stringify({ "1": key }), SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION: "1", SPOTIFY_CLIENT_ID: "client" };
  return { storage, store: new SpotifyCredentialStore({ storage }, env) };
}
function request(path, body) {
  return new Request("https://credential-store.internal" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
const initialToken = "initial-spotify-refresh-token-123456";
const operation = "A".repeat(43);

test("readiness confirms a valid keyring without requiring an initialized credential", async () => {
  const { storage, store } = setup();
  const ready = await store.fetch(new Request("https://credential-store.internal/ready"));
  assert.equal(ready.status, 200);
  assert.deepEqual(await ready.json(), { status: "ready" });
  assert.equal(await storage.get("credential"), undefined);
  const unconfigured = new SpotifyCredentialStore({ storage: new MemoryStorage() }, {});
  const unavailable = await unconfigured.fetch(new Request("https://credential-store.internal/ready"));
  assert.equal(unavailable.status, 503);
  assert.deepEqual(await unavailable.json(), { error: "credential_store_unavailable" });
});

test("credential initialization encrypts the token and never stores plaintext", async () => {
  const { storage, store } = setup();
  const result = await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  assert.equal(result.status, 201);
  const record = await storage.get("credential");
  assert.equal(record.status, "ready");
  assert.equal(record.version, 1);
  assert.equal(record.credential.algorithm, "A256GCM");
  assert.equal(record.credential.keyVersion, 1);
  assert.notEqual(record.credential.ciphertext, initialToken);
  assert.equal(JSON.stringify(record).includes(initialToken), false);
  assert.equal((await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }))).status, 409);
});

test("refresh rotates encrypted credential only after Spotify identity verification", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push(String(url));
    if (String(url).includes("/api/token")) {
      const body = new URLSearchParams(options.body);
      assert.equal(options.headers.Authorization, undefined);
      assert.equal(body.get("client_id"), "client");
      const suppliedRefreshToken = body.get("refresh_token");
      assert.ok([initialToken, "rotated-refresh-token-abcdef"].includes(suppliedRefreshToken));
      return new Response(JSON.stringify({
        access_token: "short-lived-access-token-" + (suppliedRefreshToken === initialToken ? "one" : "two"),
        refresh_token: "rotated-refresh-token-abcdef",
        token_type: "Bearer",
        expires_in: 3600,
      }), { status: 200 });
    }
    assert.equal(options.headers.Authorization, "Bearer short-lived-access-token-" + (calls.filter((call) => call.includes("/api/token")).length === 1 ? "one" : "two"));
    return new Response(JSON.stringify({ id: "spotifyuser123" }), { status: 200 });
  };
  try {
    const response = await store.fetch(request("/refresh", { operationId: operation }));
    const result = await response.json();
    assert.equal(response.status, 200);
    assert.equal(result.accessToken, "short-lived-access-token-one");
    assert.equal(result.accountId, "spotifyuser123");
    assert.equal(result.credentialVersion, 2);
    const record = await storage.get("credential");
    assert.equal(record.status, "ready");
    assert.equal(record.version, 2);
    assert.equal(JSON.stringify(record).includes("rotated-refresh-token-abcdef"), false);
    assert.equal(JSON.stringify(record).includes("short-lived-access-token-one"), false);
    assert.ok(record.accessToken?.ciphertext);
    assert.deepEqual(calls, ["https://accounts.spotify.com/api/token", "https://api.spotify.com/v1/me"]);
    const replay = await store.fetch(request("/refresh", { operationId: operation }));
    assert.equal(replay.status, 200);
    const replayBody = await replay.json();
    assert.equal(replayBody.accessToken, result.accessToken);
    assert.equal(replayBody.cached, true);
    const expired = await storage.get("credential");
    expired.accessTokenExpiresAt = Date.now() - 1000;
    await storage.put("credential", expired);
    const expiredReplay = await store.fetch(request("/refresh", { operationId: operation }));
    assert.equal(expiredReplay.status, 409);
    assert.equal((await expiredReplay.json()).error, "operation_already_committed");
    const next = await store.fetch(request("/refresh", { operationId: "B".repeat(43) }));
    assert.equal(next.status, 200);
    assert.equal((await next.json()).credentialVersion, 3);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("identity mismatch blocks credential and never commits rotated token", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => String(url).includes("/api/token")
    ? new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef", expires_in: 3600 }), { status: 200 })
    : new Response(JSON.stringify({ id: "different-user" }), { status: 200 });
  try {
    const result = await store.fetch(request("/refresh", { operationId: operation }));
    assert.equal(result.status, 409);
    assert.equal((await result.json()).error, "identity_mismatch");
    const record = await storage.get("credential");
    assert.equal(record.status, "reauthorization_required");
    assert.equal(record.version, 1);
    assert.equal(record.credential.ciphertext.includes("rotated-refresh-token-abcdef"), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("ambiguous provider failure fails closed and forbids retry with old refresh token", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error("network disconnected after request send"); };
  try {
    const result = await store.fetch(request("/refresh", { operationId: operation }));
    assert.equal(result.status, 409);
    assert.equal((await result.json()).error, "operation_outcome_uncertain_reauthorization_required");
    const record = await storage.get("credential");
    assert.equal(record.status, "reauthorization_required");
    assert.equal(record.version, 1);
    const sameOperationRetry = await store.fetch(request("/refresh", { operationId: operation }));
    assert.equal(sameOperationRetry.status, 409);
    assert.equal((await sameOperationRetry.json()).error, "credential_blocked");
    const retry = await store.fetch(request("/refresh", { operationId: "C".repeat(43) }));
    assert.equal(retry.status, 409);
    assert.equal((await retry.json()).error, "credential_blocked");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("concurrent refresh attempts reserve one durable operation only", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  let releaseProvider;
  let providerStarted;
  const started = new Promise((resolve) => { providerStarted = resolve; });
  const providerGate = new Promise((resolve) => { releaseProvider = resolve; });
  globalThis.fetch = async (url) => {
    if (String(url).includes("/api/token")) {
      providerStarted();
      await providerGate;
      return new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef", expires_in: 3600 }), { status: 200 });
    }
    return new Response(JSON.stringify({ id: "spotifyuser123" }), { status: 200 });
  };
  try {
    const first = store.fetch(request("/refresh", { operationId: operation }));
    await started;
    const second = await store.fetch(request("/refresh", { operationId: "D".repeat(43) }));
    assert.equal(second.status, 409);
    assert.equal((await second.json()).error, "credential_busy");
    releaseProvider();
    const firstResponse = await first;
    assert.equal(firstResponse.status, 200);
    const secondRetry = await store.fetch(request("/refresh", { operationId: "D".repeat(43) }));
    assert.equal(secondRetry.status, 200);
    const firstBody = await firstResponse.json();
    const secondBody = await secondRetry.json();
    assert.equal(secondBody.accessToken, firstBody.accessToken);
    assert.equal(secondBody.cached, true);
  } finally {
    releaseProvider();
    globalThis.fetch = originalFetch;
  }
});


test("tampered ciphertext is rejected and blocks the credential", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const record = await storage.get("credential");
  record.credential.ciphertext = record.credential.ciphertext.slice(0, -4) + "AAAA";
  await storage.put("credential", record);
  const originalFetch = globalThis.fetch;
  let providerCalled = false;
  globalThis.fetch = async () => { providerCalled = true; throw new Error("must not call provider"); };
  try {
    const response = await store.fetch(request("/refresh", { operationId: "E".repeat(43) }));
    assert.equal(response.status, 409);
    assert.equal((await response.json()).error, "operation_outcome_uncertain_reauthorization_required");
    assert.equal(providerCalled, false);
    assert.equal((await storage.get("credential")).status, "reauthorization_required");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("malformed requests and missing encryption configuration fail closed", async () => {
  const { store } = setup();
  assert.equal((await store.fetch(new Request("https://x/refresh", { method: "GET" }))).status, 404);
  assert.equal((await store.fetch(request("/refresh", { operationId: "short" }))).status, 400);
  const unconfigured = new SpotifyCredentialStore({ storage: new MemoryStorage() }, {});
  assert.equal((await unconfigured.fetch(request("/initialize", { accountId: "x", refreshToken: initialToken }))).status, 503);
  assert.equal(CREDENTIAL_OPERATION_TTL_MS, 120_000);
});


test("a refresh reservation survives store-instance restart and blocks a second worker", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  let releaseProvider;
  let providerStarted;
  const started = new Promise((resolve) => { providerStarted = resolve; });
  const providerGate = new Promise((resolve) => { releaseProvider = resolve; });
  globalThis.fetch = async (url) => {
    if (String(url).includes("/api/token")) {
      providerStarted();
      await providerGate;
      return new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef", expires_in: 3600 }), { status: 200 });
    }
    return new Response(JSON.stringify({ id: "spotifyuser123" }), { status: 200 });
  };
  try {
    const inFlight = store.fetch(request("/refresh", { operationId: "F".repeat(43) }));
    await started;
    // A new class instance represents a restarted Worker/DO caller sharing
    // the same persistent Durable Object storage.
    const restartedStore = new SpotifyCredentialStore({ storage }, {
      SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS: JSON.stringify({ "1": Buffer.alloc(32, 7).toString("base64") }),
      SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION: "1",
      SPOTIFY_CLIENT_ID: "client",
    });
    const second = await restartedStore.fetch(request("/refresh", { operationId: "G".repeat(43) }));
    assert.equal(second.status, 409);
    assert.equal((await second.json()).error, "credential_busy");
    releaseProvider();
    const firstResponse = await inFlight;
    assert.equal(firstResponse.status, 200);
    const secondRetry = await restartedStore.fetch(request("/refresh", { operationId: "G".repeat(43) }));
    assert.equal(secondRetry.status, 200);
    assert.equal((await secondRetry.json()).cached, true);
  } finally {
    releaseProvider();
    globalThis.fetch = originalFetch;
  }
});

test("a stale operation cannot block or overwrite a newer credential operation", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  await storage.put("credential", {
    ...(await storage.get("credential")),
    status: "refreshing",
    operationId: "H".repeat(43),
    expiresAt: Date.now() + CREDENTIAL_OPERATION_TTL_MS,
  });
  await store.blockOperation("I".repeat(43), "stale_operation");
  const record = await storage.get("credential");
  assert.equal(record.status, "refreshing");
  assert.equal(record.operationId, "H".repeat(43));
  assert.equal(record.blockedReason, undefined);
});


test("credential encryption key version is authenticated as associated data", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const record = await storage.get("credential");
  record.credential.keyVersion = 2;
  await storage.put("credential", record);
  const originalFetch = globalThis.fetch;
  let providerCalled = false;
  globalThis.fetch = async () => { providerCalled = true; throw new Error("provider must not be called"); };
  try {
    const result = await store.fetch(request("/refresh", { operationId: "L".repeat(43) }));
    assert.equal(result.status, 409);
    assert.equal((await result.json()).error, "operation_outcome_uncertain_reauthorization_required");
    assert.equal(providerCalled, false);
    assert.equal((await storage.get("credential")).status, "reauthorization_required");
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("refresh re-encrypts the credential with the active key version", async () => {
  const { storage, store } = setup();
  const keyV1 = Buffer.alloc(32, 7).toString("base64");
  const keyV2 = Buffer.alloc(32, 8).toString("base64");
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  store.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS = JSON.stringify({ "1": keyV1, "2": keyV2 });
  store.env.SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION = "2";
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => String(url).includes("/api/token")
    ? new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef", expires_in: 3600 }), { status: 200 })
    : new Response(JSON.stringify({ id: "spotifyuser123" }), { status: 200 });
  try {
    const first = await store.fetch(request("/refresh", { operationId: "M".repeat(43) }));
    const firstBody = await first.clone().json();
    assert.equal(first.status, 200, "broker refresh failed: " + JSON.stringify(firstBody));
    assert.equal((await storage.get("credential")).credential.keyVersion, 2);
    // Once the successful commit is encrypted under v2, v1 can be removed.
    store.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS = JSON.stringify({ "2": keyV2 });
    store.env.SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION = "2";
    const expired = await storage.get("credential");
    expired.accessTokenExpiresAt = Date.now() - 1000;
    await storage.put("credential", expired);
    const second = await store.fetch(request("/refresh", { operationId: "N".repeat(43) }));
    assert.equal(second.status, 200);
    assert.equal((await storage.get("credential")).credential.keyVersion, 2);
    assert.equal((await storage.get("credential")).version, 3);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("missing historical encryption key fails closed without contacting Spotify", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  store.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS = JSON.stringify({ "2": Buffer.alloc(32, 8).toString("base64") });
  store.env.SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION = "2";
  const originalFetch = globalThis.fetch;
  let providerCalled = false;
  globalThis.fetch = async () => { providerCalled = true; throw new Error("provider must not be called"); };
  try {
    const result = await store.fetch(request("/refresh", { operationId: "O".repeat(43) }));
    assert.equal(result.status, 409);
    assert.equal((await result.json()).error, "operation_outcome_uncertain_reauthorization_required");
    assert.equal(providerCalled, false);
    assert.equal((await storage.get("credential")).status, "reauthorization_required");
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("owner reauthorization restores a blocked credential only for the same verified Spotify account", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => String(url).includes("/api/token")
    ? new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef", expires_in: 3600 }), { status: 200 })
    : new Response(JSON.stringify({ id: "wrong-account" }), { status: 200 });
  try {
    const failed = await store.fetch(request("/refresh", { operationId: "P".repeat(43) }));
    assert.equal(failed.status, 409);
    assert.equal((await storage.get("credential")).status, "reauthorization_required");
    const wrongAccount = await store.fetch(request("/reauthorize", {
      accountId: "differentspotifyuser",
      refreshToken: "new-owner-approved-refresh-token-123",
    }));
    assert.equal(wrongAccount.status, 409);
    assert.equal((await wrongAccount.json()).error, "spotify_account_change_requires_owner_review");
    const restored = await store.fetch(request("/reauthorize", {
      accountId: "spotifyuser123",
      refreshToken: "new-owner-approved-refresh-token-123",
    }));
    assert.equal(restored.status, 200);
    assert.deepEqual(await restored.json(), { reauthorized: true, version: 2 });
    const record = await storage.get("credential");
    assert.equal(record.status, "ready");
    assert.equal(record.accountId, "spotifyuser123");
    assert.equal(record.version, 2);
    assert.equal(record.lastOperationId, "P".repeat(43));
    assert.equal(JSON.stringify(record).includes("new-owner-approved-refresh-token-123"), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("owner reauthorization cannot overwrite a ready or in-progress credential", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const ready = await store.fetch(request("/reauthorize", {
    accountId: "spotifyuser123",
    refreshToken: "new-owner-approved-refresh-token-123",
  }));
  assert.equal(ready.status, 409);
  await storage.put("credential", {
    ...(await storage.get("credential")),
    status: "refreshing",
    operationId: "Q".repeat(43),
  });
  const refreshing = await store.fetch(request("/reauthorize", {
    accountId: "spotifyuser123",
    refreshToken: "new-owner-approved-refresh-token-123",
  }));
  assert.equal(refreshing.status, 409);
  assert.equal((await storage.get("credential")).operationId, "Q".repeat(43));
});


test("owner-consented authorization initializes the central credential store exactly once", async () => {
  const { storage, store } = setup();
  const first = await store.fetch(request("/authorize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  assert.equal(first.status, 201);
  assert.deepEqual(await first.json(), { initialized: true, version: 1 });
  const record = await storage.get("credential");
  assert.equal(record.status, "ready");
  assert.equal(record.accountId, "spotifyuser123");
  assert.equal(JSON.stringify(record).includes(initialToken), false);
  const replay = await store.fetch(request("/authorize", { accountId: "spotifyuser123", refreshToken: "second-owner-approved-refresh-token" }));
  assert.equal(replay.status, 409);
  assert.equal((await storage.get("credential")).version, 1);
});

test("owner-consented authorization recovers only a blocked credential for the same Spotify account", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error("ambiguous provider outcome"); };
  try {
    const failed = await store.fetch(request("/refresh", { operationId: "R".repeat(43) }));
    assert.equal(failed.status, 409);
    assert.equal((await storage.get("credential")).status, "reauthorization_required");
  } finally {
    globalThis.fetch = originalFetch;
  }
  const wrong = await store.fetch(request("/authorize", {
    accountId: "differentspotifyuser",
    refreshToken: "new-owner-approved-refresh-token",
  }));
  assert.equal(wrong.status, 409);
  assert.equal((await wrong.json()).error, "spotify_account_change_requires_owner_review");
  const restored = await store.fetch(request("/authorize", {
    accountId: "spotifyuser123",
    refreshToken: "new-owner-approved-refresh-token",
  }));
  assert.equal(restored.status, 200);
  assert.deepEqual(await restored.json(), { reauthorized: true, version: 2 });
  const record = await storage.get("credential");
  assert.equal(record.status, "ready");
  assert.equal(record.version, 2);
  assert.equal(JSON.stringify(record).includes("new-owner-approved-refresh-token"), false);
});

test("explicit Spotify 429 releases the reservation and preserves the existing credential", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ error: "rate_limited" }), {
    status: 429,
    headers: { "Retry-After": "120" },
  });
  try {
    const result = await store.fetch(request("/refresh", { operationId: "S".repeat(43) }));
    assert.equal(result.status, 429);
    assert.equal(result.headers.get("Retry-After"), "120");
    assert.equal((await result.json()).error, "provider_rate_limited");
    const record = await storage.get("credential");
    assert.equal(record.status, "ready");
    assert.equal(record.version, 1);
    assert.equal(record.credential.version, 1);
    const deferred = await store.fetch(request("/refresh", { operationId: "W".repeat(43) }));
    assert.equal(deferred.status, 429);
    const deferredSeconds = Number(deferred.headers.get("Retry-After"));
    assert.ok(deferredSeconds >= 1 && deferredSeconds <= 120);
    assert.equal((await storage.get("credential")).status, "ready");
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("invalid_grant blocks refresh and requires owner-consented recovery", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ error: "invalid_grant" }), { status: 400 });
  try {
    const result = await store.fetch(request("/refresh", { operationId: "T".repeat(43) }));
    assert.equal(result.status, 409);
    assert.equal((await result.json()).error, "reauthorization_required");
    assert.equal((await storage.get("credential")).status, "reauthorization_required");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("invalid client configuration releases the reservation without invalidating the credential", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({ error: "invalid_client" }), { status: 401 });
  try {
    const result = await store.fetch(request("/refresh", { operationId: "U".repeat(43) }));
    assert.equal(result.status, 503);
    assert.equal((await result.json()).error, "provider_configuration_error");
    const record = await storage.get("credential");
    assert.equal(record.status, "ready");
    assert.equal(record.version, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("owner authorization fails closed when the configured active encryption key is absent", async () => {
  const { storage, store } = setup();
  store.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS = JSON.stringify({
    "2": Buffer.alloc(32, 8).toString("base64"),
  });
  store.env.SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION = "1";
  const result = await store.fetch(request("/authorize", {
    accountId: "spotifyuser123",
    refreshToken: initialToken,
  }));
  assert.equal(result.status, 409);
  assert.equal((await result.json()).error, "Active credential encryption key is unavailable.");
  assert.equal(await storage.get("credential"), undefined);
});


test("invalid Spotify access-token lifetime blocks an uncertain refresh response", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({
    access_token: "short-lived-access-token",
    refresh_token: "rotated-refresh-token-abcdef",
    expires_in: 30,
  }), { status: 200 });
  try {
    const result = await store.fetch(request("/refresh", { operationId: "V".repeat(43) }));
    assert.equal(result.status, 409);
    assert.equal((await result.json()).error, "provider_response_invalid_reauthorization_required");
    assert.equal((await storage.get("credential")).status, "reauthorization_required");
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("failed forced refresh discards the cached access token already rejected by Spotify", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => String(url).includes("/api/token")
    ? new Response(JSON.stringify({ access_token: "cached-access-token", refresh_token: "rotated-refresh-token-abcdef", expires_in: 3600 }), { status: 200 })
    : new Response(JSON.stringify({ id: "spotifyuser123" }), { status: 200 });
  const primed = await store.fetch(request("/refresh", { operationId: "P".repeat(43) }));
  assert.equal(primed.status, 200);
  globalThis.fetch = async (url) => {
    if (String(url).includes("/api/token")) {
      return new Response(JSON.stringify({ error: "invalid_client" }), { status: 401 });
    }
    throw new Error("unexpected identity request");
  };
  try {
    const failed = await store.fetch(request("/refresh", { operationId: "X".repeat(43), forceRefresh: true }));
    assert.equal(failed.status, 503);
    const record = await storage.get("credential");
    assert.equal(record.status, "ready");
    assert.equal(record.accessToken, undefined);
    assert.equal(record.accessTokenExpiresAt, undefined);
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("an expired in-flight refresh reservation blocks for owner recovery instead of retrying an ambiguous token", async () => {
  const { storage, store } = setup();
  await store.fetch(request("/initialize", { accountId: "spotifyuser123", refreshToken: initialToken }));
  const record = await storage.get("credential");
  record.status = "refreshing";
  record.operationId = "R".repeat(43);
  record.startedAt = Date.now() - 121_000;
  record.expiresAt = Date.now() - 1;
  await storage.put("credential", record);
  const originalFetch = globalThis.fetch;
  let providerCalls = 0;
  globalThis.fetch = async () => { providerCalls += 1; throw new Error("must not contact Spotify"); };
  try {
    const result = await store.fetch(request("/refresh", { operationId: "S".repeat(43) }));
    assert.equal(result.status, 409);
    assert.equal((await result.json()).error, "credential_blocked");
    const blocked = await storage.get("credential");
    assert.equal(blocked.status, "reauthorization_required");
    assert.equal(blocked.reason, "refresh_operation_expired");
    assert.equal(blocked.operationId, undefined);
    assert.equal(providerCalls, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
