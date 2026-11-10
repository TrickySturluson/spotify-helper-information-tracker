import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import { SpotifyRefreshLease, verifyActionsOidc, REFRESH_LEASE_TTL_MS } from "../src/refresh-lock.js";
import { handleRequest } from "../src/index.js";

function b64url(value) { return Buffer.from(value).toString("base64url"); }
function makeJwt(privateKey, claims, kid = "test-key") {
  const header = b64url(JSON.stringify({ alg: "RS256", typ: "JWT", kid }));
  const payload = b64url(JSON.stringify(claims));
  const input = header + "." + payload;
  return input + "." + sign("RSA-SHA256", Buffer.from(input), privateKey).toString("base64url");
}
function validClaims(now) {
  return {
    iss: "https://token.actions.githubusercontent.com",
    aud: "shit-spotify-refresh-lock",
    iat: now - 10,
    nbf: now - 10,
    exp: now + 240,
    repository: "TrickySturluson/spotify-helper-information-tracker",
    repository_owner_id: "337022631",
    actor_id: "337022631",
    ref: "refs/heads/main",
    event_name: "workflow_dispatch",
    workflow_ref: "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-auth-health-check.yml@refs/heads/main",
    run_id: "123456",
    run_attempt: "1",
  };
}

test("OIDC verifier accepts a signed, exact repository/workflow identity", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = 1_800_000_000;
  const claims = validClaims(now);
  const token = makeJwt(pair.privateKey, claims);
  const fetchImpl = async () => new Response(JSON.stringify({ keys: [{
    kty: "RSA", use: "sig", alg: "RS256", kid: "test-key",
    n: pair.publicKey.export({ format: "jwk" }).n,
    e: pair.publicKey.export({ format: "jwk" }).e,
  }] }), { status: 200 });
  const identity = await verifyActionsOidc(token, { fetchImpl, now, allowedWorkflowRefs: [claims.workflow_ref] });
  assert.equal(identity.repository, claims.repository);
  assert.equal(identity.actorId, "337022631");
  assert.equal(identity.runId, "123456");
});

test("OIDC verifier rejects wrong audience, repository, owner, branch, event, and workflow", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = 1_800_000_000;
  const base = validClaims(now);
  const jwk = pair.publicKey.export({ format: "jwk" });
  const fetchImpl = async () => new Response(JSON.stringify({ keys: [{ ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key" }] }), { status: 200 });
  for (const change of [
    { aud: "wrong" }, { aud: ["shit-spotify-refresh-lock", "other-relying-party"] },
    { repository: "attacker/repo" }, { repository_owner_id: "1" },
    { ref: "refs/heads/feature" }, { event_name: "pull_request" },
  ]) {
    const token = makeJwt(pair.privateKey, { ...base, ...change });
    await assert.rejects(verifyActionsOidc(token, { fetchImpl, now, allowedWorkflowRefs: [base.workflow_ref] }));
  }
  const token = makeJwt(pair.privateKey, base);
  await assert.rejects(verifyActionsOidc(token, { fetchImpl, now, allowedWorkflowRefs: [] }));
});

test("OIDC verifier allows owner issue events only for the two exact issue-command workflows", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = 1_800_000_000;
  const jwk = pair.publicKey.export({ format: "jwk" });
  const fetchImpl = async () => new Response(JSON.stringify({ keys: [{
    ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key",
  }] }), { status: 200 });
  const playlistRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-playlist-manager.yml@refs/heads/main";
  const migrationRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/great-migration.yml@refs/heads/main";
  const dailyRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-daily-midnight-cycle.yml@refs/heads/main";
  for (const [eventName, workflowRef] of [["issues", playlistRef], ["issues", migrationRef], ["issue_comment", playlistRef]]) {
    const claims = { ...validClaims(now), aud: "shit-spotify-refresh", event_name: eventName, workflow_ref: workflowRef };
    const identity = await verifyActionsOidc(makeJwt(pair.privateKey, claims), {
      fetchImpl, now, allowedWorkflowRefs: [workflowRef], audience: "shit-spotify-refresh",
    });
    assert.equal(identity.workflowRef, workflowRef);
  }
  for (const [eventName, workflowRef] of [["issues", dailyRef], ["issue_comment", migrationRef], ["issue_comment", dailyRef]]) {
    const claims = { ...validClaims(now), aud: "shit-spotify-refresh", event_name: eventName, workflow_ref: workflowRef };
    await assert.rejects(verifyActionsOidc(makeJwt(pair.privateKey, claims), {
      fetchImpl, now, allowedWorkflowRefs: [workflowRef], audience: "shit-spotify-refresh",
    }));
  }
});

test("OIDC verifier restricts manual and issue-triggered runs to the repository owner", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = 1_800_000_000;
  const jwk = pair.publicKey.export({ format: "jwk" });
  const fetchImpl = async () => new Response(JSON.stringify({ keys: [{
    ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key",
  }] }), { status: 200 });
  const playlistRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-playlist-manager.yml@refs/heads/main";
  const authHealthRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-auth-health-check.yml@refs/heads/main";
  for (const eventName of ["workflow_dispatch", "issues", "issue_comment"]) {
    const claims = {
      ...validClaims(now),
      aud: "shit-spotify-refresh",
      event_name: eventName,
      workflow_ref: playlistRef,
      actor_id: "12345",
    };
    await assert.rejects(verifyActionsOidc(makeJwt(pair.privateKey, claims), {
      fetchImpl, now, allowedWorkflowRefs: [playlistRef], audience: "shit-spotify-refresh",
    }));
  }

  // The GitHub App dispatches only the read-only auth-health workflow after
  // owner-consented PKCE authorization, so that single workflow is exempt.
  const appDispatch = {
    ...validClaims(now),
    aud: "shit-spotify-refresh",
    event_name: "workflow_dispatch",
    workflow_ref: authHealthRef,
    actor_id: "987654321",
  };
  const identity = await verifyActionsOidc(makeJwt(pair.privateKey, appDispatch), {
    fetchImpl, now, allowedWorkflowRefs: [authHealthRef], audience: "shit-spotify-refresh",
  });
  assert.equal(identity.workflowRef, authHealthRef);
});

test("OIDC verifier rejects bad signatures, expired tokens and unknown signing keys", async () => {
  const a = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const b = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = 1_800_000_000;
  const claims = validClaims(now);
  const jwk = a.publicKey.export({ format: "jwk" });
  const fetchImpl = async () => new Response(JSON.stringify({ keys: [{ ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key" }] }), { status: 200 });
  await assert.rejects(verifyActionsOidc(makeJwt(b.privateKey, claims), { fetchImpl, now, allowedWorkflowRefs: [claims.workflow_ref] }));
  await assert.rejects(verifyActionsOidc(makeJwt(a.privateKey, { ...claims, exp: now - 1 }), { fetchImpl, now, allowedWorkflowRefs: [claims.workflow_ref] }));
  await assert.rejects(verifyActionsOidc(makeJwt(a.privateKey, claims, "unknown"), { fetchImpl, now, allowedWorkflowRefs: [claims.workflow_ref] }));
});

function makeStore() {
  const values = new Map();
  let alarm = null;
  let transactionTail = Promise.resolve();
  const transactionStore = {
    get: async (key) => values.get(key),
    put: async (key, value) => values.set(key, value),
    delete: async (key) => values.delete(key),
  };
  const storage = {
    get: async (key) => values.get(key),
    put: async (key, value) => values.set(key, value),
    delete: async (key) => values.delete(key),
    setAlarm: async (when) => { alarm = when; },
    transaction: (fn) => {
      const current = transactionTail.then(() => fn(transactionStore));
      transactionTail = current.catch(() => {});
      return current;
    },
  };
  return { storage, values, get alarm() { return alarm; } };
}
function post(path, body) {
  return new Request("https://lease.internal" + path, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
}

test("lease acquisition is exclusive and returns a monotonically increasing fencing generation", async () => {
  const ctx = makeStore();
  const lease = new SpotifyRefreshLease(ctx);
  const firstId = "A".repeat(43);
  const secondId = "B".repeat(43);
  const [first, second] = await Promise.all([
    lease.fetch(post("/acquire", { leaseId: firstId, generation: 0, owner: "wf:123:1" })),
    lease.fetch(post("/acquire", { leaseId: secondId, generation: 0, owner: "wf:456:1" })),
  ]);
  assert.deepEqual([first.status, second.status].sort(), [200, 409]);
  const winner = first.status === 200 ? first : second;
  const loser = first.status === 409 ? first : second;
  const acquired = await winner.json();
  assert.equal((await loser.json()).acquired, false);
  assert.equal(acquired.generation, 1);
  assert.equal(ctx.alarm, acquired.expiresAt);
});

test("stale owners cannot renew or release a successor lease", async () => {
  const ctx = makeStore();
  const lease = new SpotifyRefreshLease(ctx);
  const firstId = "A".repeat(43);
  const secondId = "B".repeat(43);
  const first = await (await lease.fetch(post("/acquire", { leaseId: firstId, generation: 0, owner: "wf:123:1" }))).json();
  const wrongOwner = await lease.fetch(post("/release", { leaseId: firstId, generation: first.generation, owner: "attacker:999:1" }));
  assert.equal(wrongOwner.status, 409);
  const stale = await lease.fetch(post("/release", { leaseId: firstId, generation: first.generation + 1, owner: "wf:123:1" }));
  assert.equal(stale.status, 409);
  const release = await lease.fetch(post("/release", { leaseId: firstId, generation: first.generation, owner: "wf:123:1" }));
  assert.equal(release.status, 200);
  const second = await (await lease.fetch(post("/acquire", { leaseId: secondId, generation: 0, owner: "wf:456:1" }))).json();
  assert.equal(second.generation, 2);
  assert.equal((await lease.fetch(post("/release", { leaseId: firstId, generation: first.generation, owner: "wf:123:1" }))).status, 409);
  assert.equal((await ctx.storage.get("lease")).leaseId, secondId);
});

test("lease renewal extends expiry and malformed requests fail closed", async () => {
  const ctx = makeStore();
  const lease = new SpotifyRefreshLease(ctx);
  const id = "C".repeat(43);
  const acquired = await (await lease.fetch(post("/acquire", { leaseId: id, generation: 0, owner: "wf:789:1" }))).json();
  const renewed = await lease.fetch(post("/renew", { leaseId: id, generation: acquired.generation, owner: "wf:789:1" }));
  assert.equal(renewed.status, 200);
  assert.equal((await renewed.json()).ok, true);
  assert.equal(REFRESH_LEASE_TTL_MS, 120_000);
  assert.equal((await lease.fetch(post("/acquire", { leaseId: "short", generation: 0, owner: "wf:789:1" }))).status, 400);
  assert.equal((await lease.fetch(new Request("https://lease.internal/acquire", { method: "GET" }))).status, 404);
});


test("OIDC verifier supports a distinct broker-refresh audience", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = 1_800_000_000;
  const claims = { ...validClaims(now), aud: "shit-spotify-refresh" };
  const jwk = pair.publicKey.export({ format: "jwk" });
  const fetchImpl = async () => new Response(JSON.stringify({ keys: [{ ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key" }] }), { status: 200 });
  await verifyActionsOidc(makeJwt(pair.privateKey, claims), {
    fetchImpl, now, allowedWorkflowRefs: [claims.workflow_ref], audience: "shit-spotify-refresh",
  });
  await assert.rejects(verifyActionsOidc(makeJwt(pair.privateKey, claims), {
    fetchImpl, now, allowedWorkflowRefs: [claims.workflow_ref],
  }));
});

test("broker refresh route authenticates exact OIDC workflow and forwards only operation ID", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = Math.floor(Date.now() / 1000);
  const claims = { ...validClaims(now), aud: "shit-spotify-refresh" };
  const token = makeJwt(pair.privateKey, claims);
  const jwk = pair.publicKey.export({ format: "jwk" });
  const originalFetch = globalThis.fetch;
  let calls = 0;
  let forwarded;
  globalThis.fetch = async () => new Response(JSON.stringify({ keys: [{
    ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key",
  }] }), { status: 200 });
  const env = {
    BROKER_BASE_URL: "https://broker.example",
    SPOTIFY_OAUTH_ENABLED: "true",
    AUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    BROKER_REFRESH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    SPOTIFY_REFRESH_WORKFLOW_REFS: claims.workflow_ref,
    SPOTIFY_CREDENTIAL_STORE: {
      idFromName: (name) => { assert.equal(name, "spotify-primary"); return "credential-id"; },
      get: (id) => {
        assert.equal(id, "credential-id");
        return { fetch: async (url, init) => {
          calls += 1;
          assert.equal(url, "https://spotify-credential.internal/refresh");
          forwarded = JSON.parse(init.body);
          return Response.json({ accessToken: "short-lived-access-token", expiresIn: 3600 });
        } };
      },
    },
  };
  try {
    const request = new Request("https://broker.example/internal/spotify/refresh", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify({ operationId: "J".repeat(43), accountId: "attacker-controlled", owner: "attacker", forceRefresh: true }),
    });
    const result = await handleRequest(request, env);
    assert.equal(result.status, 200);
    assert.deepEqual(await result.json(), { accessToken: "short-lived-access-token", expiresIn: 3600 });
    assert.deepEqual(forwarded, { operationId: "J".repeat(43), forceRefresh: true });
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("broker refresh route rejects wrong-audience OIDC before touching credential storage", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = Math.floor(Date.now() / 1000);
  const claims = validClaims(now); // Lease audience is not valid for credential refresh.
  const token = makeJwt(pair.privateKey, claims);
  const jwk = pair.publicKey.export({ format: "jwk" });
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => new Response(JSON.stringify({ keys: [{
    ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key",
  }] }), { status: 200 });
  const env = {
    BROKER_BASE_URL: "https://broker.example",
    SPOTIFY_OAUTH_ENABLED: "true",
    AUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    BROKER_REFRESH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    SPOTIFY_REFRESH_WORKFLOW_REFS: claims.workflow_ref,
    SPOTIFY_CREDENTIAL_STORE: {
      idFromName: () => "credential-id",
      get: () => ({ fetch: async () => { calls += 1; return Response.json({}); } }),
    },
  };
  try {
    const result = await handleRequest(new Request("https://broker.example/internal/spotify/refresh", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify({ operationId: "K".repeat(43) }),
    }), env);
    assert.equal(result.status, 401);
    assert.equal(calls, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});


test("forced refresh requires the owner actor even for the auth-health workflow", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = Math.floor(Date.now() / 1000);
  const workflowRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-auth-health-check.yml@refs/heads/main";
  const claims = { ...validClaims(now), aud: "shit-spotify-refresh", workflow_ref: workflowRef, actor_id: "987654321" };
  const token = makeJwt(pair.privateKey, claims);
  const jwk = pair.publicKey.export({ format: "jwk" });
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => new Response(JSON.stringify({ keys: [{
    ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key",
  }] }), { status: 200 });
  const env = {
    BROKER_BASE_URL: "https://broker.example",
    SPOTIFY_OAUTH_ENABLED: "true",
    AUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    BROKER_REFRESH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    SPOTIFY_REFRESH_WORKFLOW_REFS: workflowRef,
    SPOTIFY_CREDENTIAL_STORE: {
      idFromName: () => "credential-id",
      get: () => ({ fetch: async () => { calls += 1; return Response.json({}); } }),
    },
  };
  try {
    const result = await handleRequest(new Request("https://broker.example/internal/spotify/refresh", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify({ operationId: "M".repeat(43), forceRefresh: true }),
    }), env);
    assert.equal(result.status, 403);
    assert.deepEqual(await result.json(), { error: "force_refresh_not_allowed" });
    assert.equal(calls, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("forced access-token refresh is rejected for every workflow except the exact auth-health workflow", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = Math.floor(Date.now() / 1000);
  const workflowRef = "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-daily-midnight-cycle.yml@refs/heads/main";
  const claims = { ...validClaims(now), aud: "shit-spotify-refresh", workflow_ref: workflowRef };
  const token = makeJwt(pair.privateKey, claims);
  const jwk = pair.publicKey.export({ format: "jwk" });
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => new Response(JSON.stringify({ keys: [{
    ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key",
  }] }), { status: 200 });
  const env = {
    BROKER_BASE_URL: "https://broker.example",
    SPOTIFY_OAUTH_ENABLED: "true",
    AUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    BROKER_REFRESH_RATE_LIMITER: { limit: async () => ({ success: true }) },
    SPOTIFY_REFRESH_WORKFLOW_REFS: workflowRef,
    SPOTIFY_CREDENTIAL_STORE: {
      idFromName: () => "credential-id",
      get: () => ({ fetch: async () => { calls += 1; return Response.json({}); } }),
    },
  };
  try {
    const result = await handleRequest(new Request("https://broker.example/internal/spotify/refresh", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify({ operationId: "L".repeat(43), forceRefresh: true }),
    }), env);
    assert.equal(result.status, 403);
    assert.equal(calls, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
