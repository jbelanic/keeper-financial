import type { PortalArea } from "@keeper/contracts";
import { redirect } from "next/navigation";

import { portalAccessRequest } from "./portal-access";
import { getSupabaseServerClient } from "./supabase-server";

export async function requirePortalAccess(area: PortalArea): Promise<void> {
  let authenticated = false;
  let needsMfa = false;
  try {
    const supabase = await getSupabaseServerClient();
    const { data: userData, error } = await supabase.auth.getUser();
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    authenticated = Boolean(!error && userData.user && token);
    if (authenticated && token && (await portalAccessRequest(token, area))) {
      return;
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
  const error = authenticated && area === "admin" ? "&error=admin-access" : "";
  redirect(`/auth/sign-in?returnTo=/${area}${error}`);
}
