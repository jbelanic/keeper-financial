"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createKeeperBrowserClient } from "@/lib/supabase-browser";

export function PortalSignOut() {
  const supabase = useMemo(() => createKeeperBrowserClient(), []);
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await supabase.auth.signOut();
    } finally {
      router.push("/auth/sign-in");
      router.refresh();
    }
  }

  return (
    <button
      type="button"
      className="portal-sign-out"
      onClick={handleSignOut}
      disabled={signingOut}
    >
      {signingOut ? "Signing out…" : "Sign out"}
    </button>
  );
}
