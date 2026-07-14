import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  return {
    title: `Agent profile: ${slug}`,
    description: "Foundation for a brokerage-approved agent profile.",
    robots: { index: false, follow: false },
  };
}
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return (
    <div className="container section">
      <FoundationPage
        title="Agent profile"
        description={`Profile route reserved for approved agent identifier “${slug}”. Public database rendering is scheduled for Phase 1E.`}
      />
    </div>
  );
}
