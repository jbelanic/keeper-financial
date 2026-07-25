import {
  BorrowerApplicationError,
  getBorrowerDraft,
  patchBorrowerDraft,
  recoverOrStartBorrowerDraft,
  startBorrowerDraft,
} from "@/lib/borrower-application-api";

const applicationId = "11111111-1111-4111-8111-111111111111";

describe("borrower application API client", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("starts through same-origin no-store credentialed requests with CSRF", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          application_id: applicationId,
          revision: 0,
          lifecycle_status: "draft",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    );

    await expect(startBorrowerDraft()).resolves.toMatchObject({
      application_id: applicationId,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/borrower-applications/start",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        cache: "no-store",
      }),
    );
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(new Headers(init.headers).get("X-Keeper-Borrower-CSRF")).toBe("1");
    expect(fetchMock.mock.calls[0][0]).not.toContain(applicationId);
  });

  it("patches an exact draft revision without persisting payload or SIN", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          application_id: applicationId,
          revision: 2,
          lifecycle_status: "draft",
          has_sin: true,
          has_co_borrower: false,
          last_activity_at: "2026-07-25T12:00:00Z",
          draft_expires_at: "2026-08-24T12:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const syntheticSin = "046454286";

    await patchBorrowerDraft(applicationId, 1, {
      primary_borrower: { sin: syntheticSin },
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(String(init?.body))).toEqual({
      expected_revision: 1,
      payload: { primary_borrower: { sin: syntheticSin } },
    });
    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
    expect(window.location.href).not.toContain(syntheticSin);
  });

  it("recovers only by opaque ID and server capability state", async () => {
    window.sessionStorage.setItem(
      "keeper.borrower.application-id",
      applicationId,
    );
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          application_id: applicationId,
          revision: 3,
          lifecycle_status: "draft",
          has_sin: true,
          has_co_borrower: true,
          last_activity_at: "2026-07-25T12:00:00Z",
          draft_expires_at: "2026-08-24T12:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    await expect(recoverOrStartBorrowerDraft()).resolves.toMatchObject({
      recovered: true,
      draft: { has_sin: true },
    });
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][0]).toBe(
      `/api/v1/borrower-applications/${applicationId}`,
    );
    expect(
      window.sessionStorage.getItem("keeper.borrower.application-id"),
    ).toBe(applicationId);
  });

  it("returns bounded validation errors without exposing response text", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: [
            {
              loc: ["body", "payload", "primary_borrower", "sin"],
              msg: "Value is invalid",
              input: "must-not-be-copied",
            },
          ],
        }),
        { status: 422, headers: { "Content-Type": "application/json" } },
      ),
    );

    await expect(getBorrowerDraft(applicationId)).rejects.toMatchObject({
      status: 422,
      issues: [
        {
          path: ["body", "payload", "primary_borrower", "sin"],
          message: "Value is invalid",
        },
      ],
    } satisfies Partial<BorrowerApplicationError>);
  });
});
