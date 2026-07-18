"use client";

import { useRef, useState } from "react";
import {
  Button,
  ConfirmationDialog,
  ErrorSummary,
  FormField,
  StatusBadge,
} from "@keeper/ui";
import type { AdminAgentProfile } from "@/lib/agent-api";
import { adminBrowserRequest } from "@/lib/admin-browser-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;
type TransitionTarget =
  | "pending_approval"
  | "published"
  | "suspended"
  | "archived";

type PendingAction = {
  profile: AdminAgentProfile;
  target: TransitionTarget;
  label: string;
} | null;

function commaList(value: FormDataEntryValue | null): string[] {
  return String(value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function socialLinks(value: FormDataEntryValue | null) {
  return String(value ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [label, ...url] = line.split("|");
      return { label: label.trim(), url: url.join("|").trim() };
    });
}

function optionalValue(value: FormDataEntryValue | null): string | null {
  const normalized = String(value ?? "").trim();
  return normalized || null;
}

export function AgentProfileManager({
  initialProfiles,
  requester = adminBrowserRequest,
}: {
  initialProfiles: AdminAgentProfile[];
  requester?: Requester;
}) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [editing, setEditing] = useState<AdminAgentProfile | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const actionTriggerRef = useRef<HTMLButtonElement | null>(null);

  function restoreActionFocus() {
    requestAnimationFrame(() => actionTriggerRef.current?.focus());
  }

  function closeDialog() {
    if (busy) return;
    setPendingAction(null);
    setReason("");
    restoreActionFocus();
  }

  function startAction(
    event: React.MouseEvent<HTMLButtonElement>,
    profile: AdminAgentProfile,
    target: TransitionTarget,
    label: string,
  ) {
    actionTriggerRef.current = event.currentTarget;
    setErrors([]);
    setReason("");
    setPendingAction({ profile, target, label });
  }

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice(editing ? "Saving profile changes…" : "Creating draft profile…");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      ...(!editing
        ? { user_id: String(form.get("user_id") ?? "").trim() }
        : {}),
      slug: String(form.get("slug") ?? "").trim(),
      licensed_name: String(form.get("licensed_name") ?? "").trim(),
      approved_title: String(form.get("approved_title") ?? "").trim(),
      licence_number: String(form.get("licence_number") ?? "").trim(),
      biography: String(form.get("biography") ?? "").trim(),
      languages: commaList(form.get("languages")),
      service_areas: commaList(form.get("service_areas")),
      specialties: commaList(form.get("specialties")),
      photo_url: optionalValue(form.get("photo_url")),
      photo_alt_text: optionalValue(form.get("photo_alt_text")),
      public_email: optionalValue(form.get("public_email")),
      public_phone: optionalValue(form.get("public_phone")),
      social_links: socialLinks(form.get("social_links")),
    };
    try {
      const response = await requester(
        editing
          ? `/api/v1/admin/agent-profiles/${editing.id}`
          : "/api/v1/admin/agent-profiles",
        {
          method: editing ? "PATCH" : "POST",
          body: JSON.stringify(payload),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("profile rejected");
      const profile = (await response.json()) as AdminAgentProfile;
      setProfiles((items) => {
        const exists = items.some((item) => item.id === profile.id);
        return exists
          ? items.map((item) => (item.id === profile.id ? profile : item))
          : [profile, ...items];
      });
      setEditing(null);
      formElement.reset();
      setNotice(
        editing
          ? "Profile changes saved for approval."
          : "Draft profile created.",
      );
    } catch {
      setErrors([
        "The profile was not saved. Check the active agent relationship, bounded public fields, HTTPS links, and your administration access.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function confirmTransition() {
    if (!pendingAction || busy) return;
    if (pendingAction.target === "suspended" && !reason.trim()) {
      setErrors(["A reason is required to suspend a public profile."]);
      return;
    }
    setBusy(true);
    setErrors([]);
    setNotice(`${pendingAction.label}…`);
    try {
      const response = await requester(
        `/api/v1/agents/${pendingAction.profile.id}/status`,
        {
          method: "POST",
          body: JSON.stringify({
            status: pendingAction.target,
            ...(pendingAction.target === "suspended"
              ? { reason: reason.trim() }
              : {}),
          }),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("transition rejected");
      const result = (await response.json()) as {
        status: AdminAgentProfile["status"];
      };
      setProfiles((items) =>
        items.map((item) =>
          item.id === pendingAction.profile.id
            ? { ...item, status: result.status }
            : item,
        ),
      );
      setNotice(`Profile ${result.status.replace("_", " ")}.`);
      setPendingAction(null);
      setReason("");
      restoreActionFocus();
    } catch {
      setErrors([
        "The lifecycle action was rejected. Refresh the profile and use an allowed transition.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-agent-manager">
      <p role="status" aria-live="polite">
        {notice}
      </p>
      <ErrorSummary errors={errors} />

      <form
        className="card agent-profile-form"
        onSubmit={save}
        aria-busy={busy}
        key={editing?.id ?? "new-agent-profile"}
      >
        <h2>{editing ? "Edit agent profile" : "Create agent profile"}</h2>
        <p>
          Only approved public profile and regulatory information belongs here.
          Do not enter borrower, underwriting, identity-document, or financial
          data.
        </p>
        <div className="form-grid">
          <FormField
            id="agent-user-id"
            label="Agent user ID (required)"
            hint="The active local user must have the agent role."
          >
            <input
              id="agent-user-id"
              name="user_id"
              defaultValue={editing?.user_id ?? ""}
              disabled={Boolean(editing)}
              required
            />
          </FormField>
          <FormField
            id="agent-slug"
            label="Slug (required)"
            hint="Lowercase words separated by hyphens."
          >
            <input
              id="agent-slug"
              name="slug"
              pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
              maxLength={100}
              defaultValue={editing?.slug ?? ""}
              required
            />
          </FormField>
          <FormField id="agent-licensed-name" label="Licensed name (required)">
            <input
              id="agent-licensed-name"
              name="licensed_name"
              maxLength={160}
              defaultValue={editing?.licensed_name ?? ""}
              required
            />
          </FormField>
          <FormField
            id="agent-approved-title"
            label="Approved title (required)"
          >
            <input
              id="agent-approved-title"
              name="approved_title"
              maxLength={160}
              defaultValue={editing?.approved_title ?? ""}
              required
            />
          </FormField>
          <FormField
            id="agent-licence-number"
            label="Licence number (required)"
          >
            <input
              id="agent-licence-number"
              name="licence_number"
              maxLength={80}
              defaultValue={editing?.licence_number ?? ""}
              required
            />
          </FormField>
          <FormField id="agent-public-email" label="Approved public email">
            <input
              id="agent-public-email"
              name="public_email"
              type="email"
              maxLength={320}
              defaultValue={editing?.public_email ?? ""}
            />
          </FormField>
          <FormField id="agent-public-phone" label="Approved public phone">
            <input
              id="agent-public-phone"
              name="public_phone"
              type="tel"
              maxLength={32}
              defaultValue={editing?.public_phone ?? ""}
            />
          </FormField>
          <FormField
            id="agent-languages"
            label="Languages"
            hint="Comma-separated, public-safe values."
          >
            <input
              id="agent-languages"
              name="languages"
              defaultValue={editing?.languages.join(", ") ?? ""}
            />
          </FormField>
          <FormField
            id="agent-service-areas"
            label="Service areas"
            hint="Comma-separated, public-safe values."
          >
            <input
              id="agent-service-areas"
              name="service_areas"
              defaultValue={editing?.service_areas.join(", ") ?? ""}
            />
          </FormField>
          <FormField
            id="agent-specialties"
            label="Specialties"
            hint="Comma-separated, public-safe values."
          >
            <input
              id="agent-specialties"
              name="specialties"
              defaultValue={editing?.specialties.join(", ") ?? ""}
            />
          </FormField>
          <FormField id="agent-photo-url" label="Approved photo HTTPS URL">
            <input
              id="agent-photo-url"
              name="photo_url"
              type="url"
              maxLength={2048}
              defaultValue={editing?.photo_url ?? ""}
            />
          </FormField>
          <FormField id="agent-photo-alt" label="Photo alternative text">
            <input
              id="agent-photo-alt"
              name="photo_alt_text"
              maxLength={300}
              defaultValue={editing?.photo_alt_text ?? ""}
            />
          </FormField>
        </div>
        <FormField
          id="agent-biography"
          label="Biography (required)"
          hint="Bounded plain text; no HTML."
        >
          <textarea
            id="agent-biography"
            name="biography"
            maxLength={3000}
            defaultValue={editing?.biography ?? ""}
            required
          />
        </FormField>
        <FormField
          id="agent-social-links"
          label="Approved social links"
          hint="One per line as Label | https://approved.example/path."
        >
          <textarea
            id="agent-social-links"
            name="social_links"
            defaultValue={
              editing?.social_links
                .map((link) => `${link.label} | ${link.url}`)
                .join("\n") ?? ""
            }
          />
        </FormField>
        {editing?.status === "published" ? (
          <p className="notice">
            Saving published content returns the profile to pending approval and
            removes it from public rendering.
          </p>
        ) : null}
        <div className="button-row">
          <Button type="submit" disabled={busy}>
            {editing ? "Save profile changes" : "Create draft profile"}
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

      <section aria-labelledby="agent-profile-list-heading">
        <h2 id="agent-profile-list-heading">Agent profiles</h2>
        {profiles.length === 0 ? (
          <p>No agent profiles have been created.</p>
        ) : (
          <div className="grid-2 agent-admin-grid">
            {profiles.map((profile) => (
              <article className="card" key={profile.id}>
                <h3>{profile.licensed_name}</h3>
                <p>
                  Status: <StatusBadge>{profile.status}</StatusBadge>
                </p>
                <p>
                  {profile.approved_title} · Licence {profile.licence_number}
                </p>
                <p>Version {profile.version}</p>
                <div className="button-row">
                  {profile.status !== "archived" ? (
                    <Button
                      type="button"
                      onClick={() => setEditing(profile)}
                      disabled={busy}
                      aria-label={`Edit ${profile.licensed_name}`}
                    >
                      Edit
                    </Button>
                  ) : null}
                  {profile.status === "draft" ? (
                    <Button
                      type="button"
                      disabled={busy}
                      onClick={(event) =>
                        startAction(
                          event,
                          profile,
                          "pending_approval",
                          "Submitting profile for approval",
                        )
                      }
                      aria-label={`Submit ${profile.licensed_name} for approval`}
                    >
                      Submit for approval
                    </Button>
                  ) : null}
                  {profile.status === "pending_approval" ? (
                    <Button
                      type="button"
                      disabled={busy}
                      onClick={(event) =>
                        startAction(
                          event,
                          profile,
                          "published",
                          "Publishing profile",
                        )
                      }
                      aria-label={`Publish ${profile.licensed_name}`}
                    >
                      Publish
                    </Button>
                  ) : null}
                  {profile.status === "published" ? (
                    <Button
                      type="button"
                      disabled={busy}
                      onClick={(event) =>
                        startAction(
                          event,
                          profile,
                          "suspended",
                          "Suspending profile",
                        )
                      }
                      aria-label={`Suspend ${profile.licensed_name}`}
                    >
                      Suspend
                    </Button>
                  ) : null}
                  {profile.status === "suspended" ? (
                    <Button
                      type="button"
                      disabled={busy}
                      onClick={(event) =>
                        startAction(
                          event,
                          profile,
                          "published",
                          "Republishing profile",
                        )
                      }
                      aria-label={`Republish ${profile.licensed_name}`}
                    >
                      Republish
                    </Button>
                  ) : null}
                  {profile.status === "draft" ||
                  profile.status === "published" ||
                  profile.status === "suspended" ? (
                    <Button
                      type="button"
                      disabled={busy}
                      onClick={(event) =>
                        startAction(
                          event,
                          profile,
                          "archived",
                          "Archiving profile",
                        )
                      }
                      aria-label={`Archive ${profile.licensed_name}`}
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

      <ConfirmationDialog
        title={
          pendingAction ? `${pendingAction.label}?` : "Confirm profile action"
        }
        open={pendingAction !== null}
        onCancel={closeDialog}
        onConfirm={confirmTransition}
        dialogRef={dialogRef}
        busy={busy}
      >
        <p>
          This explicit lifecycle action changes whether the profile can appear
          publicly. Publication requires brokerage approval; suspended and
          archived profiles are hidden immediately.
        </p>
        {pendingAction?.target === "suspended" ? (
          <FormField id="agent-transition-reason" label="Reason (required)">
            <textarea
              id="agent-transition-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              maxLength={1000}
              required
            />
          </FormField>
        ) : null}
      </ConfirmationDialog>
    </div>
  );
}
