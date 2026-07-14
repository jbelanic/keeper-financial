import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@keeper/ui/tokens.css";
import "./globals.css";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.siteUrl),
  title: { default: "Keeper Financial", template: "%s | Keeper Financial" },
  description:
    "Plain-language mortgage guidance and secure next steps from Keeper Financial in Ontario.",
  applicationName: "Keeper Financial",
  referrer: "strict-origin-when-cross-origin",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en-CA">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
