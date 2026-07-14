import type { PortalArea } from "@keeper/contracts";
import { redirect } from "next/navigation";

import { portalAccessRequest } from "./portal-access";
import { getSupabaseServerClient } from "./supabase-server";

export async function requirePortalAccess(area: PortalArea): Promise<void> {
  const supabase = await getSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token || !(await portalAccessRequest(token, area))) {
    redirect(`/auth/sign-in?returnTo=/${area}`);
  }
}
