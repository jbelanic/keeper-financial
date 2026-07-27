import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import { Breadcrumbs } from "@keeper/ui";

export function Icon({
  name,
}: {
  name:
    | "home"
    | "refresh"
    | "calendar"
    | "key"
    | "building"
    | "conversation"
    | "shield"
    | "arrow";
}) {
  const paths = {
    home: <path d="M3 11.5 12 4l9 7.5M5.5 10v10h13V10M9 20v-6h6v6" />,
    refresh: (
      <path d="M20 7v5h-5M4 17v-5h5M6.1 8A7 7 0 0 1 18.5 7M17.9 16A7 7 0 0 1 5.5 17" />
    ),
    calendar: <path d="M5 3v3M19 3v3M3.5 9h17M4 5h16v16H4zM8 13h3v3H8z" />,
    key: (
      <path d="M14.5 9.5a5 5 0 1 1-4-4 5 5 0 0 1 4 4ZM14 10l7 7M18 14l-2 2M20 16l-2 2" />
    ),
    building: <path d="M4 21V9l8-5 8 5v12M2 21h20M8 10v7M12 10v7M16 10v7" />,
    conversation: <path d="M4 5h16v11H9l-5 4V5ZM8 9h8M8 12h5" />,
    shield: (
      <path d="M12 3 4.5 6v5.5c0 4.8 3.1 8 7.5 9.5 4.4-1.5 7.5-4.7 7.5-9.5V6L12 3Zm-3 9 2 2 4-5" />
    ),
    arrow: <path d="M5 12h14M14 7l5 5-5 5" />,
  };
  return (
    <svg
      className="line-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      {paths[name]}
    </svg>
  );
}

export function PageHero({
  eyebrow,
  title,
  description,
  children,
  image,
  imageAlt,
  imagePriority = false,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
  image?: string;
  imageAlt?: string;
  imagePriority?: boolean;
}) {
  return (
    <header className={`page-hero ${image ? "page-hero-with-image" : ""}`}>
      <div className="container page-hero-grid">
        <div className="page-hero-copy">
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="page-lead">{description}</p>
          {children}
        </div>
        {image ? (
          <div className="page-hero-media">
            <Image
              src={image}
              alt={imageAlt ?? ""}
              fill
              priority={imagePriority}
              sizes="(max-width: 832px) 100vw, 52vw"
            />
          </div>
        ) : null}
      </div>
    </header>
  );
}

export function ServiceCard({
  href,
  title,
  description,
  icon,
}: {
  href: string;
  title: string;
  description: string;
  icon: Parameters<typeof Icon>[0]["name"];
}) {
  return (
    <article className="service-card">
      <Icon name={icon} />
      <h3>{title}</h3>
      <p>{description}</p>
      <Link className="text-link" href={href}>
        Learn more <Icon name="arrow" />
      </Link>
    </article>
  );
}

export function CtaBand({
  title,
  description,
  primaryHref,
  primaryLabel,
  secondaryHref,
  secondaryLabel,
}: {
  title: string;
  description: string;
  primaryHref: string;
  primaryLabel: string;
  secondaryHref?: string;
  secondaryLabel?: string;
}) {
  return (
    <section className="cta-band">
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div className="button-row">
        <Link className="button-link" href={primaryHref}>
          {primaryLabel}
        </Link>
        {secondaryHref && secondaryLabel ? (
          <Link className="button-link button-on-dark" href={secondaryHref}>
            {secondaryLabel}
          </Link>
        ) : null}
      </div>
    </section>
  );
}

export function InteriorPageHeader({
  title,
  description,
  parent,
}: {
  title: string;
  description: string;
  parent?: { label: string; href: string };
}) {
  return (
    <header className="interior-header">
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          ...(parent ? [parent] : []),
          { label: title },
        ]}
      />
      <h1>{title}</h1>
      <p className="page-lead">{description}</p>
    </header>
  );
}
