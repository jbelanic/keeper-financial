import { NextRequest } from "next/server";

let cookieUpdates: Array<{
  name: string;
  value: string;
  options?: {
    httpOnly?: boolean;
    sameSite?: "lax";
    path?: string;
    maxAge?: number;
  };
}> = [];
let observedCookies: Array<{ name: string; value: string }> = [];
const getUser = vi.fn();

vi.mock("@supabase/ssr", () => ({
  createServerClient: (
    _url: string,
    _key: string,
    options: {
      cookies: {
        getAll: () => Array<{ name: string; value: string }>;
        setAll: (items: typeof cookieUpdates) => void;
      };
    },
  ) => ({
    auth: {
      getUser: async () => {
        observedCookies = options.cookies.getAll();
        options.cookies.setAll(cookieUpdates);
        return getUser();
      },
    },
  }),
}));

describe("Supabase SSR session refresh proxy", () => {
  beforeEach(() => {
    cookieUpdates = [];
    observedCookies = [];
    getUser
      .mockReset()
      .mockResolvedValue({ data: { user: null }, error: null });
  });

  it("persists a rotated session cookie on the response", async () => {
    cookieUpdates = [
      {
        name: "sb-local-auth-token",
        value: "rotated-session",
        options: { httpOnly: true, sameSite: "lax", path: "/" },
      },
    ];
    const { proxy } = await import("@/proxy");
    const response = await proxy(
      new NextRequest("http://localhost:3000/candidate"),
    );
    expect(getUser).toHaveBeenCalledOnce();
    expect(response.cookies.get("sb-local-auth-token")?.value).toBe(
      "rotated-session",
    );
  });

  it("clears an expired or revoked session cookie", async () => {
    cookieUpdates = [
      {
        name: "sb-local-auth-token",
        value: "",
        options: { httpOnly: true, sameSite: "lax", path: "/", maxAge: 0 },
      },
    ];
    getUser.mockResolvedValue({
      data: { user: null },
      error: { name: "expired" },
    });
    const { proxy } = await import("@/proxy");
    const response = await proxy(
      new NextRequest("http://localhost:3000/candidate", {
        headers: { cookie: "sb-local-auth-token=expired-session" },
      }),
    );
    expect(response.headers.get("set-cookie")).toContain("Max-Age=0");
    expect(response.headers.get("set-cookie")).not.toContain("expired-session");
  });

  it("reads the persisted cookie on a subsequent server request", async () => {
    const { proxy } = await import("@/proxy");
    await proxy(
      new NextRequest("http://localhost:3000/candidate", {
        headers: { cookie: "sb-local-auth-token=persisted-session" },
      }),
    );
    expect(observedCookies).toContainEqual({
      name: "sb-local-auth-token",
      value: "persisted-session",
    });
  });

  it("redirects protected requests safely when session refresh is unavailable", async () => {
    getUser.mockRejectedValue(new Error("provider unavailable"));
    const { proxy } = await import("@/proxy");
    const response = await proxy(
      new NextRequest("http://localhost:3000/candidate/onboarding", {
        headers: { cookie: "sb-local-auth-token=private-session" },
      }),
    );
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/auth/sign-in?error=session&returnTo=%2Fcandidate",
    );
    expect(response.headers.get("location")).not.toContain("private-session");
  });

  it("redirects protected requests to the external container host", async () => {
    getUser.mockRejectedValue(new Error("provider unavailable"));
    const { proxy } = await import("@/proxy");
    const response = await proxy(
      new NextRequest("http://0.0.0.0:3000/candidate/onboarding", {
        headers: { host: "127.0.0.1:3000" },
      }),
    );

    expect(response.headers.get("location")).toBe(
      "http://127.0.0.1:3000/auth/sign-in?error=session&returnTo=%2Fcandidate",
    );
  });

  it("routes the exact local application host without invoking Supabase", async () => {
    const { proxy } = await import("@/proxy");
    const response = await proxy(
      new NextRequest("http://apply.localhost:3000/", {
        headers: { host: "apply.localhost:3000" },
      }),
    );
    expect(response.headers.get("x-middleware-rewrite")).toBe(
      "http://apply.localhost:3000/mortgage-application",
    );
    expect(getUser).not.toHaveBeenCalled();
  });

  it("rejects conflicting forwarded hosts before borrower routing", async () => {
    const { proxy } = await import("@/proxy");
    const response = await proxy(
      new NextRequest("http://apply.localhost:3000/", {
        headers: {
          host: "apply.localhost:3000",
          "x-forwarded-host": "unexpected.example",
        },
      }),
    );
    expect(response.status).toBe(400);
    expect(getUser).not.toHaveBeenCalled();
  });

  it("proxies only borrower API paths from the exact application host", async () => {
    const { proxy } = await import("@/proxy");
    const response = await proxy(
      new NextRequest(
        "http://apply.localhost:3000/api/v1/borrower-applications/start",
        {
          headers: {
            host: "apply.localhost:3000",
            origin: "http://apply.localhost:3000",
          },
        },
      ),
    );
    expect(response.headers.get("x-middleware-rewrite")).toBe(
      "http://localhost:8000/api/v1/borrower-applications/start",
    );
    expect(getUser).not.toHaveBeenCalled();
  });
});
