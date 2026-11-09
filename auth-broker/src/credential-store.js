const SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token";
const SPOTIFY_ME_URL = "https://api.spotify.com/v1/me";
const MAX_BODY_BYTES = 16_384;
const OPERATION_TTL_MS = 120_000;
const ACCESS_TOKEN_MIN_REMAINING_MS = 120_000;
const ENCRYPTION_KEY_VERSION = 1;

class CredentialStoreError extends Error {}

function json(body, status = 200, headers = {}) {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store", ...headers } });
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

async function importEncryptionKeyring(env) {
  let encodedKeys = {};
  const serialized = String(env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS || "");
  if (serialized) {
    if (serialized.length > 20_000) throw new CredentialStoreError("Credential encryption is not configured.");
    try { encodedKeys = JSON.parse(serialized); } catch { throw new CredentialStoreError("Credential encryption is not configured."); }
    if (!encodedKeys || typeof encodedKeys !== "object" || Array.isArray(encodedKeys)) {
      throw new CredentialStoreError("Credential encryption is not configured.");
    }
  }
  const versions = Object.keys(encodedKeys);
  if (!versions.length || versions.length > 5 || versions.some((version) => !/^[1-9][0-9]{0,3}$/.test(version))) {
    throw new CredentialStoreError("Credential encryption is not configured.");
  }
  const activeVersion = Number(env.SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION || 1);
  if (!Number.isSafeInteger(activeVersion) || !encodedKeys[String(activeVersion)]) {
    throw new CredentialStoreError("Active credential encryption key is unavailable.");
  }
  const keys = new Map();
  for (const version of versions) keys.set(Number(version), await importEncryptionKey(encodedKeys[version]));
  return { keys, activeVersion, activeKey: keys.get(activeVersion) };
}

function associatedData(version, accountId, keyVersion) {
  return new TextEncoder().encode("SHIT:spotify-refresh-token:v1:" + keyVersion + ":" + version + ":" + accountId);
}

async function encryptRefreshToken(token, key, version, accountId, keyVersion = ENCRYPTION_KEY_VERSION) {
  if (typeof token !== "string" || token.length < 20 || token.length > 8192) {
    throw new CredentialStoreError("Spotify did not return a usable refresh token.");
  }
  const nonce = randomBytes(12);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce, additionalData: associatedData(version, accountId, keyVersion), tagLength: 128 },
    key,
    new TextEncoder().encode(token),
  );
  return { algorithm: "A256GCM", keyVersion, nonce: encodeBase64(nonce), ciphertext: encodeBase64(new Uint8Array(ciphertext)), version };
}

async function decryptRefreshToken(record, key, accountId) {
  try {
    const plaintext = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: decodeBase64(record.nonce),
        additionalData: associatedData(record.version, accountId, record.keyVersion ?? ENCRYPTION_KEY_VERSION),
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

function accessTokenAssociatedData(version, accountId, keyVersion, expiresAt) {
  return new TextEncoder().encode("SHIT:spotify-access-token:v1:" + keyVersion + ":" + version + ":" + accountId + ":" + expiresAt);
}

async function encryptAccessToken(token, key, version, accountId, keyVersion, expiresAt) {
  if (typeof token !== "string" || !token || token.length > 8192 || /[\r\n]/.test(token)) {
    throw new CredentialStoreError("Spotify did not return a usable access token.");
  }
  const nonce = randomBytes(12);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce, additionalData: accessTokenAssociatedData(version, accountId, keyVersion, expiresAt), tagLength: 128 },
    key,
    new TextEncoder().encode(token),
  );
  return { algorithm: "A256GCM", keyVersion, nonce: encodeBase64(nonce), ciphertext: encodeBase64(new Uint8Array(ciphertext)), version, expiresAt };
}

async function decryptAccessToken(record, key, accountId) {
  try {
    const plaintext = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: decodeBase64(record.nonce),
        additionalData: accessTokenAssociatedData(record.version, accountId, record.keyVersion, record.expiresAt),
        tagLength: 128,
      },
      key,
      decodeBase64(record.ciphertext),
    );
    return new TextDecoder().decode(plaintext);
  } catch {
    throw new CredentialStoreError("Cached Spotify access token could not be authenticated.");
  }
}

function retryAfterSeconds(value) {
  const raw = String(value || "").trim();
  if (/^\d{1,8}$/.test(raw)) return Math.min(604800, Number(raw));
  const timestamp = Date.parse(raw);
  if (Number.isFinite(timestamp)) return Math.min(604800, Math.max(0, Math.ceil((timestamp - Date.now()) / 1000)));
  return 86400;
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
    const path = new URL(request.url).pathname;
    if (request.method === "GET" && path === "/ready") {
      try {
        await importEncryptionKeyring(this.env);
        return json({ status: "ready" });
      } catch {
        return json({ error: "credential_store_unavailable" }, 503);
      }
    }
    if (request.method !== "POST") return json({ error: "not_found" }, 404);
    if (path !== "/initialize" && path !== "/refresh" && path !== "/reauthorize" && path !== "/authorize") return json({ error: "not_found" }, 404);
    if (!String(this.env.SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS || "")) {
      return json({ error: "credential_store_unavailable" }, 503);
    }
    let input;
    try { input = await parseSmallJson(request); } catch (error) {
      return json({ error: error instanceof CredentialStoreError ? error.message : "invalid_request" }, 400);
    }
    try {
      const keyring = await importEncryptionKeyring(this.env);
      if (path === "/initialize") return await this.initialize(input, keyring);
      if (path === "/authorize") return await this.authorize(input, keyring);
      if (path === "/reauthorize") return await this.reauthorize(input, keyring);
      return await this.refresh(input, keyring);
    } catch (error) {
      const message = error instanceof CredentialStoreError ? error.message : "Credential operation failed safely.";
      return json({ error: message }, 409);
    }
  }

  // Owner-consented OAuth callback entry point. It initializes a new account
  // or restores an existing blocked credential for the same Spotify identity.
  // A ready/in-progress credential is never overwritten by another OAuth grant.
  async authorize(input, keyring) {
    if (typeof input.accountId !== "string" || !/^[A-Za-z0-9]{1,128}$/.test(input.accountId)) {
      return json({ error: "verified_account_required" }, 400);
    }
    const outcome = await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (!current) {
        const encrypted = await encryptRefreshToken(input.refreshToken, keyring.activeKey, 1, input.accountId, keyring.activeVersion);
        await txn.put("credential", {
          status: "ready", accountId: input.accountId, version: 1,
          credential: encrypted, updatedAt: Date.now(),
        });
        return { initialized: true, version: 1 };
      }
      if (current.status !== "reauthorization_required") return { error: "credential_not_eligible_for_reauthorization" };
      if (current.accountId !== input.accountId) return { error: "spotify_account_change_requires_owner_review" };
      const nextVersion = current.version + 1;
      const encrypted = await encryptRefreshToken(input.refreshToken, keyring.activeKey, nextVersion, current.accountId, keyring.activeVersion);
      await txn.put("credential", {
        status: "ready", accountId: current.accountId, version: nextVersion,
        credential: encrypted, lastOperationId: current.lastOperationId || null, updatedAt: Date.now(),
      });
      return { reauthorized: true, version: nextVersion };
    });
    return outcome.error ? json({ error: outcome.error }, 409) : json(outcome, outcome.initialized ? 201 : 200);
  }

  async initialize(input, keyring) {
    if (typeof input.accountId !== "string" || !/^[A-Za-z0-9]{1,128}$/.test(input.accountId)) {
      return json({ error: "verified_account_required" }, 400);
    }
    const encrypted = await encryptRefreshToken(input.refreshToken, keyring.activeKey, 1, input.accountId, keyring.activeVersion);
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

  async reauthorize(input, keyring) {
    if (typeof input.accountId !== "string" || !/^[A-Za-z0-9]{1,128}$/.test(input.accountId)) {
      return json({ error: "verified_account_required" }, 400);
    }
    const outcome = await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (!current) return { error: "credential_missing" };
      if (current.status !== "reauthorization_required") return { error: "credential_not_eligible_for_reauthorization" };
      if (current.accountId !== input.accountId) return { error: "spotify_account_change_requires_owner_review" };
      const nextVersion = current.version + 1;
      const encrypted = await encryptRefreshToken(
        input.refreshToken, keyring.activeKey, nextVersion, current.accountId, keyring.activeVersion,
      );
      await txn.put("credential", {
        status: "ready",
        accountId: current.accountId,
        version: nextVersion,
        credential: encrypted,
        lastOperationId: current.lastOperationId ?? current.operationId,
        updatedAt: Date.now(),
        reauthorizedAt: Date.now(),
      });
      return { version: nextVersion };
    });
    return outcome.error
      ? json({ error: outcome.error }, 409)
      : json({ reauthorized: true, version: outcome.version });
  }

  async clearCachedAccessToken(record) {
    await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (
        current &&
        current.version === record.version &&
        current.accessToken?.ciphertext === record.accessToken?.ciphertext
      ) {
        const next = { ...current };
        delete next.accessToken;
        delete next.accessTokenExpiresAt;
        await txn.put("credential", next);
      }
    });
  }

  async cachedAccessToken(record, keyring) {
    const remainingMs = Number(record.accessTokenExpiresAt) - Date.now();
    if (!record.accessToken || record.accessToken.version !== record.version || Number(record.accessToken.expiresAt) !== Number(record.accessTokenExpiresAt) || !Number.isFinite(remainingMs) || remainingMs <= ACCESS_TOKEN_MIN_REMAINING_MS) {
      if (record.accessToken) await this.clearCachedAccessToken(record);
      return null;
    }
    const key = keyring.keys.get(record.accessToken.keyVersion);
    if (!key) {
      await this.clearCachedAccessToken(record);
      return null;
    }
    let accessToken;
    try {
      accessToken = await decryptAccessToken(record.accessToken, key, record.accountId);
    } catch {
      await this.clearCachedAccessToken(record);
      return null;
    }
    return json({
      accessToken,
      tokenType: "Bearer",
      expiresIn: Math.floor(remainingMs / 1000),
      accountId: record.accountId,
      credentialVersion: record.version,
      cached: true,
    });
  }


  async refresh(input, keyring) {
    if (typeof input.operationId !== "string" || !/^[A-Za-z0-9_-]{32,128}$/.test(input.operationId)) {
      return json({ error: "invalid_operation" }, 400);
    }
    const now = Date.now();
    const reservation = await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (!current) return { error: "credential_missing" };
      if (current.lastOperationId === input.operationId) {
        if (current.status === "reauthorization_required") return { error: "credential_blocked" };
        if (current.status === "ready" && current.accessToken && current.accessTokenExpiresAt > now + ACCESS_TOKEN_MIN_REMAINING_MS) return { cached: current };
        return { error: "operation_already_committed" };
      }
      if (current.status === "refreshing") {
        if (Number.isFinite(current.expiresAt) && current.expiresAt > now) return { error: "credential_busy" };
        const blocked = { ...current, status: "reauthorization_required", reason: "refresh_operation_expired", blockedAt: now };
        delete blocked.operationId;
        delete blocked.forceRefresh;
        delete blocked.startedAt;
        delete blocked.expiresAt;
        await txn.put("credential", blocked);
        return { error: "credential_blocked" };
      }
      if (current.status !== "ready") return { error: "credential_blocked" };
      if (current.retryAfterAt > now) return { rateLimitedUntil: current.retryAfterAt };
      if (input.forceRefresh !== true && current.accessToken && current.accessTokenExpiresAt > now + ACCESS_TOKEN_MIN_REMAINING_MS) return { cached: current };
      const next = { ...current, status: "refreshing", operationId: input.operationId, forceRefresh: input.forceRefresh === true, startedAt: now, expiresAt: now + OPERATION_TTL_MS };
      await txn.put("credential", next);
      return { record: next };
    });
    if (reservation.error) return json({ error: reservation.error }, 409);
    if (reservation.rateLimitedUntil) {
      const seconds = Math.max(1, Math.ceil((reservation.rateLimitedUntil - Date.now()) / 1000));
      return json({ error: "provider_rate_limited" }, 429, { "Retry-After": String(seconds) });
    }
    if (reservation.cached) {
      const cached = await this.cachedAccessToken(reservation.cached, keyring);
      if (cached) return cached;
      return await this.refresh(input, keyring);
    }

    const previous = reservation.record;
    let refreshToken;
    try {
      const previousKey = keyring.keys.get(previous.credential.keyVersion ?? ENCRYPTION_KEY_VERSION);
      if (!previousKey) throw new CredentialStoreError("Stored credential uses an unavailable encryption key; owner recovery is required.");
      refreshToken = await decryptRefreshToken(previous.credential, previousKey, previous.accountId);
      // PKCE-issued refresh tokens use public-client semantics: client_id in the form body, no Basic auth or client secret.
      const tokenResponse = await fetch(SPOTIFY_TOKEN_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Accept: "application/json",
        },
        body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: refreshToken, client_id: this.env.SPOTIFY_CLIENT_ID }),
        signal: AbortSignal.timeout(12_000),
      });
      if (!tokenResponse.ok) {
        let providerError = null;
        try {
          const providerBody = await tokenResponse.json();
          if (providerBody && typeof providerBody.error === "string") providerError = providerBody.error;
        } catch {
          // Provider response bodies are never returned or logged.
        }
        if (tokenResponse.status === 429) {
          // A definite provider rate limit is not evidence that the refresh
          // token was consumed. Release this reservation and honor Retry-After.
          const retryAfter = tokenResponse.headers.get("Retry-After") || "86400";
          const seconds = retryAfterSeconds(retryAfter);
          await this.releaseOperation(input.operationId, seconds);
          return json({ error: "provider_rate_limited" }, 429, { "Retry-After": String(seconds) });
        }
        if (providerError === "invalid_grant") {
          await this.blockOperation(input.operationId, "invalid_grant");
          return json({ error: "reauthorization_required" }, 409);
        }
        if ([400, 401, 403].includes(tokenResponse.status)) {
          await this.releaseOperation(input.operationId);
          return json({ error: "provider_configuration_error" }, 503);
        }
        // A server error or unreadable provider outcome may have happened
        // after token rotation. Never retry the previous refresh token.
        await this.blockOperation(input.operationId, "provider_outcome_uncertain");
        return json({ error: "provider_outcome_uncertain_reauthorization_required" }, 409);
      }
      const tokenData = await tokenResponse.json();
      if (
        typeof tokenData.access_token !== "string" ||
        !tokenData.access_token ||
        tokenData.access_token.length > 8192 ||
        /[\r\n]/.test(tokenData.access_token) ||
        !Number.isSafeInteger(tokenData.expires_in) ||
        tokenData.expires_in < 120 ||
        tokenData.expires_in > 86_400
      ) {
        await this.blockOperation(input.operationId, "provider_response_invalid");
        return json({ error: "provider_response_invalid_reauthorization_required" }, 409);
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
      const nextCredential = await encryptRefreshToken(nextRefreshToken, keyring.activeKey, nextVersion, previous.accountId, keyring.activeVersion);
      const accessTokenExpiresAt = Date.now() + tokenData.expires_in * 1000;
      const nextAccessToken = await encryptAccessToken(tokenData.access_token, keyring.activeKey, nextVersion, previous.accountId, keyring.activeVersion, accessTokenExpiresAt);
      const committed = await this.ctx.storage.transaction(async (txn) => {
        const current = await txn.get("credential");
        if (!current || current.status !== "refreshing" || current.operationId !== input.operationId || current.version !== previous.version) return false;
        await txn.put("credential", {
          status: "ready",
          accountId: previous.accountId,
          version: nextVersion,
          credential: nextCredential,
          accessToken: nextAccessToken,
          accessTokenExpiresAt,
          lastOperationId: input.operationId,
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

  async releaseOperation(operationId, retryAfterSecondsValue = null) {
    await this.ctx.storage.transaction(async (txn) => {
      const current = await txn.get("credential");
      if (current?.status === "refreshing" && current.operationId === operationId) {
        const next = { ...current, status: "ready", updatedAt: Date.now() };
        if (current.forceRefresh === true) {
          delete next.accessToken;
          delete next.accessTokenExpiresAt;
        }
        delete next.operationId;
        delete next.forceRefresh;
        delete next.startedAt;
        delete next.expiresAt;
        delete next.blockedReason;
        delete next.blockedAt;
        delete next.retryAfterAt;
        if (Number.isSafeInteger(retryAfterSecondsValue) && retryAfterSecondsValue > 0) {
          next.retryAfterAt = Date.now() + retryAfterSecondsValue * 1000;
        }
        await txn.put("credential", next);
      }
    });
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
