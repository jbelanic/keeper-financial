import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { AdminPosting } from "@/lib/recruitment-api";

const draft = {
  id: "00000000-0000-4000-8000-000000000444",
  slug: "synthetic-opportunity",
  title: "Synthetic opportunity",
  summary: "Synthetic summary",
  body: "Synthetic plain-text body",
  status: "draft",
  version: 1,
  published_at: null,
  closed_at: null,
  archived_at: null,
  created_at: "2026-07-15T12:00:00Z",
  updated_at: "2026-07-15T12:00:00Z",
} satisfies AdminPosting;

describe("admin recruitment posting UI", () => {
  it("creates bounded plain-text postings and prevents duplicate actions", async () => {
    const requester = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => draft,
    });
    const { RecruitmentPostingAdmin } = await import(
      "@/app/(admin)/admin/recruitment/recruitment-posting-admin"
    );
    render(
      <RecruitmentPostingAdmin initialPostings={[]} requester={requester} />,
    );
    fireEvent.change(screen.getByLabelText(/slug/i), {
      target: { value: draft.slug },
    });
    fireEvent.change(screen.getByLabelText(/^title/i), {
      target: { value: draft.title },
    });
    fireEvent.change(screen.getByLabelText(/summary/i), {
      target: { value: draft.summary },
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: draft.body },
    });
    fireEvent.click(screen.getByRole("button", { name: /create draft/i }));
    await waitFor(() => expect(requester).toHaveBeenCalledOnce());
    expect(JSON.parse(String(requester.mock.calls[0][1].body))).toEqual({
      slug: draft.slug,
      title: draft.title,
      summary: draft.summary,
      body: draft.body,
    });
    expect(screen.getByRole("status")).toHaveTextContent(/draft created/i);
  });

  it("offers only explicit lifecycle actions and announces publication", async () => {
    const requester = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        ...draft,
        status: "published",
        published_at: "2026-07-15T12:05:00Z",
      }),
    });
    const { RecruitmentPostingAdmin } = await import(
      "@/app/(admin)/admin/recruitment/recruitment-posting-admin"
    );
    render(
      <RecruitmentPostingAdmin
        initialPostings={[draft]}
        requester={requester}
      />,
    );
    expect(screen.queryByRole("button", { name: /delete/i })).toBeNull();
    fireEvent.click(
      screen.getByRole("button", { name: /publish synthetic opportunity/i }),
    );
    await waitFor(() => expect(requester).toHaveBeenCalledOnce());
    expect(requester.mock.calls[0][0]).toMatch(/\/publish$/);
    expect(screen.getByRole("status")).toHaveTextContent(/posting published/i);
  });
});
