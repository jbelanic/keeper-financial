import type { NextRequest } from "next/server";

export function requestOrigin(request: NextRequest) {
  const host = request.headers.get("host") ?? request.nextUrl.host;
  const forwardedProtocol = request.headers
    .get("x-forwarded-proto")
    ?.split(",", 1)[0]
    ?.trim();
  const protocol = (forwardedProtocol || request.nextUrl.protocol).replace(
    /:$/,
    "",
  );

  return `${protocol}://${host}`;
}

export function requestUrl(request: NextRequest, path: string) {
  return new URL(path, requestOrigin(request));
}
