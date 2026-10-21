import type { PortalArea } from "@keeper/contracts";
import { redirect } from "next/navigation";

import { portalAccessRequest } from "./portal-access";
import { getSupabaseServerClient } from "./supabase-server";

export async function requirePortalAccess(area: PortalArea): Promise<string[]> {
  let authenticated = false;
  let needsMfa = false;
  try {
    const supabase = await getSupabaseServerClient();
    const { data: userData, error } = await supabase.auth.getUser();
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    authenticated = Boolean(!error && userData.user && token);
    if (authenticated && token) {
      const access = await portalAccessRequest(token, area);
      if (access) return access.roles;
    }
    if (authenticated && area === "admin") {
      const assurance =
        await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
      needsMfa = !assurance.error && assurance.data?.currentLevel !== "aal2";
    }
  } catch {
    // Session/provider failures remain fail closed at the server boundary.
  }
  if (needsMfa) {
    redirect("/auth/mfa?returnTo=/admin");
  }
  const areaError =
    authenticated && area === "admin"
      ? "&error=admin-access"
      : authenticated && area === "agent"
        ? "&error=agent-access"
        : "";
  redirect(`/auth/sign-in?returnTo=/${area}${areaError}`);
}
