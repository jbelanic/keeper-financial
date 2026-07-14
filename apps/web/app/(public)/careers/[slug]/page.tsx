import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  return {
    title: `Career opportunity: ${slug}`,
    description: "Foundation for a published Keeper Financial opportunity.",
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
        title="Career opportunity"
        description={`Posting route reserved for published opportunity “${slug}”. Draft and closed posting queries arrive in Phase 1C.`}
      />
    </div>
  );
}
