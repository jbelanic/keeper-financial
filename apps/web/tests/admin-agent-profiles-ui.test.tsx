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

    // The list owns the page; the create form is opened explicitly.
    expect(screen.queryByLabelText(/eligible agent/i)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Create new profile" }));
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

  it("lists profiles first and opens editing from the list", async () => {
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[draft]}
        initialEligibleAgents={eligibleAgents}
        requester={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Create new profile" }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/eligible agent/i)).toBeNull();

    fireEvent.click(
      screen.getByRole("button", { name: /edit synthetic agent/i }),
    );
    expect(
      screen.getByRole("heading", { name: /edit agent profile/i }),
    ).toBeInTheDocument();
    // The operator edits the published phone number in its display form.
    expect(screen.getByLabelText(/approved public phone/i)).toHaveValue(
      "(555) 010-0200",
    );
    expect(
      screen.getByText(/shown on the public profile as \(519\) 123-4567/i),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cancel editing" }));
    expect(
      screen.queryByRole("heading", { name: /edit agent profile/i }),
    ).toBeNull();
  });

  it("explains when no eligible agent is available for a new profile", async () => {
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[draft]}
        initialEligibleAgents={[]}
        requester={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Create new profile" }),
    ).toBeDisabled();
    expect(
      screen.getByText(/every agent already has one/i),
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

  it("uploads a photo through Keeper and submits the stored URL", async () => {
    const storedPhotoUrl = `https://keeperfinancial.ca/api/v1/agent-photos/${"a".repeat(32)}.jpg`;
    const requester = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ photo_url: storedPhotoUrl }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({
          ...draft,
          photo_url: storedPhotoUrl,
          photo_alt_text: "Synthetic Agent at a desk",
        }),
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

    fireEvent.click(screen.getByRole("button", { name: "Create new profile" }));
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

    const photo = new File(
      [new Uint8Array([0xff, 0xd8, 0xff])],
      "headshot.jpg",
      {
        type: "image/jpeg",
      },
    );
    fireEvent.change(screen.getByLabelText(/approved photo/i), {
      target: { files: [photo] },
    });

    await waitFor(() => expect(requester).toHaveBeenCalledTimes(1));
    expect(requester.mock.calls[0][0]).toBe("/api/v1/admin/agent-photos");
    expect(requester.mock.calls[0][1].method).toBe("POST");
    expect(requester.mock.calls[0][1].body).toBeInstanceOf(FormData);
    expect((requester.mock.calls[0][1].body as FormData).get("file")).toBe(
      photo,
    );
    await screen.findByText(/photo stored/i);

    fireEvent.change(screen.getByLabelText(/photo alternative text/i), {
      target: { value: "Synthetic Agent at a desk" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /create draft profile/i }),
    );

    await waitFor(() => expect(requester).toHaveBeenCalledTimes(2));
    const payload = JSON.parse(String(requester.mock.calls[1][1].body));
    expect(payload.photo_url).toBe(storedPhotoUrl);
    expect(payload.photo_alt_text).toBe("Synthetic Agent at a desk");
  });

  it("reports a rejected photo and never submits an image URL", async () => {
    const requester = vi.fn().mockResolvedValue({
      ok: false,
      status: 415,
      json: async () => ({ detail: "photo type is unsupported" }),
    });
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[draft]}
        initialEligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /edit synthetic agent/i }),
    );
    const photo = new File([new Uint8Array([0x25, 0x50])], "headshot.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(screen.getByLabelText(/approved photo/i), {
      target: { files: [photo] },
    });

    await screen.findByText(/the photo was not uploaded/i);
    expect(screen.queryByRole("button", { name: /remove photo/i })).toBeNull();

    fireEvent.click(
      screen.getByRole("button", { name: /save profile changes/i }),
    );
    await waitFor(() => expect(requester).toHaveBeenCalledTimes(2));
    const payload = JSON.parse(String(requester.mock.calls[1][1].body));
    expect(payload.photo_url).toBeNull();
    expect(payload.photo_alt_text).toBeNull();
  });

  it("surfaces the API's validation message instead of a catch-all", async () => {
    const requester = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [
          {
            loc: ["body", "photo_url"],
            msg: "URL must be HTTPS, or the loopback photo URL returned by the Keeper upload",
          },
        ],
      }),
    });
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[draft]}
        initialEligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /edit synthetic agent/i }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /save profile changes/i }),
    );

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The profile was not saved.");
    // The operator sees why, not just "something went wrong".
    expect(alert).toHaveTextContent("URL must be HTTPS");
    // ...and which field the rejection belongs to.
    expect(alert).toHaveTextContent("Photo: URL must be HTTPS");
  });

  it("saves several approved social links, including a bare pasted URL", async () => {
    const saved = {
      ...draft,
      social_links: [
        {
          label: "linkedin.com",
          url: "https://www.linkedin.com/in/synthetic-agent",
        },
        { label: "Instagram", url: "https://instagram.com/synthetic.agent" },
      ],
    } satisfies AdminAgentProfile;
    const requester = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => saved,
    });
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[draft]}
        initialEligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /edit synthetic agent/i }),
    );
    fireEvent.change(screen.getByLabelText(/approved social links/i), {
      target: {
        value:
          "https://www.linkedin.com/in/synthetic-agent\nInstagram | https://instagram.com/synthetic.agent",
      },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /save profile changes/i }),
    );

    await waitFor(() => expect(requester).toHaveBeenCalledOnce());
    const payload = JSON.parse(String(requester.mock.calls[0][1].body));
    expect(payload.social_links).toEqual([
      {
        label: "linkedin.com",
        url: "https://www.linkedin.com/in/synthetic-agent",
      },
      { label: "Instagram", url: "https://instagram.com/synthetic.agent" },
    ]);
    expect(screen.getByRole("status")).toHaveTextContent(
      /profile changes saved/i,
    );
  });

  it("names the social-link line that is wrong and never calls the API", async () => {
    const requester = vi.fn();
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[draft]}
        initialEligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /edit synthetic agent/i }),
    );
    fireEvent.change(screen.getByLabelText(/approved social links/i), {
      target: {
        value:
          "LinkedIn | https://www.linkedin.com/in/synthetic-agent\nInstagram |",
      },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /save profile changes/i }),
    );

    const alert = await screen.findByRole("alert");
    // The rejected line is named, not just "String should have at least 1 character".
    expect(alert).toHaveTextContent("Social links, line 2");
    expect(requester).not.toHaveBeenCalled();
  });

  it("rejects a social link that is not an https link, naming the line", async () => {
    const requester = vi.fn();
    const { AgentProfileManager } = await import(
      "@/app/(admin)/admin/agents/agent-profile-manager"
    );
    render(
      <AgentProfileManager
        initialProfiles={[draft]}
        initialEligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /edit synthetic agent/i }),
    );
    fireEvent.change(screen.getByLabelText(/approved social links/i), {
      target: { value: "linkedin.com/in/synthetic-agent" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /save profile changes/i }),
    );

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Social links, line 1");
    expect(alert).toHaveTextContent("https://");
    expect(requester).not.toHaveBeenCalled();
  });
});
