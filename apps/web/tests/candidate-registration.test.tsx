import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const signUp = vi.fn();
vi.mock("@supabase/ssr", () => ({
  createBrowserClient: () => ({ auth: { signUp } }),
}));

describe("candidate registration", () => {
  beforeEach(() => signUp.mockReset());

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
});
