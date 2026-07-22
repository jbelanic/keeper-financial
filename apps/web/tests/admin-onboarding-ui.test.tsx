import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

const assignment = {
  assignment_id: "00000000-0000-4000-8000-000000000901",
  candidate_id: "00000000-0000-4000-8000-000000000902",
  application_id: "00000000-0000-4000-8000-000000000903",
  candidate_name: "Synthetic Candidate",
  candidate_email: "candidate@example.test",
  opportunity_title: "Mortgage Agent Opportunity",
  attempt_number: 2,
  plan_name: "Ontario agent onboarding",
  status: "active" as const,
  created_at: "2026-07-19T12:00:00Z",
  activation_ready: false,
};

describe("administrator onboarding workspace", () => {
  it("issues the agreement and explicitly completes a ready assignment", async () => {
    const detail = {
      ...assignment,
      activation_ready: true,
      tasks: [],
      gates: [],
      esign_envelopes: [],
    };
    const issued = {
      id: "00000000-0000-4000-8000-000000000990",
      candidate_id: assignment.candidate_id,
      assignment_id: assignment.assignment_id,
      provider: "documenso",
      status: "sent",
      envelope_id: "provider-envelope",
      envelope_url: "https://sign.keeperfinancial.ca/sign/provider-envelope",
      last_synced_at: "2026-07-20T12:00:00Z",
      superseded_at: null,
      replacement_envelope_id: null,
      created_at: "2026-07-20T12:00:00Z",
    };
    const requester = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => detail })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => issued,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...detail, esign_envelopes: [issued] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "completed" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...detail, status: "completed" }),
      });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const { OnboardingAdmin } = await import(
      "@/app/(admin)/admin/onboarding/onboarding-admin"
    );
    render(
      <OnboardingAdmin
        initialPlans={[]}
        initialAssignments={[assignment]}
        requester={requester}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Manage active assignment" }),
    );
    expect(
      await screen.findByRole("button", { name: "Send contractor agreement" }),
    ).toBeInTheDocument();
    expect(screen.getByText("candidate@example.test")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Send contractor agreement" }),
    );
    await waitFor(() =>
      expect(requester).toHaveBeenCalledWith(
        `/api/v1/admin/onboarding/assignments/${assignment.assignment_id}/esign-envelopes/issue-ica`,
        { method: "POST" },
      ),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Complete onboarding and enable agent",
      }),
    );
    await waitFor(() =>
      expect(requester).toHaveBeenCalledWith(
        `/api/v1/admin/onboarding/assignments/${assignment.assignment_id}/complete`,
        { method: "POST" },
      ),
    );
    expect(
      await screen.findByRole("link", { name: /agent profiles/i }),
    ).toHaveAttribute("href", "/admin/agents");
  });

  it("shows the recognized completion conflict instead of blaming green readiness", async () => {
    const detail = {
      ...assignment,
      activation_ready: true,
      tasks: [],
      gates: [],
      esign_envelopes: [],
    };
    const requester = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => detail })
      .mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({ detail: "the agent role is not configured" }),
      });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const { OnboardingAdmin } = await import(
      "@/app/(admin)/admin/onboarding/onboarding-admin"
    );
    render(
      <OnboardingAdmin
        initialPlans={[]}
        initialAssignments={[assignment]}
        requester={requester}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Manage active assignment" }),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Complete onboarding and enable agent",
      }),
    );

    expect(
      await screen.findByText(
        "Agent access is not configured. Apply current database migrations and retry.",
      ),
    ).toBeInTheDocument();
  });

  it("reissues a rejected Keeper agreement through the bounded issuance endpoint", async () => {
    const rejected = {
      id: "00000000-0000-4000-8000-000000000990",
      candidate_id: assignment.candidate_id,
      assignment_id: assignment.assignment_id,
      provider: "documenso",
      status: "rejected",
      envelope_id: "rejected-envelope",
      envelope_url: "https://sign.keeperfinancial.ca/sign/rejected-envelope",
      last_synced_at: "2026-07-20T12:00:00Z",
      superseded_at: null,
      replacement_envelope_id: null,
      created_at: "2026-07-20T12:00:00Z",
    };
    const detail = {
      ...assignment,
      tasks: [],
      gates: [],
      esign_envelopes: [rejected],
    };
    const requester = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => detail })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => rejected,
      })
      .mockResolvedValueOnce({ ok: true, json: async () => detail });
    const { OnboardingAdmin } = await import(
      "@/app/(admin)/admin/onboarding/onboarding-admin"
    );
    render(
      <OnboardingAdmin
        initialPlans={[]}
        initialAssignments={[assignment]}
        requester={requester}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Manage active assignment" }),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Resend contractor agreement",
      }),
    );

    await waitFor(() =>
      expect(requester).toHaveBeenCalledWith(
        `/api/v1/admin/onboarding/assignments/${assignment.assignment_id}/esign-envelopes/issue-ica`,
        { method: "POST" },
      ),
    );
  });

  it("authors and reorders tasks when creating an editable unused plan", async () => {
    const created = {
      id: "00000000-0000-4000-8000-000000000904",
      name: "Ontario agent onboarding",
      description: "Synthetic plan",
      is_active: true,
      is_locked: false,
      created_at: "2026-07-19T12:00:00Z",
      updated_at: "2026-07-19T12:00:00Z",
      tasks: [
        {
          id: "00000000-0000-4000-8000-000000000905",
          plan_id: "00000000-0000-4000-8000-000000000904",
          title: "Second task",
          instructions: "",
          sequence: 1,
          is_required: true,
        },
        {
          id: "00000000-0000-4000-8000-000000000906",
          plan_id: "00000000-0000-4000-8000-000000000904",
          title: "First task",
          instructions: "",
          sequence: 2,
          is_required: true,
        },
      ],
    };
    const requester = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => created,
    });
    const { OnboardingAdmin } = await import(
      "@/app/(admin)/admin/onboarding/onboarding-admin"
    );
    render(
      <OnboardingAdmin
        initialPlans={[]}
        initialAssignments={[assignment]}
        requester={requester}
      />,
    );

    expect(screen.queryByLabelText(/candidate id/i)).not.toBeInTheDocument();
    expect(screen.getByText("Synthetic Candidate")).toBeInTheDocument();
    expect(
      screen.getByText(/Mortgage Agent Opportunity — attempt 2/i),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/plan name/i), {
      target: { value: created.name },
    });
    fireEvent.change(screen.getByLabelText("Task title (required)"), {
      target: { value: "First task" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add task" }));
    const titles = screen.getAllByLabelText("Task title (required)");
    fireEvent.change(titles[1], { target: { value: "Second task" } });
    const moveUpButtons = screen.getAllByRole("button", { name: "Move up" });
    fireEvent.click(moveUpButtons[1]);
    fireEvent.click(screen.getByRole("button", { name: "Create plan" }));

    await waitFor(() => expect(requester).toHaveBeenCalledOnce());
    expect(requester.mock.calls[0][0]).toBe("/api/v1/admin/onboarding/plans");
    const payload = JSON.parse(String(requester.mock.calls[0][1].body));
    expect(payload.tasks.map((task: { title: string }) => task.title)).toEqual([
      "Second task",
      "First task",
    ]);
    expect(screen.getByRole("status")).toHaveTextContent(
      /onboarding plan created/i,
    );
  });

  it("explains draft task removal and confirms the unsaved change", async () => {
    const { OnboardingAdmin } = await import(
      "@/app/(admin)/admin/onboarding/onboarding-admin"
    );
    render(
      <OnboardingAdmin
        initialPlans={[]}
        initialAssignments={[]}
        requester={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/at least one task is required/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/task changes are not persisted until/i),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add task" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Remove task" })[1]);

    expect(screen.getAllByLabelText("Task title (required)")).toHaveLength(1);
    expect(screen.getByRole("status")).toHaveTextContent(
      /task removed from the draft/i,
    );
  });

  it("edits an unused plan and exposes referenced plans as locked", async () => {
    const editablePlan = {
      id: "00000000-0000-4000-8000-000000000910",
      name: "Editable plan",
      description: "Before first use",
      is_active: true,
      is_locked: false,
    };
    const lockedPlan = {
      id: "00000000-0000-4000-8000-000000000920",
      name: "Referenced plan",
      description: "Already assigned",
      is_active: true,
      is_locked: true,
    };
    const detail = {
      ...editablePlan,
      created_at: "2026-07-19T12:00:00Z",
      updated_at: "2026-07-19T12:00:00Z",
      tasks: [
        {
          id: "00000000-0000-4000-8000-000000000911",
          plan_id: editablePlan.id,
          title: "Original task",
          instructions: "Original instructions",
          sequence: 1,
          is_required: true,
        },
      ],
    };
    const requester = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => detail,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          ...detail,
          name: "Revised editable plan",
          tasks: [{ ...detail.tasks[0], title: "Revised task" }],
        }),
      });
    const { OnboardingAdmin } = await import(
      "@/app/(admin)/admin/onboarding/onboarding-admin"
    );
    render(
      <OnboardingAdmin
        initialPlans={[editablePlan, lockedPlan]}
        initialAssignments={[]}
        requester={requester}
      />,
    );

    const lockedCard = screen
      .getByRole("heading", { name: lockedPlan.name })
      .closest("li");
    expect(lockedCard).not.toBeNull();
    expect(
      within(lockedCard!).getByText(/locked after first assignment/i),
    ).toBeInTheDocument();
    expect(
      within(lockedCard!).queryByRole("button", { name: /deactivate/i }),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Edit plan" }));
    await waitFor(() =>
      expect(screen.getByLabelText(/plan name/i)).toHaveValue(
        editablePlan.name,
      ),
    );
    fireEvent.change(screen.getByLabelText(/plan name/i), {
      target: { value: "Revised editable plan" },
    });
    fireEvent.change(screen.getByLabelText("Task title (required)"), {
      target: { value: "Revised task" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save plan changes" }));

    await waitFor(() => expect(requester).toHaveBeenCalledTimes(2));
    expect(requester.mock.calls[1][0]).toBe(
      `/api/v1/admin/onboarding/plans/${editablePlan.id}`,
    );
    expect(requester.mock.calls[1][1].method).toBe("PATCH");
    const payload = JSON.parse(String(requester.mock.calls[1][1].body));
    expect(payload.tasks[0].title).toBe("Revised task");
    expect(screen.getByRole("status")).toHaveTextContent(
      /unused onboarding plan updated/i,
    );
  });

  it("labels active and historical assignments without offering historical mutation", async () => {
    const historical = {
      ...assignment,
      assignment_id: "00000000-0000-4000-8000-000000000930",
      status: "superseded" as const,
      activation_ready: false,
    };
    const { OnboardingAdmin } = await import(
      "@/app/(admin)/admin/onboarding/onboarding-admin"
    );

    render(
      <OnboardingAdmin
        initialPlans={[]}
        initialAssignments={[assignment, historical]}
        requester={vi.fn()}
      />,
    );

    const activeCard = screen
      .getAllByText("Synthetic Candidate")[0]
      .closest("li");
    const historicalCard = screen
      .getAllByText("Synthetic Candidate")[1]
      .closest("li");
    expect(activeCard).not.toBeNull();
    expect(historicalCard).not.toBeNull();
    expect(
      within(activeCard!).getByText("Active assignment"),
    ).toBeInTheDocument();
    expect(
      within(activeCard!).getByRole("button", {
        name: "Manage active assignment",
      }),
    ).toBeInTheDocument();
    expect(
      within(historicalCard!).getByText("Superseded assignment"),
    ).toBeInTheDocument();
    expect(
      within(historicalCard!).getByRole("button", {
        name: "View assignment history",
      }),
    ).toBeInTheDocument();
    expect(
      within(historicalCard!).queryByText("not activation-ready"),
    ).not.toBeInTheDocument();
  });
});
