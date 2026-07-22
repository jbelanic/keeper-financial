import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { requestUrl } from "@/lib/request-url";

export async function proxy(request: NextRequest) {
  const forwardedHeaders = new Headers(request.headers);
  let response = NextResponse.next({ request: { headers: forwardedHeaders } });
  const supabase = createServerClient(
    process.env.SUPABASE_INTERNAL_URL ??
      process.env.NEXT_PUBLIC_SUPABASE_URL ??
      "http://127.0.0.1:54321",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "local-placeholder",
    {
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll: (items) => {
          items.forEach(({ name, value }) => request.cookies.set(name, value));
          response = NextResponse.next({
            request: { headers: forwardedHeaders },
          });
          items.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          );
        },
      },
    },
  );
  // A server-validated user lookup refreshes an eligible expired access token
  // and clears invalid/revoked sessions without authorizing application access.
  try {
    await supabase.auth.getUser();
  } catch {
    if (
      request.nextUrl.pathname.startsWith("/candidate") ||
      request.nextUrl.pathname.startsWith("/admin")
    ) {
      const signIn = requestUrl(request, "/auth/sign-in");
      signIn.searchParams.set("error", "session");
      signIn.searchParams.set(
        "returnTo",
        request.nextUrl.pathname.startsWith("/admin") ? "/admin" : "/candidate",
      );
      return NextResponse.redirect(signIn);
    }
  }
  return response;
}

export const config = {
  matcher: ["/candidate/:path*", "/admin/:path*", "/auth/:path*"],
};
