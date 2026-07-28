import { NextResponse, type NextRequest } from "next/server";
import {
  CandidateProvisioningError,
  isSafePostingSlug,
  startCandidateApplication,
} from "@/lib/candidate-provisioning";
import { requestOrigin, requestUrl } from "@/lib/request-url";
import { getSupabaseServerClient } from "@/lib/supabase-server";

function safeReturnTo(
  value: FormDataEntryValue | null,
): "/candidate" | "/admin" | "/agent" {
  if (value === "/admin" || value === "/agent") return value;
  return "/candidate";
}

function signInUrl(
  request: NextRequest,
  error: string,
  posting?: string,
  returnTo: "/candidate" | "/admin" | "/agent" = "/candidate",
) {
  const url = requestUrl(request, "/auth/sign-in");
  url.searchParams.set("error", error);
  if (posting) url.searchParams.set("posting", posting);
  if (returnTo === "/admin") url.searchParams.set("returnTo", returnTo);
  return url;
}

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (origin && origin !== requestOrigin(request)) {
    return new NextResponse("Sign-in request rejected", { status: 403 });
  }
  const form = await request.formData();
  const postingValue = form.get("posting");
  const posting = typeof postingValue === "string" ? postingValue : "";
  const returnTo = safeReturnTo(form.get("returnTo"));
  if (posting && !isSafePostingSlug(posting)) {
    return NextResponse.redirect(
      signInUrl(request, "posting-unavailable"),
      303,
    );
  }
  const emailValue = form.get("email");
  const passwordValue = form.get("password");
  const email = typeof emailValue === "string" ? emailValue.trim() : "";
  const password = typeof passwordValue === "string" ? passwordValue : "";
  if (!email || email.length > 254 || !password || password.length > 1024) {
    return NextResponse.redirect(
      signInUrl(request, "credentials", posting || undefined, returnTo),
      303,
    );
  }

  const supabase = await getSupabaseServerClient();
  let authResult: {
    data: { session: { access_token: string } | null };
    error: unknown;
  };
  try {
    authResult = await supabase.auth.signInWithPassword({
      email,
      password,
    });
  } catch {
    return NextResponse.redirect(
      signInUrl(request, "credentials", posting || undefined, returnTo),
      303,
    );
  }
  const token = authResult.data.session?.access_token;
  if (authResult.error || !token) {
    return NextResponse.redirect(
      signInUrl(request, "credentials", posting || undefined, returnTo),
      303,
    );
  }
  if (!posting) {
    if (returnTo === "/admin") {
      return NextResponse.redirect(
        requestUrl(request, "/auth/mfa?returnTo=/admin"),
        303,
      );
    }
    if (returnTo === "/agent") {
      return NextResponse.redirect(
        requestUrl(request, "/auth/mfa?returnTo=/agent"),
        303,
      );
    }
    return NextResponse.redirect(requestUrl(request, returnTo), 303);
  }
  try {
    const application = await startCandidateApplication(token, posting);
    return NextResponse.redirect(
      requestUrl(request, `/candidate/applications/${application.id}`),
      303,
    );
  } catch (error) {
    if (error instanceof CandidateProvisioningError && error.status === 404) {
      return NextResponse.redirect(
        signInUrl(request, "posting-unavailable"),
        303,
      );
    }
    return NextResponse.redirect(
      signInUrl(request, "application-access", posting),
      303,
    );
  }
}
