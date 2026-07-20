import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { candidateDocumentMfaReturn, safeMfaReturnTo } from "@/lib/mfa-return";

const mfa = vi.hoisted(() => ({
  challengeAndVerify: vi.fn(),
  enroll: vi.fn(),
  getAuthenticatorAssuranceLevel: vi.fn(),
  listFactors: vi.fn(),
  unenroll: vi.fn(),
}));
const refreshSession = vi.hoisted(() => vi.fn());

vi.mock("@supabase/ssr", () => ({
  createBrowserClient: () => ({ auth: { mfa, refreshSession } }),
}));

describe("candidate document MFA", () => {
  beforeEach(() => {
    Object.values(mfa).forEach((mock) => mock.mockReset());
    refreshSession.mockReset().mockResolvedValue({
      data: { session: { access_token: "synthetic-refreshed-token" } },
      error: null,
    });
  });

  it("accepts only an exact candidate document return and rejects privileged or external paths", () => {
    const exact =
      "/candidate/applications/00000000-0000-4000-8000-000000000111#documents";
    expect(safeMfaReturnTo(exact)).toBe(exact);
    expect(safeMfaReturnTo("/admin/candidates")).toBe("/candidate");
    expect(safeMfaReturnTo("https://example.test/admin")).toBe("/candidate");
    expect(
      safeMfaReturnTo("/candidate/applications/not-a-uuid#documents"),
    ).toBe("/candidate");
    expect(
      candidateDocumentMfaReturn("00000000-0000-4000-8000-000000000111"),
    ).toBe(
      "/auth/mfa?returnTo=%2Fcandidate%2Fapplications%2F00000000-0000-4000-8000-000000000111%23documents",
    );
  });

  it("refreshes and proves AAL2 before returning to the exact candidate document section", async () => {
    mfa.getAuthenticatorAssuranceLevel
      .mockResolvedValueOnce({
        data: { currentLevel: "aal1", nextLevel: "aal2" },
        error: null,
      })
      .mockResolvedValue({
        data: { currentLevel: "aal2", nextLevel: "aal2" },
        error: null,
      });
    mfa.listFactors.mockResolvedValue({
      data: {
        all: [
          { id: "candidate-factor", factor_type: "totp", status: "verified" },
        ],
        totp: [
          { id: "candidate-factor", factor_type: "totp", status: "verified" },
        ],
        phone: [],
      },
      error: null,
    });
    mfa.challengeAndVerify.mockResolvedValue({
      data: { access_token: "synthetic-aal2-token" },
      error: null,
    });
    const returnTo =
      "/candidate/applications/00000000-0000-4000-8000-000000000111#documents" as const;
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(<MfaEnrollment returnTo={returnTo} />);

    fireEvent.change(
      await screen.findByLabelText(/six-digit authentication code/i),
      { target: { value: "123456" } },
    );
    fireEvent.click(screen.getByRole("button", { name: /verify code/i }));

    await waitFor(() => expect(refreshSession).toHaveBeenCalledOnce());
    expect(
      await screen.findByRole("link", {
        name: /continue to candidate documents/i,
      }),
    ).toHaveAttribute("href", returnTo);
  });

  it("uses a candidate-scoped factor name during enrollment", async () => {
    mfa.getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal1", nextLevel: "aal1" },
      error: null,
    });
    mfa.listFactors.mockResolvedValue({
      data: { all: [], totp: [], phone: [] },
      error: null,
    });
    mfa.enroll.mockResolvedValue({
      data: {
        id: "candidate-factor",
        type: "totp",
        totp: {
          qr_code: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
          secret: "SYNTHETICSETUPKEY",
          uri: "otpauth://synthetic",
        },
      },
      error: null,
    });
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(
      <MfaEnrollment returnTo="/candidate/applications/00000000-0000-4000-8000-000000000111#documents" />,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /begin totp enrollment/i }),
    );
    await screen.findByAltText("TOTP enrollment QR code");
    expect(mfa.enroll).toHaveBeenCalledWith({
      factorType: "totp",
      friendlyName: "Keeper Financial candidate documents",
      issuer: "Keeper Financial",
    });
  });
});
