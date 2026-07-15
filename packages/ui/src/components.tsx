import { cloneElement, isValidElement } from "react";
import type {
  ComponentPropsWithoutRef,
  ReactElement,
  ReactNode,
  RefObject,
} from "react";

export function Button({
  className = "",
  ...props
}: ComponentPropsWithoutRef<"button">) {
  return <button className={`button ${className}`.trim()} {...props} />;
}

export function Card({
  className = "",
  ...props
}: ComponentPropsWithoutRef<"section">) {
  return <section className={`card ${className}`.trim()} {...props} />;
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "start",
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  align?: "start" | "center";
}) {
  return (
    <header className={`section-heading section-heading-${align}`}>
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
    </header>
  );
}

export function Disclosure({
  summary,
  children,
}: {
  summary: string;
  children: ReactNode;
}) {
  return (
    <details className="disclosure">
      <summary>{summary}</summary>
      <div className="disclosure-content">{children}</div>
    </details>
  );
}

export function FormField({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  const describedBy = [hint ? `${id}-hint` : null, error ? `${id}-error` : null]
    .filter(Boolean)
    .join(" ");
  const control = isValidElement(children)
    ? cloneElement(
        children as ReactElement<{
          "aria-describedby"?: string;
          "aria-invalid"?: boolean;
        }>,
        {
          "aria-describedby": describedBy || undefined,
          "aria-invalid": error ? true : undefined,
        },
      )
    : children;
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      {hint ? <span id={`${id}-hint`}>{hint}</span> : null}
      {control}
      {error ? (
        <span id={`${id}-error`} className="field-error">
          {error}
        </span>
      ) : null}
    </div>
  );
}

export function ErrorSummary({
  title = "Please check the form",
  errors,
}: {
  title?: string;
  errors: string[];
}) {
  if (errors.length === 0) return null;
  return (
    <section
      className="error-summary"
      role="alert"
      aria-labelledby="error-summary-title"
      tabIndex={-1}
    >
      <h2 id="error-summary-title">{title}</h2>
      <ul>
        {errors.map((error) => (
          <li key={error}>{error}</li>
        ))}
      </ul>
    </section>
  );
}

export function StatusBadge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  return <span className={`status-badge status-${tone}`}>{children}</span>;
}

export function DataTable({
  caption,
  headers,
  rows,
}: {
  caption: string;
  headers: string[];
  rows: ReactNode[][];
}) {
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      role="region"
      aria-label={caption}
    >
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            {headers.map((header) => (
              <th scope="col" key={header}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EmptyState({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="state-panel">
      <h2>{title}</h2>
      <p>{children}</p>
    </section>
  );
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="state-panel" role="status">
      <span className="spinner" aria-hidden="true" /> {label}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  children,
}: {
  title?: string;
  children: ReactNode;
}) {
  return (
    <section className="state-panel error-state" role="alert">
      <h2>{title}</h2>
      <p>{children}</p>
    </section>
  );
}

export function Breadcrumbs({
  items,
}: {
  items: Array<{ label: string; href?: string }>;
}) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="breadcrumbs">
        {items.map((item, index) => (
          <li key={item.label}>
            {item.href ? (
              <a href={item.href}>{item.label}</a>
            ) : (
              <span
                aria-current={index === items.length - 1 ? "page" : undefined}
              >
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function Timeline({
  items,
}: {
  items: Array<{ label: string; detail: string }>;
}) {
  return (
    <ol className="timeline">
      {items.map((item) => (
        <li key={`${item.label}-${item.detail}`}>
          <strong>{item.label}</strong>
          <span>{item.detail}</span>
        </li>
      ))}
    </ol>
  );
}

export function ProgressChecklist({
  items,
}: {
  items: Array<{ label: string; complete: boolean }>;
}) {
  return (
    <ul className="checklist">
      {items.map((item) => (
        <li key={item.label}>
          <span aria-hidden="true">{item.complete ? "✓" : "○"}</span>
          <span>
            {item.label}
            {item.complete ? (
              <span className="visually-hidden"> complete</span>
            ) : null}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function ConfirmationDialog({
  title,
  children,
  open,
  onCancel,
  onConfirm,
  dialogRef,
  busy = false,
}: {
  title: string;
  children: ReactNode;
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  dialogRef: RefObject<HTMLDialogElement | null>;
  busy?: boolean;
}) {
  if (!open) return null;
  return (
    <dialog
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-busy={busy}
      className="dialog"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onCancel();
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          if (!busy) onCancel();
          return;
        }
        if (event.key !== "Tab") return;
        const focusable = Array.from(
          event.currentTarget.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
          ),
        ).filter((element) => !element.hasAttribute("hidden"));
        const first = focusable[0];
        const last = focusable.at(-1);
        if (!first || !last) {
          event.preventDefault();
        } else if (
          event.shiftKey &&
          (document.activeElement === first ||
            !event.currentTarget.contains(document.activeElement))
        ) {
          event.preventDefault();
          last.focus();
        } else if (
          !event.shiftKey &&
          (document.activeElement === last ||
            !event.currentTarget.contains(document.activeElement))
        ) {
          event.preventDefault();
          first.focus();
        }
      }}
    >
      <h2 id="dialog-title">{title}</h2>
      <div>{children}</div>
      <div className="button-row">
        <Button type="button" onClick={onCancel} autoFocus disabled={busy}>
          Cancel
        </Button>
        <Button
          type="button"
          className="button-danger"
          onClick={onConfirm}
          disabled={busy}
        >
          Confirm
        </Button>
      </div>
    </dialog>
  );
}

export function FileUpload({
  id,
  label,
  accept,
}: {
  id: string;
  label: string;
  accept: string;
}) {
  return (
    <FormField
      id={id}
      label={label}
      hint="Files remain private and access-controlled."
    >
      <input id={id} name={id} type="file" accept={accept} />
    </FormField>
  );
}

export function ConsentCheckbox({
  id,
  children,
  required = false,
  error,
}: {
  id: string;
  children: ReactNode;
  required?: boolean;
  error?: string;
}) {
  return (
    <div className="consent">
      <input
        id={id}
        name={id}
        type="checkbox"
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
      />
      <div>
        <label htmlFor={id}>{children}</label>
        {error ? (
          <div id={`${id}-error`} className="field-error">
            {error}
          </div>
        ) : null}
      </div>
    </div>
  );
}
