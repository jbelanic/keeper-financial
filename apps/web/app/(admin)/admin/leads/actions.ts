"use server";

import { revalidatePath } from "next/cache";
import {
  assignAdminLeadAgent,
  updateAdminLeadStatus,
  withdrawAdminLeadMarketing,
} from "@/lib/admin-leads";

export async function withdrawMarketingConsent(
  formData: FormData,
): Promise<void> {
  const leadId = formData.get("lead_id");
  if (typeof leadId !== "string") throw new Error("invalid lead identifier");
  await withdrawAdminLeadMarketing(leadId);
  revalidatePath("/admin/leads");
}

export async function updateLeadStatus(formData: FormData): Promise<void> {
  const leadId = formData.get("lead_id");
  const status = formData.get("status");
  if (typeof leadId !== "string") throw new Error("invalid lead identifier");
  if (
    status !== "new" &&
    status !== "assigned" &&
    status !== "contacted" &&
    status !== "closed"
  ) {
    throw new Error("invalid lead status");
  }
  await updateAdminLeadStatus(leadId, status);
  revalidatePath("/admin/leads");
}

export async function assignLeadAgent(formData: FormData): Promise<void> {
  const leadId = formData.get("lead_id");
  const agentUserId = formData.get("agent_user_id");
  if (typeof leadId !== "string") throw new Error("invalid lead identifier");
  // An empty selection clears the assignment; the API re-validates eligibility.
  const target =
    typeof agentUserId === "string" && agentUserId.trim() ? agentUserId : null;
  await assignAdminLeadAgent(leadId, target);
  revalidatePath("/admin/leads");
}
