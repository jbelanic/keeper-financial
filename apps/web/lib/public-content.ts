export const publicNavigation = [
  { label: "Mortgages", href: "/mortgages" },
  { label: "How it works", href: "/how-it-works" },
  { label: "Our agents", href: "/agents" },
  { label: "Join Keeper Financial", href: "/careers" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
] as const;

export const mortgageServices = [
  {
    slug: "purchase",
    title: "Purchase mortgages",
    shortTitle: "Buy a home",
    summary:
      "Understand the mortgage steps that can support a planned home purchase.",
    introduction:
      "A purchase mortgage is one part of a larger home-buying decision. Keeper Financial can help you organize questions, understand the process, and decide when to continue to a secure application.",
    considerations: [
      "Your intended timing and the type of property you are considering",
      "The difference between an early conversation and a full application",
      "The documents a secure mortgage provider may request later",
    ],
  },
  {
    slug: "refinancing",
    title: "Refinancing",
    shortTitle: "Refinance",
    summary:
      "Explore what it means to replace or change an existing mortgage before maturity.",
    introduction:
      "Refinancing can change the amount, term, or structure of an existing mortgage. Costs and suitability vary, so the first useful step is a clear conversation about your general objective—not sharing financial documents on this website.",
    considerations: [
      "Why you are considering a change and when you hope to make it",
      "Potential costs or trade-offs that should be discussed before proceeding",
      "When a secure application is appropriate for a complete review",
    ],
  },
  {
    slug: "renewals",
    title: "Mortgage renewals",
    shortTitle: "Plan a renewal",
    summary:
      "Prepare for an upcoming maturity with time to understand your options.",
    introduction:
      "A renewal is an opportunity to review your current mortgage and your priorities before accepting new terms. Starting early can create space for questions and an informed comparison process.",
    considerations: [
      "Your maturity date and the renewal information already provided to you",
      "Whether your needs or plans have changed since your last term",
      "Questions to raise before choosing a new term or lender",
    ],
  },
  {
    slug: "first-time-buyers",
    title: "First-time home buyers",
    shortTitle: "First-time buyers",
    summary:
      "Learn the stages of a first purchase in clear, manageable language.",
    introduction:
      "Buying a first home can introduce unfamiliar terms and timelines. Keeper Financial offers a conversation-first path so you can understand the sequence before deciding whether to begin a secure application.",
    considerations: [
      "The difference between planning, pre-approval, and a final lending decision",
      "Questions about purchase costs beyond the mortgage itself",
      "How to keep sensitive financial information inside an approved secure platform",
    ],
  },
  {
    slug: "investment-properties",
    title: "Investment properties",
    shortTitle: "Investment properties",
    summary:
      "Discuss the mortgage process for a property intended as an investment.",
    introduction:
      "Investment-property financing can involve different considerations from a principal residence. An initial conversation can help clarify the process while any detailed financial assessment remains in the approved secure application platform.",
    considerations: [
      "The intended use of the property and your general timeline",
      "Questions to prepare for a complete lender review",
      "Why eligibility and lending decisions can only follow a full assessment",
    ],
  },
] as const;

export const processSteps = [
  {
    title: "Start with your goal",
    description:
      "Choose a general mortgage topic and decide whether you want a conversation first or are ready for a secure application.",
  },
  {
    title: "Talk through the process",
    description:
      "Use the published phone, email, or minimal contact form. Do not send sensitive financial or identity information.",
  },
  {
    title: "Continue securely",
    description:
      "When appropriate, move to Keeper Financial’s approved external application platform for detailed information and documents.",
  },
  {
    title: "Review next steps",
    description:
      "A mortgage professional can explain what happens next. Approval, rates, and eligibility always depend on a complete assessment.",
  },
] as const;

export function getMortgageService(slug: string) {
  return mortgageServices.find((service) => service.slug === slug);
}
