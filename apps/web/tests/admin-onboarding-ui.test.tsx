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
