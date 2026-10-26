"use client";

import Image from "next/image";
import { useRef, useState } from "react";
import {
  Button,
  ConfirmationDialog,
  ErrorSummary,
  FormField,
  StatusBadge,
} from "@keeper/ui";
import type { AdminAgentProfile, EligibleAgent } from "@/lib/agent-api";
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

/** The API caps a profile at ten approved social links. */
const MAX_SOCIAL_LINKS = 10;

type SocialLink = { label: string; url: string };

/**
 * The approved-social-link field is one link per line. `Label | https://…` sets
 * the public link text; a bare `https://…` line is also accepted and labelled
 * with its domain, so pasting a profile URL is enough. A line without a URL
 * used to reach the API as `""` and come back as "String should have at least
 * 1 character", which named neither the field nor the line, so the entry is
 * parsed and explained here before anything is sent.
 */
function parseSocialLinks(value: FormDataEntryValue | null): {
  links: SocialLink[];
  errors: string[];
} {
  const links: SocialLink[] = [];
  const errors: string[] = [];

  String(value ?? "")
    .split("\n")
    .forEach((raw, index) => {
      const line = raw.trim();
      if (!line) return;
      const position = index + 1;
      const separator = line.indexOf("|");
      const label = separator === -1 ? "" : line.slice(0, separator).trim();
      const url = (separator === -1 ? line : line.slice(separator + 1)).trim();

      let parsed: URL;
      try {
        parsed = new URL(url);
      } catch {
        errors.push(
          `Social links, line ${position}: "${line}" is not a link. Enter https://… or Label | https://….`,
        );
        return;
      }
      if (parsed.protocol !== "https:") {
        errors.push(
          `Social links, line ${position}: links must start with https://.`,
        );
        return;
      }
      const publicLabel =
        label || parsed.hostname.toLowerCase().replace(/^www\./, "");
      if (publicLabel.length > 80) {
        errors.push(
          `Social links, line ${position}: the link text is longer than 80 characters.`,
        );
        return;
      }
      links.push({ label: publicLabel, url });
    });

  if (links.length > MAX_SOCIAL_LINKS) {
    errors.push(
      `Social links: keep at most ${MAX_SOCIAL_LINKS} links (found ${links.length}).`,
    );
  }
  return { links, errors };
}

function optionalValue(value: FormDataEntryValue | null): string | null {
  const normalized = String(value ?? "").trim();
  return normalized || null;
}

function publicSlug(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100);
}

const PROFILE_SAVE_FALLBACK =
  "The profile was not saved. Check the active agent relationship, bounded public fields, links, and your administration access.";

const FIELD_LABELS: Record<string, string> = {
  slug: "Slug",
  licensed_name: "Licensed name",
  approved_title: "Approved title",
  licence_number: "Licence number",
  biography: "Biography",
  languages: "Languages",
  service_areas: "Service areas",
  specialties: "Specialties",
  photo_url: "Photo",
  photo_alt_text: "Photo alternative text",
  public_email: "Public email",
  public_phone: "Public phone",
  social_links: "Social links",
};

const ENTRY_LABELS: Record<string, string> = {
  label: "link text",
  url: "link URL",
};

/**
 * FastAPI pins each rejection to a location such as
 * `["body", "social_links", 1, "url"]`. Naming that location is what the
 * operator needs, because the raw message on its own ("String should have at
 * least 1 character") never says which field or which social-link line failed.
 */
function fieldContext(loc: unknown): string {
  if (!Array.isArray(loc)) return "";
  const parts = loc as Array<string | number>;
  const field = parts.find(
    (part): part is string =>
      typeof part === "string" &&
      part !== "body" &&
      part !== "query" &&
      part !== "path" &&
      part !== "header",
  );
  const name = field ? FIELD_LABELS[field] : undefined;
  if (!name) return "";
  const details: string[] = [];
  const entry = parts.find((part): part is number => typeof part === "number");
  if (entry !== undefined) details.push(`line ${entry + 1}`);
  const entryField = parts.find(
    (part): part is string => ENTRY_LABELS[part] !== undefined,
  );
  if (entryField) details.push(ENTRY_LABELS[entryField]);
  return details.length ? `${name}, ${details.join(", ")}` : name;
}

/**
 * FastAPI reports a rejected save as a 422 with either `detail: "<message>"` or
 * `detail: [{ msg, loc }, ...]`. Showing that message, prefixed with the field
 * it belongs to, is the difference between "something went wrong" and
 * "Social links, line 2, link URL: URL must be HTTPS", so surface the first
 * bounded human-readable one and fall back to the generic sentence when the
 * body is unexpected.
 */
async function profileSaveError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    const detail = (body as { detail?: unknown } | null)?.detail;
    const item = Array.isArray(detail)
      ? detail.find(
          (candidate): candidate is { msg: string; loc?: unknown } =>
            typeof (candidate as { msg?: unknown })?.msg === "string",
        )
      : undefined;
    const message =
      item?.msg ?? (typeof detail === "string" ? detail : undefined);
    const trimmed = message?.trim();
    if (trimmed) {
      const text = trimmed.slice(0, 300);
      const context = fieldContext(item?.loc);
      return `The profile was not saved. ${context ? `${context}: ${text}` : text}`;
    }
  } catch {
    // Fall through to the generic sentence.
  }
  return PROFILE_SAVE_FALLBACK;
}

export function AgentProfileManager({
  initialProfiles,
  initialEligibleAgents,
  requester = adminBrowserRequest,
}: {
  initialProfiles: AdminAgentProfile[];
  initialEligibleAgents: EligibleAgent[];
  requester?: Requester;
}) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [editing, setEditing] = useState<AdminAgentProfile | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [slug, setSlug] = useState("");
  const [slugAvailability, setSlugAvailability] = useState("");
  // Keeper stores the photo and serves it from our own public read route, so the
  // administrator never needs an external HTTPS host (decision 56).
  const [photoUrl, setPhotoUrl] = useState("");
  const [photoAlt, setPhotoAlt] = useState("");
  const [photoBusy, setPhotoBusy] = useState(false);
  const [photoNotice, setPhotoNotice] = useState("");
  // The list owns the page; the create/edit form is opened explicitly.
  const [formOpen, setFormOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const actionTriggerRef = useRef<HTMLButtonElement | null>(null);

  function restoreActionFocus() {
    requestAnimationFrame(() => actionTriggerRef.current?.focus());
  }

  function revealEditor() {
    requestAnimationFrame(() => {
      document
        .getElementById("agent-profile-editor")
        ?.scrollIntoView?.({ block: "start" });
    });
  }

  function resetPhotoState(profile: AdminAgentProfile | null) {
    setPhotoUrl(profile?.photo_url ?? "");
    setPhotoAlt(profile?.photo_alt_text ?? "");
    setPhotoBusy(false);
    setPhotoNotice("");
  }

  function openCreateForm() {
    setEditing(null);
    setSelectedAgentId("");
    setSlug("");
    setSlugAvailability("");
    resetPhotoState(null);
    setFormOpen(true);
    revealEditor();
  }

  function openEditForm(profile: AdminAgentProfile) {
    setEditing(profile);
    setSelectedAgentId(profile.user_id);
    setSlug(profile.slug);
    setSlugAvailability("");
    resetPhotoState(profile);
    setFormOpen(true);
    revealEditor();
  }

  function closeForm() {
    setEditing(null);
    setSelectedAgentId("");
    setSlug("");
    setSlugAvailability("");
    resetPhotoState(null);
    setFormOpen(false);
  }

  async function uploadPhoto(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || photoBusy) return;
    setPhotoBusy(true);
    setErrors([]);
    setPhotoNotice("Uploading photo…");
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await requester("/api/v1/admin/agent-photos", {
        method: "POST",
        body,
      });
      if (!response.ok) throw new Error("photo rejected");
      const result = (await response.json()) as { photo_url: string };
      setPhotoUrl(result.photo_url);
      setPhotoNotice(
        "Photo stored. Add alternative text, then save the profile to apply the change.",
      );
      event.target.value = "";
    } catch {
      setPhotoNotice("");
      setErrors([
        "The photo was not uploaded. Use a JPEG or PNG file no larger than 5 MiB.",
      ]);
    } finally {
      setPhotoBusy(false);
    }
  }

  function removePhoto() {
    if (photoBusy) return;
    setPhotoUrl("");
    setPhotoAlt("");
    setPhotoNotice("Photo removed. Save the profile to apply the change.");
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
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const { links: approvedLinks, errors: linkErrors } = parseSocialLinks(
      form.get("social_links"),
    );
    if (linkErrors.length) {
      // Name the line before the request: the API cannot say which line it was.
      setErrors(linkErrors);
      setNotice("");
      return;
    }
    setBusy(true);
    setErrors([]);
    setNotice(editing ? "Saving profile changes…" : "Creating draft profile…");
    const payload = {
      ...(!editing
        ? { user_id: String(form.get("user_id") ?? "").trim() }
        : {}),
      slug: editing?.slug_locked_at
        ? editing.slug
        : String(form.get("slug") ?? "").trim(),
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
      social_links: approvedLinks,
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
      if (!response.ok) throw new Error(await profileSaveError(response));
      const profile = (await response.json()) as AdminAgentProfile;
      setProfiles((items) => {
        const exists = items.some((item) => item.id === profile.id);
        return exists
          ? items.map((item) => (item.id === profile.id ? profile : item))
          : [profile, ...items];
      });
      formElement.reset();
      closeForm();
      setNotice(
        editing
          ? "Profile changes saved for approval."
          : "Draft profile created.",
      );
    } catch (error) {
      setErrors([
        error instanceof Error && error.message
          ? error.message
          : PROFILE_SAVE_FALLBACK,
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function checkSlugAvailability(candidateSlug: string) {
    if (editing?.slug_locked_at || !candidateSlug) return;
    setSlugAvailability("Checking slug availability…");
    try {
      const response = await requester(
        `/api/v1/admin/agent-profiles/slug-availability?slug=${encodeURIComponent(candidateSlug)}`,
      );
      if (!response.ok) throw new Error("unavailable");
      const result = (await response.json()) as { available: boolean };
      setSlugAvailability(
        result.available || editing?.slug === candidateSlug
          ? "Slug is available."
          : "Slug is already reserved.",
      );
    } catch {
      setSlugAvailability("Slug availability could not be verified.");
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
            ? {
                ...item,
                status: result.status,
                slug_locked_at:
                  pendingAction.target === "published"
                    ? (item.slug_locked_at ?? new Date().toISOString())
                    : item.slug_locked_at,
              }
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

      <section aria-labelledby="agent-profile-list-heading">
        <h2 id="agent-profile-list-heading">Agent profiles</h2>
        <p>
          Create, edit, approve, publish, suspend, and archive public-safe
          profiles through the explicit lifecycle.
        </p>
        <div className="button-row admin-toolbar">
          <Button
            type="button"
            onClick={openCreateForm}
            disabled={busy || initialEligibleAgents.length === 0}
            aria-expanded={formOpen}
            aria-controls="agent-profile-editor"
          >
            Create new profile
          </Button>
        </div>
        {initialEligibleAgents.length === 0 ? (
          <p className="notice">
            No active agent is available for a new profile: every agent already
            has one.
          </p>
        ) : null}
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
                      onClick={() => openEditForm(profile)}
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

      {formOpen ? (
        <form
          id="agent-profile-editor"
          className="card agent-profile-form"
          onSubmit={save}
          aria-busy={busy}
          key={editing?.id ?? "new-agent-profile"}
        >
          <h2>{editing ? "Edit agent profile" : "Create agent profile"}</h2>
          <p>
            Only approved public profile and regulatory information belongs
            here. Do not enter borrower, underwriting, identity-document, or
            financial data.
          </p>
          <div className="form-grid">
            <FormField
              id="agent-user-id"
              label="Eligible agent (required)"
              hint="Only an active local agent without an existing profile is listed."
            >
              <select
                id="agent-user-id"
                name="user_id"
                value={editing?.user_id ?? selectedAgentId}
                disabled={Boolean(editing)}
                onChange={(event) => {
                  const userId = event.target.value;
                  setSelectedAgentId(userId);
                  const agent = initialEligibleAgents.find(
                    (item) => item.user_id === userId,
                  );
                  if (agent && !slug) setSlug(publicSlug(agent.display_name));
                }}
                required
              >
                <option value="">Select an eligible agent</option>
                {initialEligibleAgents.map((agent) => (
                  <option key={agent.user_id} value={agent.user_id}>
                    {agent.display_name} — {agent.email}
                  </option>
                ))}
                {editing &&
                !initialEligibleAgents.some(
                  (item) => item.user_id === editing.user_id,
                ) ? (
                  <option value={editing.user_id}>
                    {editing.licensed_name}
                  </option>
                ) : null}
              </select>
            </FormField>
            <FormField
              id="agent-slug"
              label="Slug (required)"
              hint={
                editing?.slug_locked_at
                  ? "Locked permanently on first publication."
                  : "Generated from the selected agent; lowercase words separated by hyphens."
              }
            >
              <input
                id="agent-slug"
                name="slug"
                pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                maxLength={100}
                value={editing?.slug_locked_at ? editing.slug : slug}
                disabled={Boolean(editing?.slug_locked_at)}
                onChange={(event) => {
                  setSlug(publicSlug(event.target.value));
                  setSlugAvailability("");
                }}
                onBlur={(event) => checkSlugAvailability(event.target.value)}
                required
              />
              <span aria-live="polite">{slugAvailability}</span>
            </FormField>
            <FormField
              id="agent-licensed-name"
              label="Licensed name (required)"
            >
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
            <FormField
              id="agent-photo-file"
              label="Approved photo"
              hint="JPEG or PNG, up to 5 MiB. Keeper stores the file privately and serves it through this site."
            >
              <input
                id="agent-photo-file"
                name="photo_file"
                type="file"
                accept="image/jpeg,image/png"
                onChange={uploadPhoto}
                disabled={photoBusy || busy}
              />
              <span aria-live="polite">{photoNotice}</span>
            </FormField>
            <input type="hidden" name="photo_url" value={photoUrl} />
            <FormField
              id="agent-photo-alt"
              label="Photo alternative text"
              hint="Required with a photo; describe the person and the setting."
            >
              <input
                id="agent-photo-alt"
                name="photo_alt_text"
                maxLength={300}
                value={photoAlt}
                onChange={(event) => setPhotoAlt(event.target.value)}
              />
            </FormField>
            {photoUrl ? (
              <div className="agent-photo-preview">
                <Image
                  src={photoUrl}
                  alt={photoAlt || "Current agent photo preview"}
                  width={160}
                  height={160}
                  unoptimized
                />
                <button
                  type="button"
                  className="text-link"
                  onClick={removePhoto}
                  disabled={photoBusy || busy}
                >
                  Remove photo
                </button>
              </div>
            ) : null}
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
            hint="One link per line: paste an https:// link, or enter Label | https://… to choose the public link text. Up to 10 links."
          >
            <textarea
              id="agent-social-links"
              name="social_links"
              rows={4}
              defaultValue={
                editing?.social_links
                  .map((link) => `${link.label} | ${link.url}`)
                  .join("\n") ?? ""
              }
            />
          </FormField>
          {editing?.status === "published" ? (
            <p className="notice">
              Saving published content returns the profile to pending approval
              and removes it from public rendering.
            </p>
          ) : null}
          <div className="button-row">
            <Button type="submit" disabled={busy}>
              {editing ? "Save profile changes" : "Create draft profile"}
            </Button>
            <Button type="button" onClick={closeForm} disabled={busy}>
              {editing ? "Cancel editing" : "Cancel"}
            </Button>
          </div>
        </form>
      ) : null}

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
