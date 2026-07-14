import type { Metadata } from "next";
import { Card } from "@keeper/ui";
import { ApplyForm } from "./apply-form";

export const metadata: Metadata = {
  title: "Get started",
  description:
    "Choose a minimal contact-first inquiry or an approved secure external mortgage application.",
};

export default function ApplyPage() {
  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return (
    <>
      <header className="foundation-header container">
        <p className="eyebrow">Get started</p>
        <h1>Choose the path that works for you.</h1>
        <p>
          Both options are presented equally. A full mortgage application is
          never collected on this website.
        </p>
      </header>
      <section className="container section">
        <div className="grid-2">
          <Card>
            <h2>Speak with someone first</h2>
            <p>
              Provide only enough information for the team to contact you. Do
              not submit sensitive financial or identity information.
            </p>
            <ApplyForm />
          </Card>
          <Card>
            <h2>Start a secure full application</h2>
            <p>
              Your financial and underwriting information belongs in the
              selected established mortgage-application platform—not on Keeper
              Financial’s website.
            </p>
            <p className="notice">
              The provider is not yet selected. Until an approved HTTPS host is
              configured, this link fails safely and no application is started.
            </p>
            <a
              className="button-link"
              href={`${apiBase}/api/v1/integrations/mortgage-application`}
            >
              Continue to configured secure provider
            </a>
          </Card>
        </div>
      </section>
    </>
  );
}
