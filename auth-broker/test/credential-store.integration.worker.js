import { env } from "cloudflare:workers";
import { runInDurableObject } from "cloudflare:test";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { network } from "./network.js";

const TOKEN_URL = "https://accounts.spotify.com/api/token";
const ME_URL = "https://api.spotify.com/v1/me";
const ACCOUNT_ID = "spotifytest123";
const INITIAL_REFRESH = "initial-refresh-token-for-integration-tests";
const ROTATED_REFRESH = "rotated-refresh-token-for-integration-tests";

function newStore(label) {
  const id = env.SPOTIFY_CREDENTIAL_STORE.idFromName(label + "-" + crypto.randomUUID());
  return { id, stub: env.SPOTIFY_CREDENTIAL_STORE.get(id) };
}

function post(stub, path, body) {
  return stub.fetch("https://credential-store.internal" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function initialize(stub) {
  return post(stub, "/initialize", { accountId: ACCOUNT_ID, refreshToken: INITIAL_REFRESH });
}

async function storedRecord(stub) {
  let record;
  await runInDurableObject(stub, async (_instance, state) => {
    record = await state.storage.get("credential");
  });
  return record;
}

function successfulSpotifyHandlers({ onTokenRequest } = {}) {
  return [
    http.post(TOKEN_URL, async ({ request }) => {
      const form = new URLSearchParams(await request.text());
      expect(form.get("grant_type")).toBe("refresh_token");
      expect(form.get("refresh_token")).toBe(INITIAL_REFRESH);
      if (onTokenRequest) await onTokenRequest();
      return HttpResponse.json({
        access_token: "short-lived-integration-access-token",
        refresh_token: ROTATED_REFRESH,
        token_type: "Bearer",
        expires_in: 3600,
      });
    }),
    http.get(ME_URL, () => HttpResponse.json({ id: ACCOUNT_ID })),
  ];
}

describe("SpotifyCredentialStore on the Cloudflare Workers SQLite runtime", () => {
  it("persists only ciphertext and commits rotation after /v1/me identity verification", async () => {
    const { id, stub } = newStore("success");
    const initialized = await initialize(stub);
    expect(initialized.status).toBe(201);

    const initialRecord = await storedRecord(stub);
    expect(initialRecord.status).toBe("ready");
    expect(initialRecord.credential.algorithm).toBe("A256GCM");
    expect(initialRecord.credential.keyVersion).toBe(1);
    expect(JSON.stringify(initialRecord)).not.toContain(INITIAL_REFRESH);

    network.use(...successfulSpotifyHandlers());
    const refreshed = await post(stub, "/refresh", { operationId: "A".repeat(43) });
    expect(refreshed.status).toBe(200);
    const result = await refreshed.json();
    expect(result.accessToken).toBe("short-lived-integration-access-token");
    expect(result.accountId).toBe(ACCOUNT_ID);
    expect(result.credentialVersion).toBe(2);

    const reacquiredStub = env.SPOTIFY_CREDENTIAL_STORE.get(id);
    const finalRecord = await storedRecord(reacquiredStub);
    expect(finalRecord.status).toBe("ready");
    expect(finalRecord.version).toBe(2);
    expect(finalRecord.credential.keyVersion).toBe(1);
    expect(JSON.stringify(finalRecord)).not.toContain(ROTATED_REFRESH);
    expect(reacquiredStub).toBeDefined();
  });

  it("uses the SQLite transaction to reject a concurrent refresh reservation", async () => {
    const { stub } = newStore("concurrent");
    expect((await initialize(stub)).status).toBe(201);

    let providerStarted;
    const started = new Promise((resolve) => { providerStarted = resolve; });
    let releaseProvider;
    const providerGate = new Promise((resolve) => { releaseProvider = resolve; });
    network.use(...successfulSpotifyHandlers({ onTokenRequest: async () => {
      providerStarted();
      await providerGate;
    } }));

    const first = post(stub, "/refresh", { operationId: "B".repeat(43) });
    await started;
    const second = await post(stub, "/refresh", { operationId: "C".repeat(43) });
    expect(second.status).toBe(409);
    expect((await second.json()).error).toBe("credential_busy");
    releaseProvider();
    expect((await first).status).toBe(200);
  });

  it("keeps an ambiguous refresh blocked across a newly acquired Durable Object stub", async () => {
    const { id, stub } = newStore("ambiguous");
    expect((await initialize(stub)).status).toBe(201);
    network.use(http.post(TOKEN_URL, () => HttpResponse.error()));

    const failed = await post(stub, "/refresh", { operationId: "D".repeat(43) });
    expect(failed.status).toBe(409);
    expect((await failed.json()).error).toBe("operation_outcome_uncertain_reauthorization_required");
    expect((await storedRecord(stub)).status).toBe("reauthorization_required");

    const sameStub = env.SPOTIFY_CREDENTIAL_STORE.get(id);
    const blocked = await post(sameStub, "/refresh", { operationId: "E".repeat(43) });
    expect(blocked.status).toBe(409);
    expect((await blocked.json()).error).toBe("credential_blocked");
  });

  it("restores a blocked credential only after same-account reauthorization", async () => {
    const { stub } = newStore("reauthorize");
    expect((await initialize(stub)).status).toBe(201);
    network.use(
      http.post(TOKEN_URL, () => HttpResponse.json({
        access_token: "short-lived-integration-access-token",
        refresh_token: ROTATED_REFRESH,
        expires_in: 3600,
      })),
      http.get(ME_URL, () => HttpResponse.json({ id: "different-account" })),
    );
    const failed = await post(stub, "/refresh", { operationId: "F".repeat(43) });
    expect(failed.status).toBe(409);
    expect((await storedRecord(stub)).status).toBe("reauthorization_required");

    const mismatch = await post(stub, "/reauthorize", {
      accountId: "differentaccount",
      refreshToken: "owner-approved-new-refresh-token-for-same-account",
    });
    expect(mismatch.status).toBe(409);

    const restored = await post(stub, "/reauthorize", {
      accountId: ACCOUNT_ID,
      refreshToken: "owner-approved-new-refresh-token-for-same-account",
    });
    expect(restored.status).toBe(200);
    expect(await restored.json()).toEqual({ reauthorized: true, version: 2 });
    const record = await storedRecord(stub);
    expect(record.status).toBe("ready");
    expect(record.version).toBe(2);
    expect(record.lastOperationId).toBe("F".repeat(43));
  });
});


// FILE OVERVIEW
// Purpose: Exercise SpotifyCredentialStore against real SQLite Durable Objects in the Workers runtime.
// Coverage: Ciphertext persistence, verified token rotation, transactional concurrency, blocked state, and reauthorization.
// Network: MSW intercepts Spotify token and identity endpoints; tests make no external Spotify requests.
// Related: auth-broker/src/credential-store.js, auth-broker/vitest.config.js.
