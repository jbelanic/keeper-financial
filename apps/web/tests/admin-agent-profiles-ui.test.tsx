import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import type { components } from "@keeper/contracts";

type AdminAgentProfile = components["schemas"]["AdminAgentProfile"];

const draft = {
  id: "00000000-0000-4000-8000-000000000777",
  user_id: "00000000-0000-4000-8000-000000000778",
  slug: "synthetic-agent",
  licensed_name: "Synthetic Agent",
  approved_title: "Mortgage Agent Level 2",
  licence_number: "M00000000",
  biography: "Synthetic public-safe biography.",
  languages: ["English"],
  service_areas: ["London"],
  specialties: ["Purchases"],
  photo_url: null,
  photo_alt_text: null,
  public_email: "synthetic.agent@example.test",
  public_phone: "+1 555 010 0200",
  social_links: [],
  status: "draft",
  version: 1,
  slug_locked_at: null,
  created_at: "2026-07-16T12:00:00Z",
  updated_at: "2026-07-16T12:00:00Z",
  approved_at: null,
  published_at: null,
} satisfies AdminAgentProfile;

const eligibleAgents = [
  {
    user_id: draft.user_id,
    email: "synthetic.agent@example.test",
    display_name: "Synthetic Agent",
  },
];

describe("admin agent profile manager", () => {
  it("creates a bounded profile and can select it for editing", async () => {
    const requester = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => draft,
    });
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[]}
        initialEligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    fireEvent.change(screen.getByLabelText(/eligible agent/i), {
      target: { value: draft.user_id },
    });
    fireEvent.change(screen.getByLabelText(/^slug/i), {
      target: { value: draft.slug },
    });
    fireEvent.change(screen.getByLabelText(/licensed name/i), {
      target: { value: draft.licensed_name },
    });
    fireEvent.change(screen.getByLabelText(/approved title/i), {
      target: { value: draft.approved_title },
    });
    fireEvent.change(screen.getByLabelText(/licence number/i), {
      target: { value: draft.licence_number },
    });
    fireEvent.change(screen.getByLabelText(/biography/i), {
      target: { value: draft.biography },
    });
    fireEvent.change(screen.getByLabelText(/languages/i), {
      target: { value: "English" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /create draft profile/i }),
    );

    await waitFor(() => expect(requester).toHaveBeenCalledOnce());
    const payload = JSON.parse(String(requester.mock.calls[0][1].body));
    expect(payload).toMatchObject({
      user_id: draft.user_id,
      slug: draft.slug,
      licence_number: draft.licence_number,
      languages: ["English"],
    });
    expect(payload).not.toHaveProperty("status");
    expect(screen.getByRole("status")).toHaveTextContent(
      /draft profile created/i,
    );
    fireEvent.click(
      screen.getByRole("button", { name: /edit synthetic agent/i }),
    );
    expect(
      screen.getByRole("heading", { name: /edit agent profile/i }),
    ).toBeInTheDocument();
  });

  it("uses an accessible confirmation dialog and requires a suspension reason", async () => {
    const published = {
      ...draft,
      status: "published",
    } satisfies AdminAgentProfile;
    const suspended = {
      ...published,
      status: "suspended",
    } satisfies AdminAgentProfile;
    const requester = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => suspended,
    });
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[published]}
        initialEligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    const trigger = screen.getByRole("button", {
      name: /suspend synthetic agent/i,
    });
    trigger.focus();
    fireEvent.click(trigger);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("open");
    expect(
      within(dialog).getByRole("button", { name: "Cancel" }),
    ).toHaveFocus();
    expect(within(dialog).getByLabelText(/reason/i)).toBeRequired();
    fireEvent.change(within(dialog).getByLabelText(/reason/i), {
      target: { value: "Public profile review required." },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "Confirm" }));

    await waitFor(() => expect(requester).toHaveBeenCalledOnce());
    expect(requester.mock.calls[0][0]).toBe(
      `/api/v1/agents/${published.id}/status`,
    );
    expect(JSON.parse(String(requester.mock.calls[0][1].body))).toEqual({
      status: "suspended",
      reason: "Public profile review required.",
    });
    expect(screen.getByRole("status")).toHaveTextContent(/profile suspended/i);
  });

  it("offers explicit submit, publish, republish, and archive actions", async () => {
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    const { rerender } = render(
      <AgentProfileManager
        key="draft"
        initialProfiles={[draft]}
        initialEligibleAgents={eligibleAgents}
        requester={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", {
        name: /submit synthetic agent for approval/i,
      }),
    ).toBeInTheDocument();

    rerender(
      <AgentProfileManager
        key="pending"
        initialProfiles={[{ ...draft, status: "pending_approval" }]}
        initialEligibleAgents={eligibleAgents}
        requester={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /publish synthetic agent/i }),
    ).toBeInTheDocument();

    rerender(
      <AgentProfileManager
        key="suspended"
        initialProfiles={[{ ...draft, status: "suspended" }]}
        initialEligibleAgents={eligibleAgents}
        requester={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /republish synthetic agent/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /archive synthetic agent/i }),
    ).toBeInTheDocument();
  });
});
