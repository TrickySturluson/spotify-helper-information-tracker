import sodium from "libsodium-wrappers";

const OWNER = "TrickySturluson";
const REPOSITORY = "spotify-helper-information-tracker";
const SECRET_NAME = "SPOTIFY_REFRESH_TOKEN";
const AUTH_WORKFLOW = "spotify-auth-health-check.yml";
const REQUIRED_SCOPES = [
  "user-read-private",
  "user-library-read",
  "playlist-read-private",
  "playlist-read-collaborative",
  "playlist-modify-private",
  "playlist-modify-public",
];
const SESSION_TTL = 900;
const OAUTH_TTL = 300;

class BrokerError extends Error {}

function base64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function decodeBase64(value) {
  const binary = atob(value);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function randomValue(bytes = 32) {
  const value = new Uint8Array(bytes);
  crypto.getRandomValues(value);
  return base64Url(value);
}

async function sha256(value) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
}

export async function pkceChallenge(verifier) {
  return base64Url(await sha256(verifier));
}

export function parseCookies(header = "") {
  const result = {};
  for (const part of header.split(";")) {
    const index = part.indexOf("=");
    if (index < 1) continue;
    const key = part.slice(0, index).trim();
    const value = part.slice(index + 1).trim();
    if (key) result[key] = value;
  }
  return result;
}

export function isAuthorizedOwner(login, expected = OWNER) {
  return typeof login === "string" && login.toLowerCase() === expected.toLowerCase();
}

export function hasRequiredScopes(scope) {
  if (typeof scope !== "string") return false;
  const granted = new Set(scope.split(/\s+/).filter(Boolean));
  return REQUIRED_SCOPES.every((item) => granted.has(item));
}

function cookie(name, value, maxAge) {
  return `${name}=${value}; Path=/; Max-Age=${maxAge}; Secure; HttpOnly; SameSite=Lax`;
}

function clearCookie(name) {
  return cookie(name, "", 0);
}

function response(body, status = 200, headers = {}) {
  const output = new Headers(headers);
  output.set("X-Content-Type-Options", "nosniff");
  output.set("Referrer-Policy", "no-referrer");
  output.set("X-Frame-Options", "DENY");
  output.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  output.set("Cache-Control", "no-store");
  output.set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
  output.set("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
  return new Response(body, { status, headers: output });
}

function page(title, message, link = null) {
  const safeTitle = escapeHtml(title);
  const safeMessage = escapeHtml(message);
  const linkHtml = link
    ? `<p><a href="${escapeHtml(link.href)}">${escapeHtml(link.label)}</a></p>`
    : "";
  return response(
    `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${safeTitle}</title><body><main><h1>${safeTitle}</h1><p>${safeMessage}</p>${linkHtml}</main></body></html>`,
    200,
    { "Content-Type": "text/html; charset=utf-8" },
  );
}

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function redirect(url, headers = {}) {
  return response(null, 302, { Location: url, ...headers });
}

async function rateLimit(request, env, route) {
  if (!env.AUTH_RATE_LIMITER) throw new BrokerError("Rate limiter is not configured.");
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const result = await env.AUTH_RATE_LIMITER.limit({ key: `${route}:${ip}` });
  if (!result.success) throw new BrokerError("Too many attempts.");
}

async function getSession(request, env) {
  const id = parseCookies(request.headers.get("Cookie"))["__Host-shit_session"];
  if (!id || !/^[A-Za-z0-9_-]{40,}$/.test(id)) return null;
  const value = await env.OAUTH_KV.get(`session:${id}`);
  if (!value) return null;
  const session = JSON.parse(value);
  if (!isAuthorizedOwner(session.login)) return null;
  return { id, login: session.login };
}

function requireEnv(env, names) {
  for (const name of names) {
    if (!String(env[name] || "").trim()) throw new BrokerError("Authorization service is not configured.");
  }
}

async function exchangeForm(url, fields, headers = {}) {
  const result = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json", ...headers },
    body: new URLSearchParams(fields),
  });
  if (!result.ok) throw new BrokerError("An authorization provider rejected the request.");
  const data = await result.json();
  if (data.error) throw new BrokerError("An authorization provider rejected the request.");
  return data;
}

async function githubApi(path, token, method = "GET", body = undefined) {
  const result = await fetch(`https://api.github.com${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "SHIT-Mobile-Authorization-Broker",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!result.ok) throw new BrokerError("GitHub could not complete the secure credential update.");
  return result.status === 204 ? null : result.json();
}

function derLength(length) {
  if (length < 128) return Uint8Array.of(length);
  const bytes = [];
  let value = length;
  while (value > 0) {
    bytes.unshift(value & 255);
    value >>= 8;
  }
  return Uint8Array.of(0x80 | bytes.length, ...bytes);
}

function der(tag, content) {
  const length = derLength(content.length);
  const result = new Uint8Array(1 + length.length + content.length);
  result[0] = tag;
  result.set(length, 1);
  result.set(content, 1 + length.length);
  return result;
}

function concat(...parts) {
  const result = new Uint8Array(parts.reduce((sum, part) => sum + part.length, 0));
  let offset = 0;
  for (const part of parts) {
    result.set(part, offset);
    offset += part.length;
  }
  return result;
}

function pkcs8PrivateKey(pem) {
  const isPkcs1 = pem.includes("BEGIN RSA PRIVATE KEY");
  const raw = pem.replace(/-----BEGIN [^-]+-----/g, "").replace(/-----END [^-]+-----/g, "").replace(/\s/g, "");
  const pkcs1 = decodeBase64(raw);
  if (!isPkcs1) return pkcs1;
  // PKCS#8 wrapper for rsaEncryption OID 1.2.840.113549.1.1.1.
  const algorithm = Uint8Array.from([0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00]);
  return der(0x30, concat(Uint8Array.of(0x02, 0x01, 0x00), algorithm, der(0x04, pkcs1)));
}

async function githubAppJwt(env) {
  const pem = String(env.GITHUB_APP_PRIVATE_KEY || "");
  const key = await crypto.subtle.importKey(
    "pkcs8",
    pkcs8PrivateKey(pem),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const now = Math.floor(Date.now() / 1000);
  const header = base64Url(new TextEncoder().encode(JSON.stringify({ alg: "RS256", typ: "JWT" })));
  const payload = base64Url(new TextEncoder().encode(JSON.stringify({
    iat: now - 60,
    exp: now + 540,
    iss: String(env.GITHUB_APP_ID),
  })));
  const signingInput = `${header}.${payload}`;
  const signature = new Uint8Array(await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    key,
    new TextEncoder().encode(signingInput),
  ));
  return `${signingInput}.${base64Url(signature)}`;
}

async function installationToken(env) {
  const jwt = await githubAppJwt(env);
  const installation = await githubApi(`/repos/${OWNER}/${REPOSITORY}/installation`, jwt);
  if (!installation?.id) throw new BrokerError("GitHub App is not installed on the SHIT repository.");
  const token = await githubApi(
    `/app/installations/${installation.id}/access_tokens`,
    jwt,
    "POST",
    {
      repositories: [REPOSITORY],
      permissions: { actions: "write", secrets: "write" },
    },
  );
  if (!token?.token) throw new BrokerError("GitHub App installation token was not issued.");
  return token.token;
}

async function assertNoConcurrentSpotifyJobs(token) {
  const runs = await githubApi(
    `/repos/${OWNER}/${REPOSITORY}/actions/runs?status=in_progress&per_page=100`,
    token,
  );
  if ((runs?.total_count || 0) > 100) {
    throw new BrokerError("Too many active GitHub Actions runs to safely authorize. Wait and retry.");
  }
  const active = (runs?.workflow_runs || []).filter((run) => {
    const path = String(run.path || "");
    const spotifyWorkflow = path.startsWith(".github/workflows/") &&
      (path.includes("spotify") || /great-migration|update\.yml|enrich-music-metadata|acoustic-metadata-enrichment|backfill-music-durations/i.test(path));
    const brokerWorkflow = /mobile-auth-broker-tests|deploy-mobile-auth-broker/i.test(path);
    return spotifyWorkflow && !brokerWorkflow;
  });
  if (active.length) {
    throw new BrokerError("A Spotify-related GitHub workflow is already running. Wait for it to finish before reauthorizing.");
  }
}

async function saveRefreshToken(env, refreshToken) {
  if (typeof refreshToken !== "string" || refreshToken.length < 20) {
    throw new BrokerError("Spotify did not return a usable refresh token.");
  }
  await sodium.ready;
  const token = await installationToken(env);
  await assertNoConcurrentSpotifyJobs(token);
  const path = `/repos/${OWNER}/${REPOSITORY}`;
  const publicKey = await githubApi(`${path}/actions/secrets/public-key`, token);
  const key = sodium.from_base64(publicKey.key, sodium.base64_variants.ORIGINAL);
  const encrypted = sodium.crypto_box_seal(sodium.from_string(refreshToken), key);
  const encryptedValue = sodium.to_base64(encrypted, sodium.base64_variants.ORIGINAL);
  await githubApi(
    `${path}/actions/secrets/${SECRET_NAME}`,
    token,
    "PUT",
    { encrypted_value: encryptedValue, key_id: publicKey.key_id },
  );
  // Only dispatch after GitHub confirms the encrypted secret update.
  try {
    await githubApi(
      `${path}/actions/workflows/${AUTH_WORKFLOW}/dispatches`,
      token,
      "POST",
      { ref: "main" },
    );
    return true;
  } catch {
    // The secret is already saved. Report that accurately and do not make the
    // user repeat OAuth merely because the verification dispatch failed.
    return false;
  }
}

async function githubLoginCallback(request, env, url) {
  const cookies = parseCookies(request.headers.get("Cookie"));
  const state = url.searchParams.get("state") || "";
  const code = url.searchParams.get("code") || "";
  if (!state || state !== cookies["__Host-shit_gh_state"] || !code) {
    throw new BrokerError("GitHub sign-in could not be verified. Start again.");
  }
  const stateKey = `github-state:${state}`;
  const stateValue = await env.OAUTH_KV.get(stateKey);
  if (!stateValue) throw new BrokerError("GitHub sign-in expired. Start again.");
  await env.OAUTH_KV.delete(stateKey);
  const tokenData = await exchangeForm("https://github.com/login/oauth/access_token", {
    client_id: env.GITHUB_OAUTH_CLIENT_ID,
    client_secret: env.GITHUB_OAUTH_CLIENT_SECRET,
    code,
    redirect_uri: env.GITHUB_OAUTH_REDIRECT_URI,
  });
  if (!tokenData.access_token) throw new BrokerError("GitHub sign-in failed.");
  const userResponse = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${tokenData.access_token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "SHIT-Mobile-Authorization-Broker",
    },
  });
  if (!userResponse.ok) throw new BrokerError("GitHub identity could not be verified.");
  const user = await userResponse.json();
  if (!isAuthorizedOwner(user.login, env.GITHUB_OWNER || OWNER)) {
    throw new BrokerError("This GitHub account is not authorized to manage SHIT.");
  }
  const sessionId = randomValue(32);
  await env.OAUTH_KV.put(`session:${sessionId}`, JSON.stringify({ login: user.login }), { expirationTtl: SESSION_TTL });
  return redirect(new URL("/spotify/start", url.origin).toString(), {
    "Set-Cookie": cookie("__Host-shit_session", sessionId, SESSION_TTL),
  });
}

async function spotifyCallback(request, env, url) {
  const cookies = parseCookies(request.headers.get("Cookie"));
  const session = await getSession(request, env);
  const state = url.searchParams.get("state") || "";
  const code = url.searchParams.get("code") || "";
  if (!session || !state || state !== cookies["__Host-shit_spotify_state"] || !code) {
    throw new BrokerError("Spotify authorization could not be verified. Start again.");
  }
  const key = `spotify-state:${state}`;
  const activeKey = `spotify-active:${session.id}`;
  const stored = await env.OAUTH_KV.get(key);
  const activeState = await env.OAUTH_KV.get(activeKey);
  if (!stored || activeState !== state) throw new BrokerError("Spotify authorization expired or was superseded. Start again.");
  await env.OAUTH_KV.delete(key);
  await env.OAUTH_KV.delete(activeKey);
  const stateData = JSON.parse(stored);
  if (stateData.sessionId !== session.id) throw new BrokerError("Spotify authorization session mismatch.");
  const tokenData = await exchangeForm("https://accounts.spotify.com/api/token", {
    client_id: env.SPOTIFY_CLIENT_ID,
    grant_type: "authorization_code",
    code,
    redirect_uri: env.SPOTIFY_REDIRECT_URI,
    code_verifier: stateData.verifier,
  });
  if (!hasRequiredScopes(tokenData.scope)) {
    throw new BrokerError("Spotify did not grant every permission required by SHIT. Start again and approve all requested permissions.");
  }
  const verificationStarted = await saveRefreshToken(env, tokenData.refresh_token);
  await env.OAUTH_KV.delete(`session:${session.id}`);
  const message = verificationStarted
    ? "Your Spotify authorization was securely saved to GitHub. SHIT has started a read-only authentication check. No playlist was unlocked or changed."
    : "Your Spotify authorization was securely saved to GitHub, but the automatic read-only check could not be started. Open the Actions page and run the Spotify Auth Health Check manually. No playlist was unlocked or changed.";
  return page(
    "Spotify authorization saved",
    message,
    { href: `https://github.com/${OWNER}/${REPOSITORY}/actions/workflows/${AUTH_WORKFLOW}`, label: "View SHIT authentication check" },
  );
}

export async function handleRequest(request, env) {
  const url = new URL(request.url);
  try {
    if (url.pathname === "/" && request.method === "GET") {
      return page("SHIT mobile authorization", "Sign in with the repository owner account, then approve Spotify. This process never edits playlists.", {
        href: "/auth/github/start",
        label: "Continue with GitHub",
      });
    }

    if (url.pathname === "/auth/github/start" && request.method === "GET") {
      await rateLimit(request, env, "github-start");
      requireEnv(env, ["GITHUB_OAUTH_CLIENT_ID", "GITHUB_OAUTH_REDIRECT_URI"]);
      const state = randomValue(24);
      await env.OAUTH_KV.put(`github-state:${state}`, "pending", { expirationTtl: OAUTH_TTL });
      const target = new URL("https://github.com/login/oauth/authorize");
      target.search = new URLSearchParams({
        client_id: env.GITHUB_OAUTH_CLIENT_ID,
        redirect_uri: env.GITHUB_OAUTH_REDIRECT_URI,
        scope: "read:user",
        state,
      });
      return redirect(target.toString(), { "Set-Cookie": cookie("__Host-shit_gh_state", state, OAUTH_TTL) });
    }

    if (url.pathname === "/auth/github/callback" && request.method === "GET") {
      await rateLimit(request, env, "github-callback");
      requireEnv(env, ["GITHUB_OAUTH_CLIENT_ID", "GITHUB_OAUTH_CLIENT_SECRET", "GITHUB_OAUTH_REDIRECT_URI", "GITHUB_OWNER"]);
      const result = await githubLoginCallback(request, env, url);
      result.headers.append("Set-Cookie", clearCookie("__Host-shit_gh_state"));
      return result;
    }

    if (url.pathname === "/spotify/start" && request.method === "GET") {
      await rateLimit(request, env, "spotify-start");
      requireEnv(env, ["SPOTIFY_CLIENT_ID", "SPOTIFY_REDIRECT_URI"]);
      const session = await getSession(request, env);
      if (!session) return redirect("/auth/github/start");
      const verifier = randomValue(64);
      const state = randomValue(24);
      const challenge = await pkceChallenge(verifier);
      await env.OAUTH_KV.put(
        `spotify-state:${state}`,
        JSON.stringify({ sessionId: session.id, verifier }),
        { expirationTtl: OAUTH_TTL },
      );
      // Only the most recently started Spotify authorization for this session
      // may complete; this prevents stale parallel callbacks from racing secrets.
      await env.OAUTH_KV.put(`spotify-active:${session.id}`, state, { expirationTtl: OAUTH_TTL });
      const target = new URL("https://accounts.spotify.com/authorize");
      target.search = new URLSearchParams({
        client_id: env.SPOTIFY_CLIENT_ID,
        response_type: "code",
        redirect_uri: env.SPOTIFY_REDIRECT_URI,
        scope: REQUIRED_SCOPES.join(" "),
        state,
        code_challenge_method: "S256",
        code_challenge: challenge,
      });
      return redirect(target.toString(), { "Set-Cookie": cookie("__Host-shit_spotify_state", state, OAUTH_TTL) });
    }

    if (url.pathname === "/spotify/callback" && request.method === "GET") {
      await rateLimit(request, env, "spotify-callback");
      requireEnv(env, ["SPOTIFY_CLIENT_ID", "SPOTIFY_REDIRECT_URI", "GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY"]);
      const result = await spotifyCallback(request, env, url);
      result.headers.append("Set-Cookie", clearCookie("__Host-shit_spotify_state"));
      result.headers.append("Set-Cookie", clearCookie("__Host-shit_session"));
      return result;
    }

    return response("Not found.", 404, { "Content-Type": "text/plain; charset=utf-8" });
  } catch (error) {
    // Never log provider responses, OAuth codes, tokens, state values, or exception details.
    const message = error instanceof BrokerError ? error.message : "The authorization service encountered an unexpected error.";
    return page("Authorization not completed", message, { href: "/", label: "Start again" });
  }
}

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  },
};


// FILE OVERVIEW
// Purpose: Mobile-first Spotify Authorization Code + PKCE bootstrap for SHIT.
// Runtime: Cloudflare Worker with short-lived KV state and an edge rate limiter.
// Credentials: GitHub OAuth secret and repository-scoped GitHub App private key are Worker secrets.
// Side effects: Updates only the repository SPOTIFY_REFRESH_TOKEN Actions secret, then dispatches
//              the read-only Spotify auth-health workflow. It has no playlist-write operations.
// Safety: GitHub owner allowlist, single-use state, session binding, PKCE, secret encryption,
//         short-lived installation token, no token logging/return, fail-closed secret persistence.
// Related: auth-broker/README.md, project/goals/mobile-cloud-operation/ROADMAP.md.
