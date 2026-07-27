"use server";

import { revalidatePath } from "next/cache";
import { withdrawAdminLeadMarketing } from "@/lib/admin-leads";

export async function withdrawMarketingConsent(
  formData: FormData,
): Promise<void> {
  const leadId = formData.get("lead_id");
  if (typeof leadId !== "string") throw new Error("invalid lead identifier");
  await withdrawAdminLeadMarketing(leadId);
  revalidatePath("/admin/leads");
}
