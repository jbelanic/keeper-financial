import { fireEvent, render, screen, waitFor } from "@testing-library/react";

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

describe("local administrator TOTP workflow", () => {
  beforeEach(() => {
    mfa.challengeAndVerify.mockReset();
    mfa.enroll.mockReset();
    mfa.getAuthenticatorAssuranceLevel.mockReset();
    mfa.listFactors.mockReset();
    mfa.unenroll.mockReset();
    refreshSession.mockReset().mockResolvedValue({
      data: { session: { access_token: "refreshed-aal2-token" } },
      error: null,
    });
  });

  it("challenges a verified TOTP factor and continues only after AAL2", async () => {
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
        all: [{ id: "factor-1", factor_type: "totp", status: "verified" }],
        totp: [{ id: "factor-1", factor_type: "totp", status: "verified" }],
        phone: [],
      },
      error: null,
    });
    mfa.challengeAndVerify.mockResolvedValue({
      data: { access_token: "aal2-access-token" },
      error: null,
    });
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(<MfaEnrollment returnTo="/admin" />);

    const input = await screen.findByLabelText(/six-digit authenticator code/i);
    fireEvent.change(input, { target: { value: "123456" } });
    fireEvent.click(
      screen.getByRole("button", { name: /verify authenticator/i }),
    );

    await waitFor(() =>
      expect(mfa.challengeAndVerify).toHaveBeenCalledWith({
        factorId: "factor-1",
        code: "123456",
      }),
    );
    expect(
      await screen.findByRole("link", { name: /continue to administration/i }),
    ).toHaveAttribute("href", "/admin");
    expect(refreshSession).toHaveBeenCalledOnce();
  });

  it("enrolls and verifies a new TOTP factor without service-role access", async () => {
    const qrCode =
      'data:image/svg+xml;utf-8,<svg xmlns="http://www.w3.org/2000/svg"></svg>';
    mfa.getAuthenticatorAssuranceLevel
      .mockResolvedValueOnce({
        data: { currentLevel: "aal1", nextLevel: "aal1" },
        error: null,
      })
      .mockResolvedValue({
        data: { currentLevel: "aal2", nextLevel: "aal2" },
        error: null,
      });
    mfa.listFactors.mockResolvedValue({
      data: { all: [], totp: [], phone: [] },
      error: null,
    });
    mfa.enroll.mockResolvedValue({
      data: {
        id: "new-factor",
        type: "totp",
        totp: {
          qr_code: `${qrCode}\n\t `,
          secret: "SYNTHETICSETUPKEY",
          uri: "otpauth://synthetic",
        },
      },
      error: null,
    });
    mfa.challengeAndVerify.mockResolvedValue({
      data: { access_token: "aal2-access-token" },
      error: null,
    });
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(<MfaEnrollment returnTo="/admin" />);

    fireEvent.click(
      await screen.findByRole("button", { name: /begin totp enrollment/i }),
    );
    expect(
      await screen.findByAltText("TOTP enrollment QR code"),
    ).toHaveAttribute("src", qrCode);
    expect(await screen.findByText("SYNTHETICSETUPKEY")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/six-digit authenticator code/i), {
      target: { value: "654321" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /verify authenticator/i }),
    );

    await waitFor(() =>
      expect(mfa.enroll).toHaveBeenCalledWith({
        factorType: "totp",
        friendlyName: "Keeper Financial administration",
        issuer: "Keeper Financial",
      }),
    );
    expect(
      await screen.findByRole("link", { name: /continue to administration/i }),
    ).toBeInTheDocument();
    expect(refreshSession).toHaveBeenCalledOnce();
  });

  it("removes an existing unverified factor before creating one replacement", async () => {
    mfa.getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal1", nextLevel: "aal1" },
      error: null,
    });
    mfa.listFactors.mockResolvedValue({
      data: {
        all: [
          {
            id: "incomplete-factor",
            factor_type: "totp",
            status: "unverified",
          },
        ],
        totp: [],
        phone: [],
      },
      error: null,
    });
    mfa.unenroll.mockResolvedValue({ data: {}, error: null });
    mfa.enroll.mockResolvedValue({
      data: {
        id: "replacement-factor",
        type: "totp",
        totp: {
          qr_code: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
          secret: "REPLACEMENTSETUPKEY",
          uri: "otpauth://synthetic-replacement",
        },
      },
      error: null,
    });
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(<MfaEnrollment returnTo="/admin" />);

    const enrollButton = await screen.findByRole("button", {
      name: /begin totp enrollment/i,
    });
    fireEvent.click(enrollButton);
    fireEvent.click(enrollButton);

    await screen.findByAltText("TOTP enrollment QR code");
    expect(mfa.unenroll).toHaveBeenCalledTimes(1);
    expect(mfa.unenroll).toHaveBeenCalledWith({
      factorId: "incomplete-factor",
    });
    expect(mfa.enroll).toHaveBeenCalledTimes(1);
    expect(mfa.unenroll.mock.invocationCallOrder[0]).toBeLessThan(
      mfa.enroll.mock.invocationCallOrder[0],
    );
  });

  it.each([
    "",
    "data:image/svg+xml;utf-8,   ",
    "data:image/svg+xml-bad,<svg></svg>",
    "not-an-svg",
    null,
  ])(
    "fails safely and removes the incomplete factor for malformed QR source %j",
    async (qrCode) => {
      const secret = "MALFORMEDQRSECRET";
      const consoleError = vi
        .spyOn(console, "error")
        .mockImplementation(() => undefined);
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
          id: "invalid-qr-factor",
          type: "totp",
          totp: { qr_code: qrCode, secret, uri: "otpauth://malformed" },
        },
        error: null,
      });
      mfa.unenroll.mockResolvedValue({ data: {}, error: null });
      const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
      render(<MfaEnrollment returnTo="/admin" />);

      fireEvent.click(
        await screen.findByRole("button", { name: /begin totp enrollment/i }),
      );

      expect(await screen.findByRole("alert")).toHaveTextContent(
        /multi-factor authentication could not be completed/i,
      );
      expect(
        screen.queryByAltText("TOTP enrollment QR code"),
      ).not.toBeInTheDocument();
      expect(screen.queryByText(secret)).not.toBeInTheDocument();
      expect(mfa.unenroll).toHaveBeenCalledWith({
        factorId: "invalid-qr-factor",
      });
      expect(JSON.stringify(consoleError.mock.calls)).not.toContain(secret);
      consoleError.mockRestore();
    },
  );

  it("keeps verification failures bounded without logging the setup secret", async () => {
    const secret = "PRIVATESETUPKEY";
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => undefined);
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
        id: "verification-factor",
        type: "totp",
        totp: {
          qr_code: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
          secret,
          uri: "otpauth://verification",
        },
      },
      error: null,
    });
    mfa.challengeAndVerify.mockResolvedValue({
      data: null,
      error: { message: `provider failure ${secret}` },
    });
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(<MfaEnrollment returnTo="/admin" />);

    fireEvent.click(
      await screen.findByRole("button", { name: /begin totp enrollment/i }),
    );
    fireEvent.change(
      await screen.findByLabelText(/six-digit authenticator code/i),
      {
        target: { value: "123456" },
      },
    );
    fireEvent.click(
      screen.getByRole("button", { name: /verify authenticator/i }),
    );

    const error = await screen.findByRole("alert");
    expect(error).toHaveTextContent(/verification code was not accepted/i);
    expect(error).not.toHaveTextContent(secret);
    expect(JSON.stringify(consoleError.mock.calls)).not.toContain(secret);
    consoleError.mockRestore();
  });

  it("recognizes an already-AAL2 session without changing factors", async () => {
    mfa.getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal2", nextLevel: "aal2" },
      error: null,
    });
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(<MfaEnrollment returnTo="/admin" />);

    expect(
      await screen.findByRole("link", { name: /continue to administration/i }),
    ).toBeInTheDocument();
    expect(mfa.listFactors).not.toHaveBeenCalled();
    expect(mfa.enroll).not.toHaveBeenCalled();
  });

  it("bounds provider failures without exposing provider payloads", async () => {
    mfa.getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: null,
      error: { message: "raw provider payload" },
    });
    const { MfaEnrollment } = await import("@/app/auth/mfa/mfa-enrollment");
    render(<MfaEnrollment returnTo="/admin" />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /multi-factor authentication is unavailable/i,
    );
    expect(screen.queryByText(/raw provider payload/i)).not.toBeInTheDocument();
  });
});
