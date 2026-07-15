import { NextResponse, type NextRequest } from "next/server";
import {
  startCandidateApplication,
  isSafePostingSlug,
} from "@/lib/candidate-provisioning";
import { getSupabaseServerClient } from "@/lib/supabase-server";

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const posting = request.nextUrl.searchParams.get("posting") ?? "";
  if (!code || !isSafePostingSlug(posting)) {
    return NextResponse.redirect(
      new URL("/auth/sign-in?error=verification", request.url),
    );
  }
  const supabase = await getSupabaseServerClient();
  const { data, error } = await supabase.auth.exchangeCodeForSession(code);
  const token = data.session?.access_token;
  if (error || !token) {
    return NextResponse.redirect(
      new URL("/auth/sign-in?error=verification", request.url),
    );
  }
  try {
    const application = await startCandidateApplication(token, posting);
    return NextResponse.redirect(
      new URL(`/candidate/applications/${application.id}`, request.url),
    );
  } catch {
    return NextResponse.redirect(
      new URL(`/auth/sign-in?error=application-access`, request.url),
    );
  }
}
