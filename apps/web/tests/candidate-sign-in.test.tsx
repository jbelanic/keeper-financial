import { render, screen } from "@testing-library/react";
import { NextRequest } from "next/server";

const signInWithPassword = vi.fn();
const exchangeCodeForSession = vi.fn();
const startCandidateApplication = vi.fn();
const getPublishedPosting = vi.fn();

vi.mock("@/lib/supabase-server", () => ({
  getSupabaseServerClient: async () => ({
    auth: { signInWithPassword, exchangeCodeForSession },
  }),
}));

vi.mock("@/lib/candidate-provisioning", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/candidate-provisioning")>();
  return { ...actual, startCandidateApplication };
});

vi.mock("@/lib/recruitment-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/recruitment-api")>();
  return { ...actual, getPublishedPosting };
});

function request(body: URLSearchParams) {
  return new NextRequest("http://localhost:3000/auth/sign-in/submit", {
    method: "POST",
    headers: {
      origin: "http://localhost:3000",
      "content-type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });
}

describe("posting-bound existing-user sign-in", () => {
  beforeEach(() => {
    signInWithPassword.mockReset();
    exchangeCodeForSession.mockReset();
    startCandidateApplication.mockReset();
    getPublishedPosting.mockReset();
  });

  it("renders an explicit posting-bound native form", async () => {
    const { SignInForm } = await import("@/app/auth/sign-in/sign-in-form");
    const { container } = render(
      <SignInForm
        posting="synthetic-opportunity"
        returnTo="/candidate"
        error="application-access"
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      /application access could not be prepared/i,
    );
    expect(container.querySelector("form")).toHaveAttribute(
      "action",
      "/auth/sign-in/submit",
    );
    expect(container.querySelector('input[name="posting"]')).toHaveValue(
      "synthetic-opportunity",
    );
  });

  it("provisions only when a validated posting context is supplied", async () => {
    signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "signed-access-token" } },
      error: null,
    });
    startCandidateApplication.mockResolvedValue({ id: "application-123" });
    const { POST } = await import("@/app/auth/sign-in/submit/route");
    const response = await POST(
      request(
        new URLSearchParams({
          email: "synthetic@example.test",
          password: "synthetic-password",
          posting: "synthetic-opportunity",
          returnTo: "/candidate",
        }),
      ),
    );
    expect(response.status).toBe(303);
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/candidate/applications/application-123",
    );
    expect(startCandidateApplication).toHaveBeenCalledWith(
      "signed-access-token",
      "synthetic-opportunity",
    );
  });

  it("keeps generic sign-in non-provisioning", async () => {
    signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "signed-access-token" } },
      error: null,
    });
    const { POST } = await import("@/app/auth/sign-in/submit/route");
    const response = await POST(
      request(
        new URLSearchParams({
          email: "unmapped@example.test",
          password: "synthetic-password",
          returnTo: "/candidate",
        }),
      ),
    );
    expect(response.status).toBe(303);
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/candidate",
    );
    expect(startCandidateApplication).not.toHaveBeenCalled();
  });

  it("redirects to the external request host behind the local container", async () => {
    signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "signed-access-token" } },
      error: null,
    });
    const { POST } = await import("@/app/auth/sign-in/submit/route");
    const response = await POST(
      new NextRequest("http://0.0.0.0:3000/auth/sign-in/submit", {
        method: "POST",
        headers: {
          host: "127.0.0.1:3000",
          origin: "http://127.0.0.1:3000",
          "content-type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          email: "admin@example.test",
          password: "synthetic-password",
          returnTo: "/admin",
        }).toString(),
      }),
    );

    expect(response.status).toBe(303);
    expect(response.headers.get("location")).toBe(
      "http://127.0.0.1:3000/auth/mfa?returnTo=/admin",
    );
  });

  it("routes an explicit admin return through MFA without provisioning", async () => {
    signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "signed-access-token" } },
      error: null,
    });
    const { POST } = await import("@/app/auth/sign-in/submit/route");
    const response = await POST(
      request(
        new URLSearchParams({
          email: "admin@example.test",
          password: "synthetic-password",
          returnTo: "/admin",
        }),
      ),
    );
    expect(response.status).toBe(303);
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/auth/mfa?returnTo=/admin",
    );
    expect(startCandidateApplication).not.toHaveBeenCalled();
  });

  it("offers an explicit brokerage administrator sign-in path", async () => {
    const { default: SignInPage } = await import("@/app/auth/sign-in/page");
    render(<>{await SignInPage({ searchParams: Promise.resolve({}) })}</>);
    expect(
      screen.getByRole("link", { name: /brokerage administrator sign in/i }),
    ).toHaveAttribute("href", "/auth/sign-in?returnTo=/admin");
    expect(
      screen.getByText(
        /sign in to an existing keeper financial portal account/i,
      ),
    ).toBeInTheDocument();
  });

  it("explains that posting-bound sign-in provisions before ordinary portal access", async () => {
    getPublishedPosting.mockResolvedValue({
      slug: "synthetic-opportunity",
      title: "Synthetic opportunity",
    });
    const { default: SignInPage } = await import("@/app/auth/sign-in/page");
    render(
      <>
        {await SignInPage({
          searchParams: Promise.resolve({ posting: "synthetic-opportunity" }),
        })}
      </>,
    );

    expect(
      screen.getByText(
        /this route will continue only to the selected published opportunity/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        /sign in to an existing keeper financial portal account/i,
      ),
    ).not.toBeInTheDocument();
  });

  it("rejects malformed posting context before authentication", async () => {
    const { POST } = await import("@/app/auth/sign-in/submit/route");
    const response = await POST(
      request(
        new URLSearchParams({
          email: "synthetic@example.test",
          password: "synthetic-password",
          posting: "../admin",
        }),
      ),
    );
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/auth/sign-in?error=posting-unavailable",
    );
    expect(signInWithPassword).not.toHaveBeenCalled();
    expect(startCandidateApplication).not.toHaveBeenCalled();
  });

  it("preserves safe posting context on a recoverable provisioning error", async () => {
    signInWithPassword.mockResolvedValue({
      data: { session: { access_token: "signed-access-token" } },
      error: null,
    });
    startCandidateApplication.mockRejectedValue(new Error("temporary"));
    const { POST } = await import("@/app/auth/sign-in/submit/route");
    const response = await POST(
      request(
        new URLSearchParams({
          email: "synthetic@example.test",
          password: "synthetic-password",
          posting: "synthetic-opportunity",
        }),
      ),
    );
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/auth/sign-in?error=application-access&posting=synthetic-opportunity",
    );
  });

  it("fails closed with bounded recovery when the identity provider is unavailable", async () => {
    signInWithPassword.mockRejectedValue(new Error("provider unavailable"));
    const { POST } = await import("@/app/auth/sign-in/submit/route");
    const response = await POST(
      request(
        new URLSearchParams({
          email: "synthetic@example.test",
          password: "synthetic-password",
          posting: "synthetic-opportunity",
        }),
      ),
    );
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/auth/sign-in?error=credentials&posting=synthetic-opportunity",
    );
    expect(startCandidateApplication).not.toHaveBeenCalled();
  });
});

describe("posting-bound confirmation callback", () => {
  beforeEach(() => {
    exchangeCodeForSession.mockReset();
    startCandidateApplication.mockReset();
  });

  it("exchanges the code and enters the provisioned application", async () => {
    exchangeCodeForSession.mockResolvedValue({
      data: { session: { access_token: "callback-access-token" } },
      error: null,
    });
    startCandidateApplication.mockResolvedValue({ id: "application-456" });
    const { GET } = await import("@/app/auth/callback/route");
    const response = await GET(
      new NextRequest(
        "http://localhost:3000/auth/callback?code=bounded-code&posting=synthetic-opportunity",
      ),
    );
    expect(exchangeCodeForSession).toHaveBeenCalledWith("bounded-code");
    expect(startCandidateApplication).toHaveBeenCalledWith(
      "callback-access-token",
      "synthetic-opportunity",
    );
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/candidate/applications/application-456",
    );
  });

  it("redirects callbacks to the external container host", async () => {
    exchangeCodeForSession.mockResolvedValue({
      data: { session: { access_token: "callback-access-token" } },
      error: null,
    });
    startCandidateApplication.mockResolvedValue({ id: "application-456" });
    const { GET } = await import("@/app/auth/callback/route");
    const response = await GET(
      new NextRequest(
        "http://0.0.0.0:3000/auth/callback?code=bounded-code&posting=synthetic-opportunity",
        { headers: { host: "127.0.0.1:3000" } },
      ),
    );

    expect(response.headers.get("location")).toBe(
      "http://127.0.0.1:3000/candidate/applications/application-456",
    );
  });

  it("retains safe posting context when verification can be retried", async () => {
    exchangeCodeForSession.mockResolvedValue({
      data: { session: null },
      error: {},
    });
    const { GET } = await import("@/app/auth/callback/route");
    const response = await GET(
      new NextRequest(
        "http://localhost:3000/auth/callback?code=bounded-code&posting=synthetic-opportunity",
      ),
    );
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/auth/sign-in?error=verification&posting=synthetic-opportunity",
    );
    expect(startCandidateApplication).not.toHaveBeenCalled();
  });

  it("fails closed without exposing provider errors when code exchange is unavailable", async () => {
    exchangeCodeForSession.mockRejectedValue(new Error("provider payload"));
    const { GET } = await import("@/app/auth/callback/route");
    const response = await GET(
      new NextRequest(
        "http://localhost:3000/auth/callback?code=bounded-code&posting=synthetic-opportunity",
      ),
    );
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/auth/sign-in?error=verification&posting=synthetic-opportunity",
    );
    expect(response.headers.get("location")).not.toContain("provider");
  });
});
