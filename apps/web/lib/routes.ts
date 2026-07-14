export const PUBLIC_ROUTES = [
  "/",
  "/mortgages",
  "/mortgages/purchase",
  "/mortgages/refinancing",
  "/mortgages/renewals",
  "/mortgages/first-time-buyers",
  "/mortgages/investment-properties",
  "/how-it-works",
  "/apply",
  "/agents",
  "/agents/[slug]",
  "/careers",
  "/careers/[slug]",
  "/about",
  "/privacy",
  "/complaints",
  "/accessibility",
  "/contact",
  "/auth/sign-in",
] as const;

export const SITEMAP_ROUTES = [
  "/",
  "/mortgages",
  "/mortgages/purchase",
  "/mortgages/refinancing",
  "/mortgages/renewals",
  "/mortgages/first-time-buyers",
  "/mortgages/investment-properties",
  "/how-it-works",
  "/apply",
  "/agents",
  "/careers",
  "/about",
  "/contact",
  "/privacy",
  "/complaints",
  "/accessibility",
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
