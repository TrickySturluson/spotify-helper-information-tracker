import { setupNetwork } from "@msw/cloudflare";

export const network = setupNetwork();


// FILE OVERVIEW
// Purpose: Shared MSW network fixture for Cloudflare Workers runtime tests.
// Safety: Outbound requests are intercepted by explicit per-test handlers.
