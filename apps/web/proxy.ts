import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { requestUrl } from "@/lib/request-url";

const applicationHosts = new Set([
  "apply.localhost:3000",
  "apply.keeperfinancial.ca",
]);

function publicSiteOriginForApplicationHost(host: string) {
  const fallback =
    host === "apply.localhost:3000"
      ? "http://localhost:3000"
      : "https://keeperfinancial.ca";
  try {
    const candidate = new URL(process.env.NEXT_PUBLIC_SITE_URL ?? fallback);
    const isLocalPublicSite =
      candidate.protocol === "http:" &&
      ["localhost", "127.0.0.1"].includes(candidate.hostname) &&
      candidate.port === "3000";
    const isProductionPublicSite =
      candidate.protocol === "https:" &&
      candidate.hostname === "keeperfinancial.ca" &&
      !candidate.port;
    if (
      (!isLocalPublicSite && !isProductionPublicSite) ||
      candidate.username ||
      candidate.password ||
      candidate.search ||
      candidate.hash
    ) {
      return fallback;
    }
    return candidate.origin;
  } catch {
    return fallback;
  }
}

function normalizedHost(value: string | null) {
  return value?.trim().toLowerCase() ?? "";
}

export async function proxy(request: NextRequest) {
  const host = normalizedHost(request.headers.get("host"));
  const forwardedHost = normalizedHost(request.headers.get("x-forwarded-host"));
  if (forwardedHost && forwardedHost !== host) {
    return new NextResponse("Invalid forwarded host", { status: 400 });
  }

  if (applicationHosts.has(host)) {
    if (request.nextUrl.pathname.startsWith("/api/v1/borrower-applications")) {
      const apiOrigin =
        process.env.API_INTERNAL_URL ??
        process.env.NEXT_PUBLIC_API_BASE_URL ??
        "http://localhost:8000";
      const target = new URL(
        `${request.nextUrl.pathname}${request.nextUrl.search}`,
        apiOrigin,
      );
      const headers = new Headers(request.headers);
      if (host === "apply.localhost:3000") {
        headers.set("host", "localhost:8000");
        headers.set("origin", "http://localhost:8000");
      } else {
        headers.set("host", "apply.keeperfinancial.ca");
        headers.set("origin", "https://apply.keeperfinancial.ca");
      }
      return NextResponse.rewrite(target, { request: { headers } });
    }

    if (
      request.nextUrl.pathname === "/" ||
      request.nextUrl.pathname === "/mortgage-application"
    ) {
      const target = request.nextUrl.clone();
      target.pathname = "/mortgage-application";
      return NextResponse.rewrite(target);
    }

    const target = new URL(
      `${request.nextUrl.pathname}${request.nextUrl.search}`,
      publicSiteOriginForApplicationHost(host),
    );
    return NextResponse.redirect(target);
  }

  const forwardedHeaders = new Headers(request.headers);
  if (
    !request.nextUrl.pathname.startsWith("/candidate") &&
    !request.nextUrl.pathname.startsWith("/admin") &&
    !request.nextUrl.pathname.startsWith("/auth")
  ) {
    return NextResponse.next({ request: { headers: forwardedHeaders } });
  }
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
  matcher: [
    "/((?!_next/static|_next/image|images/|favicon.ico|robots.txt|sitemap.xml).*)",
  ],
};
