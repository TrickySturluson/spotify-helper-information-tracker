import { afterAll, afterEach, beforeAll } from "vitest";
import { network } from "./network.js";

beforeAll(() => network.enable());
afterEach(() => network.resetHandlers());
afterAll(() => network.disable());


// FILE OVERVIEW
// Purpose: Enable and reset the MSW Cloudflare network fixture around Vitest test files.
// Safety: No external provider requests are allowed unless a test explicitly mocks them.
