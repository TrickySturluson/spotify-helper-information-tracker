import test from "node:test";
import assert from "node:assert/strict";
import {
  escapeHtml,
  handleRequest,
  hasRequiredScopes,
  isAuthorizedOwner,
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


test("concurrency gate recognizes Spotify credential workflows but excludes broker jobs", () => {
  assert.equal(isSpotifyWorkflowPath(".github/workflows/spotify-daily-midnight-cycle.yml"), true);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/spotify-auth-health-check.yml"), true);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/great-migration.yml"), true);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/daily-curator-tests.yml"), false);
  assert.equal(isSpotifyWorkflowPath(".github/workflows/deploy-mobile-auth-broker.yml"), false);
  assert.equal(isSpotifyWorkflowPath("auth-broker/src/index.js"), false);
});
