import { NextRequest, NextResponse } from "next/server";

const PUBLIC_FILE = /\.[^/]+$/;

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    PUBLIC_FILE.test(pathname) ||
    pathname === "/ar" ||
    pathname.startsWith("/ar/") ||
    pathname === "/en" ||
    pathname.startsWith("/en/")
  ) {
    return NextResponse.next();
  }
  const url = request.nextUrl.clone();
  url.pathname = `/ar${pathname === "/" ? "" : pathname}`;
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
