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
  const env = { SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS: JSON.stringify({ "1": key }), SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION: "1", SPOTIFY_CLIENT_ID: "client", SPOTIFY_CLIENT_SECRET: "secret" };
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
    assert.deepEqual(calls, ["https://accounts.spotify.com/api/token", "https://api.spotify.com/v1/me"]);
    const replay = await store.fetch(request("/refresh", { operationId: operation }));
    assert.equal(replay.status, 409);
    assert.equal((await replay.json()).error, "operation_already_committed");
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
    ? new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef" }), { status: 200 })
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
      return new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef" }), { status: 200 });
    }
    return new Response(JSON.stringify({ id: "spotifyuser123" }), { status: 200 });
  };
  try {
    const first = store.fetch(request("/refresh", { operationId: operation }));
    await started;
    const second = await store.fetch(request("/refresh", { operationId: "D".repeat(43) }));
    assert.equal(second.status, 409);
    assert.equal((await second.json()).error, "credential_blocked");
    releaseProvider();
    assert.equal((await first).status, 200);
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
      return new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef" }), { status: 200 });
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
      SPOTIFY_CLIENT_SECRET: "secret",
    });
    const second = await restartedStore.fetch(request("/refresh", { operationId: "G".repeat(43) }));
    assert.equal(second.status, 409);
    assert.equal((await second.json()).error, "credential_blocked");
    assert.equal((await storage.get("credential")).operationId, "F".repeat(43));
    releaseProvider();
    assert.equal((await inFlight).status, 200);
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
    ? new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef" }), { status: 200 })
    : new Response(JSON.stringify({ id: "spotifyuser123" }), { status: 200 });
  try {
    const first = await store.fetch(request("/refresh", { operationId: "M".repeat(43) }));
    const firstBody = await first.clone().json();
    assert.equal(first.status, 200, "broker refresh failed: " + JSON.stringify(firstBody));
    assert.equal((await storage.get("credential")).credential.keyVersion, 2);
    // Once the successful commit is encrypted under v2, v1 can be removed.
    store.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS = JSON.stringify({ "2": keyV2 });
    store.env.SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION = "2";
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
    ? new Response(JSON.stringify({ access_token: "short-lived-access-token", refresh_token: "rotated-refresh-token-abcdef" }), { status: 200 })
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
