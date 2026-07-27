import type { Metadata } from "next";
import { siteConfig } from "@/lib/site-config";

export function createPageMetadata({
  title,
  description,
  path,
  noIndex = false,
}: {
  title: string;
  description: string;
  path: string;
  noIndex?: boolean;
}): Metadata {
  const canonical = new URL(path, siteConfig.siteUrl).toString();
  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      type: "website",
      locale: "en_CA",
      siteName: siteConfig.displayName,
      title,
      description,
      url: canonical,
    },
    twitter: {
      card: "summary",
      title,
      description,
    },
    robots: noIndex
      ? { index: false, follow: false, noarchive: true }
      : { index: true, follow: true },
  };
}
