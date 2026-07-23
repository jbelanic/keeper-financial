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

export const fthbRebate = {
  label: "First-time home buyers’ (FTHB) GST/HST rebate",
  url: "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/gst-hst-businesses/gst-hst-rebates/first-time-home-buyers-gst-hst-rebate.html",
} as const;

// Short summary card shown on each mortgage product detail page, linking to the
// full broker page. Mirrors the approved broker copy's tone and guardrails.
export const brokerSummary: MortgageSection = {
  eyebrow: "Why work with a broker",
  heading: "Mortgage guidance built around your options",
  body: [
    "A mortgage broker can help you review available options from multiple lenders, understand lender requirements, and compare solutions based on your goals, income, credit profile, down payment, property type, and long-term plans.",
    "No broker can guarantee approval, a specific rate, or that every borrower will qualify. The goal is to help you understand your options before you commit.",
  ],
};

// Shared "why work with a broker" content, approved 2026-07-23. Rendered on
// every mortgage product detail page. General information only; it states no
// approval, rate, or qualification guarantee.
export const brokerInfoSections: MortgageSection[] = [
  {
    eyebrow: "Working with an Ontario mortgage broker",
    heading: "Mortgage guidance built around your options",
    body: [
      "Choosing a mortgage is one of the most important financial decisions many Ontario homeowners will make. A mortgage broker can help you review available mortgage options, understand lender requirements, and compare solutions based on your goals, income, credit profile, down payment, property type, and long-term plans.",
      "At Keeper Financial, our role is to help you make a more informed mortgage decision — whether you are buying a home, renewing your mortgage, refinancing, consolidating debt, or reviewing your current rate options.",
    ],
  },
  {
    eyebrow: "Why work with a mortgage broker?",
    heading: "Access to multiple lending options",
    body: [
      "When you work directly with one financial institution, you generally see that institution’s available mortgage products. A mortgage broker can help you review options from multiple lenders, which may include banks, credit unions, monoline lenders, trust companies, and alternative lenders where appropriate.",
      "This broader view can help you compare not only rates, but also terms, payment flexibility, prepayment privileges, penalties, qualification requirements, and lender conditions.",
    ],
  },
  {
    heading: "Advice based on your full mortgage picture",
    body: [
      "A competitive rate matters, but it is not the only factor. The right mortgage depends on how the product fits your financial situation and future plans.",
      "A licensed mortgage professional can help you consider questions such as:",
    ],
    points: [
      "How long do you expect to keep the property?",
      "Do you need payment flexibility?",
      "Are you planning to move, refinance, or renovate?",
      "How important are prepayment privileges?",
      "What type of penalty structure applies if you break the mortgage early?",
      "Does a fixed or variable rate better match your risk comfort and financial goals?",
    ],
  },
  {
    heading: "Support through the application process",
    body: [
      "Mortgage applications can involve income documents, credit review, down payment confirmation, property details, lender conditions, and closing timelines. A broker helps organize the process and can explain what lenders typically need to assess an application.",
      "Keeper Financial helps borrowers prepare, submit, and review mortgage applications with a clear process from first conversation to lender decision.",
    ],
  },
  {
    heading: "Help with purchases, renewals, and refinancing",
    body: [
      "Many borrowers only compare options when buying a home, but your mortgage should also be reviewed when renewing or refinancing.",
      "A mortgage broker can help you assess:",
    ],
    points: [
      "New home purchases",
      "First-time buyer options",
      "Mortgage renewals",
      "Refinancing to access equity",
      "Debt consolidation through mortgage financing",
      "Switching lenders",
      "Investment property financing",
      "Self-employed borrower scenarios",
      "Alternative lending options where suitable",
    ],
  },
  {
    heading: "Clearer comparison before you decide",
    body: [
      "Mortgage products can look similar at first glance, but details matter. A lower rate may come with limitations. A flexible product may be more suitable for some borrowers than the lowest advertised option. A mortgage broker can help you compare the practical differences between products before you make a decision.",
      "Keeper Financial helps you review the details clearly, including rate type, term length, amortization, payment structure, prepayment options, portability, penalties, and lender conditions.",
    ],
  },
  {
    eyebrow: "A broker does not guarantee approval — and that matters",
    heading: "No guarantee of approval or rate",
    body: [
      "No mortgage broker can guarantee approval, guarantee a specific rate, or guarantee that every borrower will qualify. Mortgage approval depends on lender review, borrower qualification, credit history, income, debt obligations, property details, down payment, and other underwriting requirements.",
      "What a broker can do is help you understand your position, prepare a stronger application, compare available options, and work with lenders that may be suitable for your circumstances.",
    ],
  },
  {
    eyebrow: "Local Ontario experience with online convenience",
    heading: "Local guidance, modern process",
    body: [
      "Keeper Financial combines local Ontario mortgage guidance with a modern online experience. You can start your mortgage review online, share information securely, and work with a licensed mortgage professional who can help explain your options clearly.",
      "Whether you prefer a fully online process or a more personal conversation, our goal is to make the mortgage process more transparent, organized, and easier to navigate.",
    ],
  },
  {
    heading: "When should you speak with a mortgage broker?",
    body: ["You may benefit from speaking with a mortgage broker if you are:"],
    points: [
      "Buying your first home",
      "Comparing mortgage rates",
      "Renewing within the next 6 to 12 months",
      "Considering refinancing",
      "Thinking about consolidating debt",
      "Buying an investment property",
      "Self-employed or recently changed income structure",
      "Unsure whether to choose fixed or variable",
      "Considering switching lenders",
      "Looking for a second opinion before signing a mortgage offer",
    ],
  },
  {
    heading: "How Keeper Financial helps",
    body: [
      "Keeper Financial helps Ontario borrowers review mortgage options with a clear, professional process:",
    ],
    points: [
      "Tell us about your mortgage goals.",
      "Review your financial and property details.",
      "Compare available mortgage options.",
      "Understand lender requirements and conditions.",
      "Submit an application when you are ready.",
      "Work with a licensed mortgage professional through the process.",
    ],
  },
  {
    eyebrow: "Important mortgage disclosure",
    heading: "General information only",
    body: [
      "Mortgage rates, products, and available options are subject to borrower qualification, lender approval, property approval, product availability, and change without notice. Not all borrowers will qualify. Information on this website is general in nature and should not be interpreted as a mortgage approval, rate guarantee, or commitment to lend. A licensed mortgage professional can help you review options based on your specific circumstances.",
    ],
  },
];

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
          "Federal and provincial programs for first-time buyers exist and change over time. Confirm current details from official government sources. For example, the federal First-time home buyers’ (FTHB) GST/HST rebate is described by the Canada Revenue Agency.",
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
