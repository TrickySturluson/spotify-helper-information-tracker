import test from "node:test";
import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const WORKFLOW_DIR = path.join(ROOT, ".github", "workflows");
const EXPECTED_DIRECT_REFRESH_ENDPOINTS = new Set();
const EXPECTED_CONSUMERS = new Set();
const EXPECTED_BROKER_CONSUMERS = new Set([
  "spotify-auth-health-check.yml",
  "spotify-daily-live-preflight.yml",
  "spotify-daily-midnight-cycle.yml",
  "spotify-daily-feedback-observation.yml",
  "tricky-daily-snapshot-refresh.yml",
  "spotify-reference-library.yml",
  "spotify-playlist-manager.yml",
  "great-migration.yml",
  "update.yml",
]);

async function workflowFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await workflowFiles(target));
    else if (entry.isFile() && /\.ya?ml$/i.test(entry.name)) files.push(target);
  }
  return files;
}

test("no active workflow reads or persists the legacy Spotify refresh-token secret", async () => {
  const consumers = new Set();
  for (const file of await workflowFiles(WORKFLOW_DIR)) {
    const source = await readFile(file, "utf8");
    if (/secrets\.SPOTIFY_REFRESH_TOKEN|\bSPOTIFY_REFRESH_TOKEN\b/.test(source)) {
      consumers.add(path.basename(file));
    }
  }
  assert.deepEqual([...consumers].sort(), [...EXPECTED_CONSUMERS].sort(),
    "Refresh-token consumers changed. Update WORKFLOW_MIGRATION_INVENTORY.md and the broker migration plan before proceeding.");
});

test("no workflow directly calls Spotify's refresh-token endpoint", async () => {
  const offenders = [];
  for (const file of await workflowFiles(WORKFLOW_DIR)) {
    const source = await readFile(file, "utf8");
    if (/https:\/\/accounts\.spotify\.com\/api\/token/.test(source)) offenders.push(path.relative(ROOT, file));
  }
  assert.deepEqual(offenders.sort(), [...EXPECTED_DIRECT_REFRESH_ENDPOINTS].map((name) => path.join(".github", "workflows", name)).sort(),
    "Direct token endpoint callers changed. Migrate them behind the broker and update the documented baseline.");
});

test("all nine Spotify workflows use the central OIDC broker", async () => {
  for (const filename of EXPECTED_BROKER_CONSUMERS) {
    const source = await readFile(path.join(WORKFLOW_DIR, filename), "utf8");
    assert.match(source, /id-token:\s*write/, filename + " must request GitHub OIDC permission");
    assert.ok(
      source.includes("scripts/spotify/broker_access_token.py") ||
      source.includes("scripts.spotify.broker_access_token"),
      filename + " must obtain access through the broker client",
    );
    assert.doesNotMatch(source, /SPOTIFY_REFRESH_TOKEN|SHIT_PERSIST_ROTATED_SPOTIFY_TOKEN|spotify-secret-writer/,
      filename + " must not use legacy refresh-token storage");
  }
});

test("deployment workflow pins the exact nine main-branch OIDC workflow identities", async () => {
  const source = await readFile(path.join(WORKFLOW_DIR, "deploy-mobile-auth-broker.yml"), "utf8");
  for (const filename of EXPECTED_BROKER_CONSUMERS) {
    assert.ok(
      source.includes(`/.github/workflows/${filename}@refs/heads/main`),
      "Missing exact OIDC allowlist entry for " + filename,
    );
  }
  assert.match(source, /wildcards and additional workflows are forbidden/);
});
