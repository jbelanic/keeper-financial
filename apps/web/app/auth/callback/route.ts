import { NextResponse, type NextRequest } from "next/server";
import {
  CandidateProvisioningError,
  startCandidateApplication,
  isSafePostingSlug,
} from "@/lib/candidate-provisioning";
import { requestUrl } from "@/lib/request-url";
import { getSupabaseServerClient } from "@/lib/supabase-server";

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const posting = request.nextUrl.searchParams.get("posting") ?? "";
  if (!code || !isSafePostingSlug(posting)) {
    const url = requestUrl(request, "/auth/sign-in");
    url.searchParams.set("error", "verification");
    if (isSafePostingSlug(posting)) url.searchParams.set("posting", posting);
    return NextResponse.redirect(url);
  }
  const supabase = await getSupabaseServerClient();
  let authResult: {
    data: { session: { access_token: string } | null };
    error: unknown;
  };
  try {
    authResult = await supabase.auth.exchangeCodeForSession(code);
  } catch {
    const url = requestUrl(request, "/auth/sign-in");
    url.searchParams.set("error", "verification");
    url.searchParams.set("posting", posting);
    return NextResponse.redirect(url);
  }
  const token = authResult.data.session?.access_token;
  if (authResult.error || !token) {
    const url = requestUrl(request, "/auth/sign-in");
    url.searchParams.set("error", "verification");
    url.searchParams.set("posting", posting);
    return NextResponse.redirect(url);
  }
  try {
    const application = await startCandidateApplication(token, posting);
    return NextResponse.redirect(
      requestUrl(request, `/candidate/applications/${application.id}`),
    );
  } catch (error) {
    const url = requestUrl(request, "/auth/sign-in");
    if (error instanceof CandidateProvisioningError && error.status === 404) {
      url.searchParams.set("error", "posting-unavailable");
      return NextResponse.redirect(url);
    }
    url.searchParams.set("error", "application-access");
    url.searchParams.set("posting", posting);
    return NextResponse.redirect(url);
  }
}
