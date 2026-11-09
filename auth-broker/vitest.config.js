import { cloudflareTest } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.toml" },
      miniflare: {
        bindings: {
          SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS: JSON.stringify({
            "1": "BwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwc=",
            "2": "CAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg=",
          }),
          SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION: "1",
          SPOTIFY_CLIENT_ID: "integration-test-client",
          SPOTIFY_CLIENT_SECRET: "integration-test-secret",
          BROKER_BASE_URL: "https://broker.example.workers.dev",
          SPOTIFY_REFRESH_WORKFLOW_REFS: "TrickySturluson/spotify-helper-information-tracker/.github/workflows/spotify-auth-health-check.yml@refs/heads/main",
        },
      },
    }),
  ],
  test: {
    include: ["test/credential-store.integration.worker.js"],
    setupFiles: ["test/worker-setup.js"],
    testTimeout: 15_000,
    hookTimeout: 15_000,
  },
});


// FILE OVERVIEW
// Purpose: Run focused broker Durable Object tests inside the Cloudflare Workers runtime.
// Bindings: Uses test-only encryption keys and mock Spotify app credentials; no production secrets.
// Related: auth-broker/wrangler.toml, test/credential-store.integration.test.js.
