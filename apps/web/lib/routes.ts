export const PUBLIC_ROUTES = [
  "/",
  "/mortgages",
  "/apply",
  "/agents",
  "/agents/[slug]",
  "/careers",
  "/careers/[slug]",
  "/privacy",
  "/complaints",
  "/accessibility",
  "/contact",
  "/auth/sign-in",
] as const;

export const CANDIDATE_ROUTES = [
  "/candidate",
  "/candidate/application",
  "/candidate/onboarding",
  "/candidate/documents",
] as const;

export const ADMIN_ROUTES = [
  "/admin",
  "/admin/candidates",
  "/admin/onboarding",
  "/admin/agents",
  "/admin/content",
] as const;
