import { afterEach, describe, expect, it, vi } from "vitest";

import { dynamic as careersRendering } from "@/app/(public)/careers/page";
import { apiBaseUrl } from "@/lib/recruitment-api";
import { supabaseServerUrl } from "@/lib/supabase-server";

describe("container-aware server routing", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses the internal API URL for server rendering", () => {
    vi.stubEnv("API_INTERNAL_URL", "http://api:8000");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000");

    expect(apiBaseUrl(true)).toBe("http://api:8000");
  });

  it("keeps the public API URL for browser requests", () => {
    vi.stubEnv("API_INTERNAL_URL", "http://api:8000");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000");

    expect(apiBaseUrl(false)).toBe("http://localhost:8000");
  });

  it("uses the host-routable Supabase URL for server authentication", () => {
    vi.stubEnv("SUPABASE_INTERNAL_URL", "http://host.docker.internal:54321");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "http://127.0.0.1:54321");

    expect(supabaseServerUrl()).toBe("http://host.docker.internal:54321");
  });

  it("does not freeze a build-time API failure into the careers page", () => {
    expect(careersRendering).toBe("force-dynamic");
  });
});
