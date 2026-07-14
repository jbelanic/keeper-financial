import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@keeper/ui", "@keeper/contracts"],
  poweredByHeader: false,
  experimental: {
    optimizePackageImports: ["@keeper/ui"],
  },
};

export default nextConfig;
