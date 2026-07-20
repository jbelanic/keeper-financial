export const publicNavigation = [
  { label: "Mortgages", href: "/mortgages" },
  { label: "How it works", href: "/how-it-works" },
  { label: "Find an Agent", href: "/agents" },
  { label: "Join Keeper Financial", href: "/careers" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
] as const;

export const mortgageServices = [
  {
    slug: "purchase",
    title: "Planning a home purchase",
    eyebrow: "Purchase mortgages",
    lead: "Understand the mortgage steps that may form part of a planned home purchase and prepare questions before beginning a complete application.",
    shortTitle: "Purchase",
    summary:
      "Understand the mortgage steps that may form part of a planned home purchase.",
    considerations: [
      "your general timeline and the type of property you are considering",
      "the difference between an early conversation, a pre-approval and a final lending decision",
      "when detailed financial information and documents may be required through the mortgage application",
    ],
  },
  {
    slug: "refinancing",
    title: "Considering a refinance",
    eyebrow: "Refinancing",
    lead: "A refinance may change the amount, term or structure of an existing mortgage. A complete review is needed to assess available options, costs and suitability.",
    shortTitle: "Refinance",
    summary:
      "A refinance may change the amount, term or structure of an existing mortgage.",
    considerations: [
      "why you are considering a change and your preferred timing",
      "potential charges, fees and other trade-offs to discuss before proceeding",
      "when to continue to a complete mortgage application",
    ],
  },
  {
    slug: "renewals",
    title: "Preparing for a mortgage renewal",
    eyebrow: "Mortgage renewals",
    lead: "Review your current mortgage, renewal information and priorities before deciding on your next term.",
    shortTitle: "Renewals",
    summary:
      "Review your current mortgage, renewal information and priorities before deciding on your next term.",
    considerations: [
      "your maturity date and any renewal offer you have received",
      "whether your needs or plans have changed",
      "questions about terms and options that require a complete review",
    ],
  },
  {
    slug: "first-time-buyers",
    title: "Buying your first home",
    eyebrow: "First-time home buyers",
    lead: "Learn the main stages of a first purchase and prepare for the information a complete mortgage application may require.",
    shortTitle: "First-time buyers",
    summary:
      "Learn the main stages of a first purchase and prepare for the information a complete mortgage application may require.",
    considerations: [
      "the difference between early planning, a pre-approval and final lender approval",
      "purchase costs and responsibilities beyond the mortgage itself",
      "how to provide detailed financial and identity information securely",
    ],
  },
  {
    slug: "investment-properties",
    title: "Financing an investment property",
    eyebrow: "Investment properties",
    lead: "Mortgage requirements for an investment property may differ from those for a principal residence. A complete review is required to assess a specific application.",
    shortTitle: "Investment properties",
    summary:
      "Mortgage requirements for an investment property may differ from those for a principal residence.",
    considerations: [
      "the intended use of the property and your general timeline",
      "questions to prepare for the mortgage application",
      "whether separate tax, accounting or legal advice may be appropriate",
    ],
  },
] as const;

export const processSteps = [
  {
    title: "Choose your topic",
    description:
      "Review information about purchases, refinancing, renewals, first homes or investment properties.",
  },
  {
    title: "Contact Keeper Financial",
    description:
      "Share your name, contact details, general mortgage goal and non-sensitive context.",
  },
  {
    title: "Continue securely",
    description:
      "Use the configured mortgage application service for detailed financial, credit, identity and document information.",
  },
  {
    title: "Review the next step",
    description:
      "A mortgage professional can explain the process after the required information is available.",
  },
] as const;

export function getMortgageService(slug: string) {
  return mortgageServices.find((service) => service.slug === slug);
}
