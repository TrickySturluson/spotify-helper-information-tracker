import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import { SpotifyRefreshLease, verifyActionsOidc, REFRESH_LEASE_TTL_MS } from "../src/refresh-lock.js";

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
  assert.equal(identity.runId, "123456");
});

test("OIDC verifier rejects wrong audience, repository, owner, branch, event, and workflow", async () => {
  const pair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const now = 1_800_000_000;
  const base = validClaims(now);
  const jwk = pair.publicKey.export({ format: "jwk" });
  const fetchImpl = async () => new Response(JSON.stringify({ keys: [{ ...jwk, kty: "RSA", use: "sig", alg: "RS256", kid: "test-key" }] }), { status: 200 });
  for (const change of [
    { aud: "wrong" }, { repository: "attacker/repo" }, { repository_owner_id: "1" },
    { ref: "refs/heads/feature" }, { event_name: "pull_request" },
  ]) {
    const token = makeJwt(pair.privateKey, { ...base, ...change });
    await assert.rejects(verifyActionsOidc(token, { fetchImpl, now, allowedWorkflowRefs: [base.workflow_ref] }));
  }
  const token = makeJwt(pair.privateKey, base);
  await assert.rejects(verifyActionsOidc(token, { fetchImpl, now, allowedWorkflowRefs: [] }));
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
  const storage = {
    get: async (key) => values.get(key),
    put: async (key, value) => values.set(key, value),
    delete: async (key) => values.delete(key),
    setAlarm: async (when) => { alarm = when; },
    transaction: async (fn) => fn({
      get: async (key) => values.get(key),
      put: async (key, value) => values.set(key, value),
      delete: async (key) => values.delete(key),
    }),
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
    lease.fetch(post("/acquire", { leaseId: firstId, generation: 0 })),
    lease.fetch(post("/acquire", { leaseId: secondId, generation: 0 })),
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
  const first = await (await lease.fetch(post("/acquire", { leaseId: firstId, generation: 0 }))).json();
  const stale = await lease.fetch(post("/release", { leaseId: firstId, generation: first.generation + 1 }));
  assert.equal(stale.status, 409);
  const release = await lease.fetch(post("/release", { leaseId: firstId, generation: first.generation }));
  assert.equal(release.status, 200);
  const second = await (await lease.fetch(post("/acquire", { leaseId: secondId, generation: 0 }))).json();
  assert.equal(second.generation, 2);
  assert.equal((await lease.fetch(post("/release", { leaseId: firstId, generation: first.generation }))).status, 409);
  assert.equal((await ctx.storage.get("lease")).leaseId, secondId);
});

test("lease renewal extends expiry and malformed requests fail closed", async () => {
  const ctx = makeStore();
  const lease = new SpotifyRefreshLease(ctx);
  const id = "C".repeat(43);
  const acquired = await (await lease.fetch(post("/acquire", { leaseId: id, generation: 0 }))).json();
  const renewed = await lease.fetch(post("/renew", { leaseId: id, generation: acquired.generation }));
  assert.equal(renewed.status, 200);
  assert.equal((await renewed.json()).ok, true);
  assert.equal(REFRESH_LEASE_TTL_MS, 120_000);
  assert.equal((await lease.fetch(post("/acquire", { leaseId: "short", generation: 0 }))).status, 400);
  assert.equal((await lease.fetch(new Request("https://lease.internal/acquire", { method: "GET" }))).status, 404);
});
