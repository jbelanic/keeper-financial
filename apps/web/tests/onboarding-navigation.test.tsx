import { render, screen } from "@testing-library/react";

const requirePortalAccess = vi.fn();
const portalServerJson = vi.fn();

vi.mock("@/lib/require-portal-access", () => ({ requirePortalAccess }));
vi.mock("@/lib/review-onboarding-api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/review-onboarding-api")>()),
  portalServerJson,
}));

describe("onboarding portal navigation", () => {
  beforeEach(() => {
    requirePortalAccess.mockReset().mockResolvedValue(undefined);
    portalServerJson.mockReset();
  });

  it("shows candidate onboarding only for a current authorized assignment", async () => {
    portalServerJson.mockResolvedValue({ available: true });
    const { default: CandidateLayout } = await import(
      "@/app/(candidate)/layout"
    );
    render(await CandidateLayout({ children: <p>Candidate content</p> }));
    expect(requirePortalAccess).toHaveBeenCalledWith("candidate");
    expect(screen.getByRole("link", { name: "Onboarding" })).toHaveAttribute(
      "href",
      "/candidate/onboarding",
    );
    expect(portalServerJson).toHaveBeenCalledWith(
      "/api/v1/candidate/onboarding/availability",
    );
  });

  it("does not imply onboarding authorization without an assignment", async () => {
    portalServerJson.mockResolvedValue({ available: false });
    const { default: CandidateLayout } = await import(
      "@/app/(candidate)/layout"
    );
    render(await CandidateLayout({ children: <p>Candidate content</p> }));
    expect(screen.queryByRole("link", { name: "Onboarding" })).toBeNull();
    expect(portalServerJson).toHaveBeenCalledOnce();
  });

  it("renders no assignment as a stable candidate state", async () => {
    portalServerJson.mockResolvedValue({
      assignment: null,
      tasks: [],
      gates: [],
      documents: [],
      acknowledgements: [],
      esign_envelopes: [],
      activation_ready: false,
    });
    const { default: CandidateOnboardingPage } = await import(
      "@/app/(candidate)/candidate/onboarding/page"
    );
    render(await CandidateOnboardingPage());
    expect(
      screen.getByText(/onboarding is not available yet/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /return to your applications/i }),
    ).toHaveAttribute("href", "/candidate/application");
    expect(portalServerJson).toHaveBeenCalledOnce();
  });

  it("offers one manual retry for a transient onboarding fetch failure", async () => {
    portalServerJson.mockResolvedValue(null);
    const { default: CandidateOnboardingPage } = await import(
      "@/app/(candidate)/candidate/onboarding/page"
    );
    render(await CandidateOnboardingPage());
    expect(screen.getByRole("alert")).toHaveTextContent(
      /onboarding service could not be verified/i,
    );
    expect(
      screen.getByRole("link", { name: /try onboarding again/i }),
    ).toHaveAttribute("href", "/candidate/onboarding");
    expect(portalServerJson).toHaveBeenCalledOnce();
  });

  it("shows onboarding administration only after admin layout authorization", async () => {
    const { default: AdminLayout } = await import("@/app/(admin)/layout");
    render(await AdminLayout({ children: <p>Admin content</p> }));
    expect(requirePortalAccess).toHaveBeenCalledWith("admin");
    expect(screen.getByRole("link", { name: "Onboarding" })).toHaveAttribute(
      "href",
      "/admin/onboarding",
    );
  });
});
