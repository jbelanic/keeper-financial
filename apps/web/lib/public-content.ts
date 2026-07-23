export const publicNavigation = [
  { label: "Mortgages", href: "/mortgages" },
  { label: "How it works", href: "/how-it-works" },
  { label: "Find an Agent", href: "/agents" },
  { label: "Join Keeper Financial", href: "/careers" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
] as const;

export type MortgageSection = {
  eyebrow?: string;
  heading: string;
  body?: string[];
  points?: string[];
};

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
    sections: [
      {
        eyebrow: "Why prepare early",
        heading: "A conversation before you shop",
        body: [
          "Starting the mortgage conversation before you shop gives you a clearer picture of budget, timeline and the steps ahead. It does not commit you to a product.",
        ],
      },
      {
        heading: "What a mortgage conversation can cover",
        points: [
          "how a purchase amount is assessed",
          "the difference between an early discussion, a pre-approval and final lender approval",
          "term and rate-structure options in plain language",
          "costs that sit outside the mortgage itself",
        ],
      },
      {
        heading: "Costs beyond the mortgage",
        points: [
          "down payment",
          "legal fees",
          "appraisal and inspection",
          "provincial land-transfer tax where applicable",
          "moving and ongoing carrying costs",
        ],
      },
    ] as MortgageSection[],
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
    sections: [
      {
        eyebrow: "Why borrowers review a refinance",
        heading: "Reasons people consider it",
        points: [
          "consolidating higher-cost debt",
          "funding renovations",
          "accessing equity",
          "changing the payment or term structure",
        ],
      },
      {
        heading: "Costs and trade-offs to weigh",
        points: [
          "a charge may apply to end your current term early",
          "legal and appraisal fees can apply",
          "a longer amortization usually means more total interest",
          "it changes your equity position",
        ],
      },
      {
        heading: "How the review works",
        points: [
          "an assessment of your current mortgage",
          "a comparison of options against your stated goal",
          "a complete application only when you choose to proceed",
        ],
      },
    ] as MortgageSection[],
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
    sections: [
      {
        eyebrow: "Your renewal letter",
        heading: "An offer, not a requirement",
        body: [
          "You are not obliged to sign the renewal your lender sends. The weeks before maturity are a normal window to review other terms.",
        ],
      },
      {
        heading: "What to review before you decide",
        points: [
          "your maturity date and any offer received",
          "the offered term length and how it fits your plans",
          "prepayment and portability features",
          "what changing lenders could involve",
        ],
      },
      {
        heading: "When to start",
        points: [
          "many borrowers begin 4 to 6 months before maturity",
          "timelines vary by lender — confirm your exact date",
        ],
      },
    ] as MortgageSection[],
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
    sections: [
      {
        eyebrow: "Stages of a first purchase",
        heading: "From planning to possession",
        points: [
          "planning and budget",
          "an early discussion or pre-approval",
          "an offer with conditions",
          "final lender approval",
          "closing and possession",
        ],
      },
      {
        eyebrow: "Programs and incentives",
        heading: "Confirm current details from official sources",
        body: [
          "Federal and provincial programs for first-time buyers exist and change over time. Confirm current details from official government sources.",
        ],
      },
      {
        heading: "What the application asks for",
        points: [
          "identification",
          "income and employment",
          "existing debts",
          "source of down payment",
          "housing history",
        ],
      },
    ] as MortgageSection[],
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
    sections: [
      {
        eyebrow: "How investment financing can differ",
        heading: "Generally different from a residence",
        points: [
          "minimum down payments are often higher",
          "qualification may consider projected rental income within set limits",
          "rates and fees can differ",
          "lender guidelines vary",
        ],
      },
      {
        heading: "What to prepare",
        points: [
          "property type and location",
          "expected rents",
          "your existing property portfolio",
          "your financing goals",
        ],
      },
      {
        heading: "Separate advice",
        body: [
          "Tax, accounting or legal advice is often appropriate and is separate from a mortgage review.",
        ],
      },
    ] as MortgageSection[],
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
