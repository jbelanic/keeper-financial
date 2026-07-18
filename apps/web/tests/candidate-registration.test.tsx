import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const signUp = vi.fn();
vi.mock("@supabase/ssr", () => ({
  createBrowserClient: () => ({ auth: { signUp } }),
}));

describe("candidate registration", () => {
  beforeEach(() => signUp.mockReset());
  afterEach(() => vi.unstubAllGlobals());

  it("registers through Supabase with a posting-bound verification callback", async () => {
    signUp.mockResolvedValue({ error: null });
    const { CandidateRegistrationForm } = await import(
      "@/app/auth/register/registration-form"
    );
    render(<CandidateRegistrationForm posting="synthetic-opportunity" />);
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "candidate@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "correct-horse-battery-staple" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /create account/i }));
    await waitFor(() => expect(signUp).toHaveBeenCalledOnce());
    expect(signUp).toHaveBeenCalledWith(
      expect.objectContaining({
        email: "candidate@example.test",
        password: "correct-horse-battery-staple",
        options: expect.objectContaining({
          emailRedirectTo: expect.stringMatching(
            /\/auth\/callback\?posting=synthetic-opportunity$/,
          ),
        }),
      }),
    );
    expect(screen.getByRole("status")).toHaveTextContent(/check your email/i);
  });

  it("never accepts an unbounded posting value", async () => {
    const { CandidateRegistrationForm } = await import(
      "@/app/auth/register/registration-form"
    );
    render(<CandidateRegistrationForm posting="../admin" />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      /application link is unavailable/i,
    );
    expect(
      screen.queryByRole("button", { name: /create account/i }),
    ).toBeNull();
  });

  it("server-validates a published posting and links existing-user recovery", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          slug: "synthetic-opportunity",
          title: "Synthetic opportunity",
          summary: "Synthetic summary.",
          body: "Synthetic body.",
        }),
      }),
    );
    const { default: RegistrationPage } = await import(
      "@/app/auth/register/page"
    );
    render(
      await RegistrationPage({
        searchParams: Promise.resolve({ posting: "synthetic-opportunity" }),
      }),
    );
    expect(
      screen.getByRole("link", { name: /sign in and continue/i }),
    ).toHaveAttribute("href", "/auth/sign-in?posting=synthetic-opportunity");
  });

  it("rejects an unpublished but well-formed posting context", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );
    const { default: RegistrationPage } = await import(
      "@/app/auth/register/page"
    );
    render(
      await RegistrationPage({
        searchParams: Promise.resolve({ posting: "closed-opportunity" }),
      }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/link is unavailable/i);
    expect(
      screen.queryByRole("button", { name: /create account/i }),
    ).toBeNull();
  });
});
