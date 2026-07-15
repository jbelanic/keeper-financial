import type { Metadata } from "next";
import { ErrorState } from "@keeper/ui";
import { portalServerJson } from "@/lib/portal-server-api";
import type { AdminPostingList } from "@/lib/recruitment-api";
import { RecruitmentPostingAdmin } from "./recruitment-posting-admin";

export const metadata: Metadata = { title: "Recruitment postings" };

export default async function RecruitmentPostingAdminPage() {
  const result = await portalServerJson<AdminPostingList>(
    "/api/v1/admin/recruitment-postings?limit=100&offset=0",
  );
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Administration</p>
        <h1>Recruitment postings</h1>
        <p>
          Create, edit, publish, close, and archive postings through the
          explicit lifecycle.
        </p>
      </header>
      {result ? (
        <RecruitmentPostingAdmin initialPostings={result.items} />
      ) : (
        <ErrorState title="Posting administration unavailable">
          Administration access, MFA, or the posting service could not be
          verified.
        </ErrorState>
      )}
    </>
  );
}
