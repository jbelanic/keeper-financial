import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@keeper/ui", "@keeper/contracts"],
  poweredByHeader: false,
  images: {
    // Serve public/ images directly. Avoids the next/image optimizer, which
    // needs a native `sharp` binary that is neither a declared dependency nor
    // guaranteed to run on the below-baseline (x86-64-v1) target host.
    unoptimized: true,
  },
  experimental: {
    optimizePackageImports: ["@keeper/ui"],
    // The /api rewrite runs inside middleware, so every proxied upload body
    // passes through it. The 10 MB default silently truncated borrower documents
    // (25 MiB is allowed) and surfaced as 422/500 instead of a stored file. Keep
    // this above BORROWER_MAX_DOCUMENT_BYTES plus multipart overhead; the API
    // still enforces the per-route limits before parsing anything.
    proxyClientMaxBodySize: 32 * 1024 * 1024,
    // Keep the security-upgrade policy explicit so `next dev`/`next build`
    // surface advisory-driven upgrade prompts instead of silently drifting.
    agentUpgrade: "security",
  },
  async redirects() {
    return [
      {
        source: "/privacy",
        destination: "/privacy-policy",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
