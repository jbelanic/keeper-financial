type Environment = Record<string, string | undefined>;

const approvedPublicFacts = {
  displayName: "Keeper Financial",
  legalName: "Keeper Financial Inc.",
  regulatoryText: "FSCO # 13696",
  address: "380 Wellington Street, Tower B, 6th Floor, London ON, N6A 5B5",
  email: "support@keeperfinancial.ca",
  complaintsEmail: "complaints@keeperfinancial.ca",
  phoneDisplay: "+1 (709) 700-7339",
  phoneHref: "+17097007339",
  siteUrl: "https://keeperfinancial.ca",
  mortgageApplicationUrl: "https://apply.keeperfinancial.ca/",
} as const;

function controlledValue(value: string | undefined, fallback: string) {
  const normalized = value?.trim();
  return normalized ? normalized : fallback;
}

function controlledHttpsUrl(value: string | undefined, fallback: string) {
  try {
    const candidate = new URL(value?.trim() || fallback);
    if (
      candidate.protocol !== "https:" ||
      candidate.username ||
      candidate.password ||
      candidate.search ||
      candidate.hash
    ) {
      return fallback;
    }
    return candidate.toString();
  } catch {
    return fallback;
  }
}

function controlledSiteUrl(value: string | undefined, fallback: string) {
  try {
    const candidate = new URL(value?.trim() || fallback);
    const isLiveLocalOrigin =
      candidate.protocol === "http:" &&
      ["localhost", "127.0.0.1"].includes(candidate.hostname) &&
      candidate.port === "3000";
    if (
      (candidate.protocol !== "https:" && !isLiveLocalOrigin) ||
      candidate.username ||
      candidate.password ||
      candidate.search ||
      candidate.hash
    ) {
      return fallback;
    }
    return candidate.toString();
  } catch {
    return fallback;
  }
}

function optionalHttpsUrl(value: string | undefined) {
  if (!value?.trim()) return undefined;
  try {
    const candidate = new URL(value.trim());
    if (
      candidate.protocol !== "https:" ||
      candidate.username ||
      candidate.password ||
      candidate.search ||
      candidate.hash
    ) {
      return undefined;
    }
    return candidate.toString();
  } catch {
    return undefined;
  }
}

export function getPublicSiteConfig(environment: Environment = process.env) {
  const phoneDisplay = controlledValue(
    environment.NEXT_PUBLIC_PUBLIC_PHONE,
    approvedPublicFacts.phoneDisplay,
  );
  const phoneHref = controlledValue(
    environment.NEXT_PUBLIC_PUBLIC_PHONE_E164,
    approvedPublicFacts.phoneHref,
  ).replace(/[^+\d]/g, "");

  return {
    displayName: controlledValue(
      environment.NEXT_PUBLIC_BROKERAGE_DISPLAY_NAME,
      approvedPublicFacts.displayName,
    ),
    legalName: controlledValue(
      environment.NEXT_PUBLIC_BROKERAGE_LEGAL_NAME,
      approvedPublicFacts.legalName,
    ),
    regulatoryText: controlledValue(
      environment.NEXT_PUBLIC_BROKERAGE_REGULATORY_TEXT,
      approvedPublicFacts.regulatoryText,
    ),
    address: controlledValue(
      environment.NEXT_PUBLIC_PUBLIC_ADDRESS,
      approvedPublicFacts.address,
    ),
    email: controlledValue(
      environment.NEXT_PUBLIC_PUBLIC_EMAIL,
      approvedPublicFacts.email,
    ),
    complaintsEmail: controlledValue(
      environment.NEXT_PUBLIC_PUBLIC_COMPLAINTS_EMAIL,
      approvedPublicFacts.complaintsEmail,
    ),
    phoneDisplay,
    phoneHref: `tel:${phoneHref}`,
    emailHref: `mailto:${controlledValue(
      environment.NEXT_PUBLIC_PUBLIC_EMAIL,
      approvedPublicFacts.email,
    )}`,
    siteUrl: controlledSiteUrl(
      environment.NEXT_PUBLIC_SITE_URL,
      approvedPublicFacts.siteUrl,
    ),
    mortgageApplicationUrl: controlledHttpsUrl(
      environment.NEXT_PUBLIC_MORTGAGE_APPLICATION_URL,
      approvedPublicFacts.mortgageApplicationUrl,
    ),
    bookingUrl: optionalHttpsUrl(environment.NEXT_PUBLIC_BOOKING_URL),
    principalBroker:
      environment.NEXT_PUBLIC_PRINCIPAL_BROKER?.trim() || undefined,
  } as const;
}

export const siteConfig = getPublicSiteConfig();
export { approvedPublicFacts };
