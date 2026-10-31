import { describe, expect, it } from "vitest";

import nextConfig from "../next.config";

// BORROWER_MAX_DOCUMENT_BYTES is 25 MiB (apps/api config) and the largest single
// upload the application accepts. Multipart framing adds a few hundred bytes on
// top of the file itself.
const BORROWER_MAX_DOCUMENT_BYTES = 25 * 1024 * 1024;
const MULTIPART_OVERHEAD_BYTES = 64 * 1024;

describe("proxied upload body limit", () => {
  // The /api rewrite runs inside middleware, so an upload body passes through it
  // before reaching the API. Next defaults this to 10 MB, which silently
  // truncated larger borrower documents and surfaced as 422/500 instead of a
  // stored file.
  it("allows a full-size borrower document plus multipart overhead", () => {
    const limit = nextConfig.experimental?.proxyClientMaxBodySize;

    expect(limit).toBeDefined();
    expect(Number(limit)).toBeGreaterThanOrEqual(
      BORROWER_MAX_DOCUMENT_BYTES + MULTIPART_OVERHEAD_BYTES,
    );
  });
});
