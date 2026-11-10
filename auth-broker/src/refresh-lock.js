const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "shit-spotify-refresh-lock";
const REPOSITORY = "TrickySturluson/spotify-helper-information-tracker";
const OWNER_ID = "337022631";
const MAX_TOKEN_AGE = 300;
const LEASE_TTL_MS = 120_000;

function decodePart(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const binary = atob(normalized + "=".repeat((4 - normalized.length % 4) % 4));
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function parsePart(value) {
  return JSON.parse(new TextDecoder().decode(decodePart(value)));
}

/**
 * Verify a GitHub Actions OIDC JWT. Never accept decoded-but-unverified claims.
 * allowedWorkflowRefs must be exact, repository-controlled workflow_ref values.
 */
export async function verifyActionsOidc(token, {
  fetchImpl = fetch,
  now = Math.floor(Date.now() / 1000),
  allowedWorkflowRefs = [],
  audience = AUDIENCE,
} = {}) {
  if (typeof token !== "string" || token.length > 16_384) throw new Error("Untrusted workload identity.");
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("Untrusted workload identity.");
  let header;
  let claims;
  try { header = parsePart(parts[0]); claims = parsePart(parts[1]); } catch { throw new Error("Untrusted workload identity."); }
  if (header.alg !== "RS256" || header.typ !== "JWT" || typeof header.kid !== "string" || Object.hasOwn(header, "jku") || Object.hasOwn(header, "x5u")) throw new Error("Untrusted workload identity.");
  let jwksResponse;
  try { jwksResponse = await fetchImpl(ISSUER + "/.well-known/jwks", { headers: { Accept: "application/json" }, signal: AbortSignal.timeout(5000) }); } catch { throw new Error("Workload identity verification unavailable."); }
  if (!jwksResponse.ok) throw new Error("Workload identity verification unavailable.");
  const jwks = await jwksResponse.json();
  const jwk = Array.isArray(jwks.keys) ? jwks.keys.find((key) => key.kid === header.kid && key.kty === "RSA" && key.use === "sig" && key.alg === "RS256") : null;
  if (!jwk) throw new Error("Untrusted workload identity.");
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const signatureValid = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5",
    key,
    decodePart(parts[2]),
    new TextEncoder().encode(parts[0] + "." + parts[1]),
  );
  if (!signatureValid) throw new Error("Untrusted workload identity.");
  const issuer = claims.iss;
  // GitHub issues a single audience for this workflow token. Reject audience
  // arrays rather than accepting a token minted for multiple relying parties.
  if (issuer !== ISSUER || claims.aud !== audience) throw new Error("Untrusted workload identity.");
  if (!Number.isFinite(claims.exp) || claims.exp <= now || !Number.isFinite(claims.nbf) || claims.nbf > now + 30) throw new Error("Untrusted workload identity.");
  if (!Number.isFinite(claims.iat) || claims.iat > now + 30 || now - claims.iat > MAX_TOKEN_AGE) throw new Error("Untrusted workload identity.");
  if (claims.repository !== REPOSITORY || String(claims.repository_owner_id) !== OWNER_ID) throw new Error("Untrusted workload identity.");
  if (typeof claims.workflow_ref !== "string" || !allowedWorkflowRefs.includes(claims.workflow_ref)) throw new Error("Unapproved workflow identity.");
  const playlistControlRef = REPOSITORY + "/.github/workflows/spotify-playlist-manager.yml@refs/heads/main";
  const greatMigrationRef = REPOSITORY + "/.github/workflows/great-migration.yml@refs/heads/main";
  const authHealthRef = REPOSITORY + "/.github/workflows/spotify-auth-health-check.yml@refs/heads/main";
  // OIDC actor_id is the personal account that initiated the workflow run.
  // Require the repository owner for manual and issue-driven execution. The
  // auth-health workflow is the sole exception: the broker's GitHub App
  // dispatches this read-only diagnostic after successful owner PKCE auth.
  const ownerActor = String(claims.actor_id || "") === OWNER_ID;
  const ownerWorkflowDispatch = claims.event_name === "workflow_dispatch" &&
    (ownerActor || claims.workflow_ref === authHealthRef);
  const standardEvent = ["push", "schedule"].includes(claims.event_name) || ownerWorkflowDispatch;
  const ownerIssueEvent = claims.event_name === "issues" && ownerActor &&
    [playlistControlRef, greatMigrationRef].includes(claims.workflow_ref);
  const ownerCommentEvent = claims.event_name === "issue_comment" && ownerActor &&
    claims.workflow_ref === playlistControlRef;
  if (claims.ref !== "refs/heads/main" || !(standardEvent || ownerIssueEvent || ownerCommentEvent)) {
    throw new Error("Untrusted workload identity.");
  }
  if (typeof claims.run_id !== "string" || !/^\d+$/.test(claims.run_id) || typeof claims.run_attempt !== "string" || !/^\d+$/.test(claims.run_attempt)) throw new Error("Untrusted workload identity.");
  return Object.freeze({
    repository: claims.repository,
    workflowRef: claims.workflow_ref,
    actorId: String(claims.actor_id || ""),
    runId: claims.run_id,
    runAttempt: claims.run_attempt,
  });
}

export class SpotifyRefreshLease {
  constructor(ctx) { this.ctx = ctx; }

  async fetch(request) {
    if (request.method !== "POST") return new Response("Not found", { status: 404 });
    const url = new URL(request.url);
    const contentType = request.headers.get("Content-Type") || "";
    if (!contentType.toLowerCase().startsWith("application/json")) return Response.json({ error: "invalid_request" }, { status: 415 });
    const declaredLength = Number(request.headers.get("Content-Length") || 0);
    if (declaredLength > 2048) return Response.json({ error: "invalid_request" }, { status: 413 });
    let body;
    try { body = await request.json(); } catch { return Response.json({ error: "invalid_request" }, { status: 400 }); }
    if (!body || typeof body.leaseId !== "string" || !/^[A-Za-z0-9_-]{32,128}$/.test(body.leaseId) || !Number.isSafeInteger(body.generation)) {
      return Response.json({ error: "invalid_request" }, { status: 400 });
    }
    const now = Date.now();
    const result = await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("lease");
      let generation = await txn.get("generation") || 0;
      if (typeof body.owner !== "string" || body.owner.length > 512) return { status: 400, body: { error: "invalid_request" } };
      if (url.pathname === "/acquire") {
        if (current && current.expiresAt > now) return { status: 409, body: { acquired: false, retryAfterSeconds: Math.max(1, Math.ceil((current.expiresAt - now) / 1000)) } };
        generation += 1;
        await txn.put("generation", generation);
        await txn.put("lease", { leaseId: body.leaseId, owner: body.owner, generation, expiresAt: now + LEASE_TTL_MS });
        return { status: 200, body: { acquired: true, generation, expiresAt: now + LEASE_TTL_MS } };
      }
      if (!current || current.expiresAt <= now || current.leaseId !== body.leaseId || current.owner !== body.owner || current.generation !== body.generation) {
        return { status: 409, body: { ok: false, lost: true } };
      }
      if (url.pathname === "/renew") {
        const expiresAt = now + LEASE_TTL_MS;
        await txn.put("lease", { ...current, expiresAt });
        return { status: 200, body: { ok: true, expiresAt } };
      }
      if (url.pathname === "/release") {
        await txn.delete("lease");
        return { status: 200, body: { ok: true } };
      }
      return { status: 404, body: { error: "not_found" } };
    });
    if (result.status === 200 && result.body.expiresAt) await this.ctx.storage.setAlarm(result.body.expiresAt);
    return Response.json(result.body, { status: result.status, headers: { "Cache-Control": "no-store" } });
  }

  async alarm() {
    const now = Date.now();
    await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("lease");
      if (current && current.expiresAt <= now) await txn.delete("lease");
    });
    const current = await this.ctx.storage.get("lease");
    if (current) await this.ctx.storage.setAlarm(current.expiresAt);
  }
}

export const REFRESH_LEASE_TTL_MS = LEASE_TTL_MS;
