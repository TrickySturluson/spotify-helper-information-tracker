import test from "node:test";
import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const WORKFLOW_DIR = path.join(ROOT, ".github", "workflows");
const EXPECTED_CONSUMERS = new Set([
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

test("direct refresh-token workflow inventory matches the documented nine-consumer baseline", async () => {
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
  assert.deepEqual(offenders, [],
    "Direct token endpoint calls must live behind the broker, not in workflow definitions.");
});
