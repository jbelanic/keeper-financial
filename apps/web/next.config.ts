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
  },
};

export default nextConfig;
