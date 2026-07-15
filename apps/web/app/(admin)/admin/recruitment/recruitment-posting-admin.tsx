"use client";

import { useState } from "react";
import { Button, ErrorSummary, FormField, StatusBadge } from "@keeper/ui";
import { adminBrowserRequest } from "@/lib/admin-browser-api";
import type { AdminPosting } from "@/lib/recruitment-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

export function RecruitmentPostingAdmin({
  initialPostings,
  requester = adminBrowserRequest,
}: {
  initialPostings: AdminPosting[];
  requester?: Requester;
}) {
  const [postings, setPostings] = useState(initialPostings);
  const [editing, setEditing] = useState<AdminPosting | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice(editing ? "Saving posting changes…" : "Creating draft…");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      slug: String(form.get("slug") ?? "").trim(),
      title: String(form.get("title") ?? "").trim(),
      summary: String(form.get("summary") ?? "").trim(),
      body: String(form.get("body") ?? "").trim(),
    };
    try {
      const response = await requester(
        editing
          ? `/api/v1/admin/recruitment-postings/${editing.id}`
          : "/api/v1/admin/recruitment-postings",
        {
          method: editing ? "PATCH" : "POST",
          body: JSON.stringify(payload),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("posting rejected");
      const posting = (await response.json()) as AdminPosting;
      setPostings((items) => {
        const exists = items.some((item) => item.id === posting.id);
        return exists
          ? items.map((item) => (item.id === posting.id ? posting : item))
          : [posting, ...items];
      });
      setEditing(null);
      formElement.reset();
      setNotice(editing ? "Posting changes saved." : "Draft created.");
    } catch {
      setErrors([
        "The posting was not saved. Check bounded plain-text fields, the slug, and your administration access.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function transition(
    posting: AdminPosting,
    action: "publish" | "close" | "archive",
  ) {
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice(
      `${action === "publish" ? "Publishing" : action === "close" ? "Closing" : "Archiving"} posting…`,
    );
    try {
      const response = await requester(
        `/api/v1/admin/recruitment-postings/${posting.id}/${action}`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error("transition rejected");
      const updated = (await response.json()) as AdminPosting;
      setPostings((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
      setNotice(
        `Posting ${action === "publish" ? "published" : action === "close" ? "closed" : "archived"}.`,
      );
    } catch {
      setErrors([
        "The lifecycle action was rejected. Refresh before trying another valid transition.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-recruitment">
      <p role="status" aria-live="polite">
        {notice}
      </p>
      <ErrorSummary errors={errors} />
      <form
        className="card"
        onSubmit={save}
        aria-busy={busy}
        key={editing?.id ?? "new"}
      >
        <h2>{editing ? "Edit posting" : "Create recruitment posting"}</h2>
        <p>
          Postings use bounded plain text. HTML and hard deletion are
          unavailable.
        </p>
        <FormField
          id="posting-slug"
          label="Slug (required)"
          hint="Lowercase words separated by hyphens."
        >
          <input
            id="posting-slug"
            name="slug"
            pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
            maxLength={100}
            defaultValue={editing?.slug ?? ""}
            required
          />
        </FormField>
        <FormField id="posting-title" label="Title (required)">
          <input
            id="posting-title"
            name="title"
            maxLength={160}
            defaultValue={editing?.title ?? ""}
            required
          />
        </FormField>
        <FormField id="posting-summary" label="Summary (required)">
          <textarea
            id="posting-summary"
            name="summary"
            maxLength={500}
            defaultValue={editing?.summary ?? ""}
            required
          />
        </FormField>
        <FormField
          id="posting-body"
          label="Plain-text description (required)"
          hint="No HTML or rich text."
        >
          <textarea
            id="posting-body"
            name="body"
            maxLength={5000}
            defaultValue={editing?.body ?? ""}
            required
          />
        </FormField>
        <div className="button-row">
          <Button type="submit" disabled={busy}>
            {editing ? "Save posting changes" : "Create draft"}
          </Button>
          {editing ? (
            <Button
              type="button"
              onClick={() => setEditing(null)}
              disabled={busy}
            >
              Cancel editing
            </Button>
          ) : null}
        </div>
      </form>
      <section aria-labelledby="posting-list-heading">
        <h2 id="posting-list-heading">Recruitment postings</h2>
        {postings.length === 0 ? (
          <p>No recruitment postings have been created.</p>
        ) : (
          <div className="grid-2">
            {postings.map((posting) => (
              <article className="card" key={posting.id}>
                <h3>{posting.title}</h3>
                <p>
                  Status: <StatusBadge>{posting.status}</StatusBadge>
                </p>
                <p>{posting.summary}</p>
                <p>Version {posting.version}</p>
                <div className="button-row">
                  {posting.status === "draft" ||
                  posting.status === "published" ? (
                    <Button
                      type="button"
                      onClick={() => setEditing(posting)}
                      disabled={busy}
                    >
                      Edit {posting.title}
                    </Button>
                  ) : null}
                  {posting.status === "draft" ? (
                    <Button
                      type="button"
                      onClick={() => transition(posting, "publish")}
                      disabled={busy}
                      aria-label={`Publish ${posting.title}`}
                    >
                      Publish
                    </Button>
                  ) : null}
                  {posting.status === "published" ? (
                    <Button
                      type="button"
                      onClick={() => transition(posting, "close")}
                      disabled={busy}
                      aria-label={`Close ${posting.title}`}
                    >
                      Close
                    </Button>
                  ) : null}
                  {posting.status === "draft" || posting.status === "closed" ? (
                    <Button
                      type="button"
                      onClick={() => transition(posting, "archive")}
                      disabled={busy}
                      aria-label={`Archive ${posting.title}`}
                    >
                      Archive
                    </Button>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
