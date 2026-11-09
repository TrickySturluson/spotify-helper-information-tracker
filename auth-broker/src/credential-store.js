const SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token";
const SPOTIFY_ME_URL = "https://api.spotify.com/v1/me";
const MAX_BODY_BYTES = 16_384;
const OPERATION_TTL_MS = 120_000;

class CredentialStoreError extends Error {}

function json(body, status = 200) {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store" } });
}

function decodeBase64(value) {
  if (typeof value !== "string" || value.length > 20_000 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
    throw new CredentialStoreError("Credential encryption is not configured.");
  }
  const binary = atob(value);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function encodeBase64(value) {
  let binary = "";
  for (const byte of value) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function randomBytes(size) {
  const bytes = new Uint8Array(size);
  crypto.getRandomValues(bytes);
  return bytes;
}

function encodeBase64Url(value) {
  return encodeBase64(value).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

async function importEncryptionKey(encoded) {
  const raw = decodeBase64(encoded);
  if (raw.length !== 32) throw new CredentialStoreError("Credential encryption is not configured.");
  return crypto.subtle.importKey("raw", raw, { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
}

function associatedData(version, accountId) {
  return new TextEncoder().encode("SHIT:spotify-refresh-token:v1:" + version + ":" + accountId);
}

async function encryptRefreshToken(token, key, version, accountId) {
  if (typeof token !== "string" || token.length < 20 || token.length > 8192) {
    throw new CredentialStoreError("Spotify did not return a usable refresh token.");
  }
  const nonce = randomBytes(12);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce, additionalData: associatedData(version, accountId), tagLength: 128 },
    key,
    new TextEncoder().encode(token),
  );
  return { algorithm: "A256GCM", nonce: encodeBase64(nonce), ciphertext: encodeBase64(new Uint8Array(ciphertext)), version };
}

async function decryptRefreshToken(record, key, accountId) {
  try {
    const plaintext = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: decodeBase64(record.nonce),
        additionalData: associatedData(record.version, accountId),
        tagLength: 128,
      },
      key,
      decodeBase64(record.ciphertext),
    );
    return new TextDecoder().decode(plaintext);
  } catch {
    throw new CredentialStoreError("Stored Spotify credential could not be authenticated; reauthorization is required.");
  }
}

async function parseSmallJson(request) {
  const length = Number(request.headers.get("Content-Length") || 0);
  if (length > MAX_BODY_BYTES) throw new CredentialStoreError("Request is too large.");
  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) throw new CredentialStoreError("Request is too large.");
  try { return JSON.parse(raw); } catch { throw new CredentialStoreError("Invalid request."); }
}

/**
 * Isolated broker-owned credential-store prototype.
 *
 * The Durable Object is the only component allowed to decrypt or refresh the
 * long-lived token. It never returns that token. A refresh attempt is reserved
 * durably before contacting Spotify. If the provider outcome or subsequent
 * commit is ambiguous, the record remains blocked and requires owner
 * reauthorization; it is never automatically retried with the old token.
 */
export class SpotifyCredentialStore {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
  }

  async fetch(request) {
    if (request.method !== "POST") return json({ error: "not_found" }, 404);
    const path = new URL(request.url).pathname;
    if (path !== "/initialize" && path !== "/refresh") return json({ error: "not_found" }, 404);
    if (!String(this.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEY || "")) {
      return json({ error: "credential_store_unavailable" }, 503);
    }
    let input;
    try { input = await parseSmallJson(request); } catch (error) {
      return json({ error: error instanceof CredentialStoreError ? error.message : "invalid_request" }, 400);
    }
    try {
      const key = await importEncryptionKey(this.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEY);
      if (path === "/initialize") return await this.initialize(input, key);
      return await this.refresh(input, key);
    } catch (error) {
      const message = error instanceof CredentialStoreError ? error.message : "Credential operation failed safely.";
      return json({ error: message }, 409);
    }
  }

  async initialize(input, key) {
    if (typeof input.accountId !== "string" || !/^[A-Za-z0-9]{1,128}$/.test(input.accountId)) {
      return json({ error: "verified_account_required" }, 400);
    }
    const encrypted = await encryptRefreshToken(input.refreshToken, key, 1, input.accountId);
    const record = {
      status: "ready",
      accountId: input.accountId,
      version: 1,
      credential: encrypted,
      updatedAt: Date.now(),
    };
    const outcome = await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (current) return false;
      await txn.put("credential", record);
      return true;
    });
    return outcome ? json({ initialized: true, version: 1 }, 201) : json({ error: "credential_already_exists" }, 409);
  }

  async refresh(input, key) {
    if (typeof input.operationId !== "string" || !/^[A-Za-z0-9_-]{32,128}$/.test(input.operationId)) {
      return json({ error: "invalid_operation" }, 400);
    }
    const now = Date.now();
    const reservation = await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (!current) return { error: "credential_missing" };
      if (current.status !== "ready") return { error: "credential_blocked" };
      const next = { ...current, status: "refreshing", operationId: input.operationId, startedAt: now, expiresAt: now + OPERATION_TTL_MS };
      await txn.put("credential", next);
      return { record: next };
    });
    if (reservation.error) return json({ error: reservation.error }, 409);

    const previous = reservation.record;
    let refreshToken;
    try {
      refreshToken = await decryptRefreshToken(previous.credential, key, previous.accountId);
      const tokenResponse = await fetch(SPOTIFY_TOKEN_URL, {
        method: "POST",
        headers: {
          Authorization: "Basic " + btoa(this.env.SPOTIFY_CLIENT_ID + ":" + this.env.SPOTIFY_CLIENT_SECRET),
          "Content-Type": "application/x-www-form-urlencoded",
          Accept: "application/json",
        },
        body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: refreshToken }),
        signal: AbortSignal.timeout(12_000),
      });
      if (!tokenResponse.ok) {
        await this.blockOperation(input.operationId, "provider_rejected");
        return json({ error: tokenResponse.status === 429 ? "provider_rate_limited" : "reauthorization_required" }, 409);
      }
      const tokenData = await tokenResponse.json();
      if (typeof tokenData.access_token !== "string" || !tokenData.access_token) {
        await this.blockOperation(input.operationId, "provider_response_invalid");
        return json({ error: "reauthorization_required" }, 409);
      }
      const identityResponse = await fetch(SPOTIFY_ME_URL, {
        headers: { Authorization: "Bearer " + tokenData.access_token, Accept: "application/json" },
        signal: AbortSignal.timeout(8_000),
      });
      if (!identityResponse.ok) {
        await this.blockOperation(input.operationId, "identity_verification_failed");
        return json({ error: "identity_verification_failed" }, 409);
      }
      const identity = await identityResponse.json();
      if (identity.id !== previous.accountId) {
        await this.blockOperation(input.operationId, "identity_mismatch");
        return json({ error: "identity_mismatch" }, 409);
      }
      const nextRefreshToken = typeof tokenData.refresh_token === "string" && tokenData.refresh_token
        ? tokenData.refresh_token
        : refreshToken;
      const nextVersion = previous.version + 1;
      const nextCredential = await encryptRefreshToken(nextRefreshToken, key, nextVersion, previous.accountId);
      const committed = await this.ctx.storage.transaction(async (txn) => {
        const current = await txn.get("credential");
        if (!current || current.status !== "refreshing" || current.operationId !== input.operationId || current.version !== previous.version) return false;
        await txn.put("credential", {
          status: "ready",
          accountId: previous.accountId,
          version: nextVersion,
          credential: nextCredential,
          updatedAt: Date.now(),
        });
        return true;
      });
      if (!committed) return json({ error: "credential_commit_uncertain_reauthorization_required" }, 409);
      return json({
        accessToken: tokenData.access_token,
        tokenType: tokenData.token_type || "Bearer",
        expiresIn: Number.isFinite(tokenData.expires_in) ? tokenData.expires_in : null,
        accountId: previous.accountId,
        credentialVersion: nextVersion,
      });
    } catch {
      await this.blockOperation(input.operationId, "operation_outcome_uncertain");
      return json({ error: "operation_outcome_uncertain_reauthorization_required" }, 409);
    } finally {
      refreshToken = undefined;
    }
  }

  async blockOperation(operationId, reason) {
    await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (current?.status === "refreshing" && current.operationId === operationId) {
        await txn.put("credential", { ...current, status: "reauthorization_required", blockedReason: reason, blockedAt: Date.now() });
      }
    });
  }
}

export const CREDENTIAL_OPERATION_TTL_MS = OPERATION_TTL_MS;
