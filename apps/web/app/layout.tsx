import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@keeper/ui/tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Keeper Financial", template: "%s | Keeper Financial" },
  description:
    "Keeper Financial is building a clear, client-first Ontario mortgage experience.",
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
