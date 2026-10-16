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
    lead: "What usually happens between planning a purchase and getting the keys, and what to prepare before you apply.",
    shortTitle: "Purchase",
    summary:
      "What happens between planning a home purchase and getting the keys.",
    considerations: [
      "Your timeline and the kind of property you are considering",
      "The difference between an early conversation, a pre-approval and a final lending decision",
      "When we will need your financial details and documents (always inside the secure application)",
    ],
    sections: [
      {
        eyebrow: "Why prepare early",
        heading: "A conversation before you shop",
        body: [
          "Starting the mortgage conversation before you shop gives you a clearer picture of your budget, your timeline and the steps ahead. It does not commit you to a product.",
        ],
      },
      {
        heading: "What a mortgage conversation can cover",
        points: [
          "How a purchase amount is assessed",
          "The difference between an early discussion, a pre-approval and final lender approval",
          "Term and rate options, in plain language",
          "Costs that sit outside the mortgage itself",
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
    lead: "Change the amount, term or structure of your mortgage, and understand the costs before you commit.",
    shortTitle: "Refinance",
    summary:
      "Change your mortgage’s amount, term or structure — and know the costs first.",
    considerations: [
      "Why you are considering a change, and your preferred timing",
      "The fees, charges and trade-offs to weigh before you proceed",
      "When a complete mortgage application is needed",
    ],
    sections: [
      {
        eyebrow: "Why borrowers review a refinance",
        heading: "Reasons people consider it",
        points: [
          "Consolidating higher-cost debt",
          "Funding renovations",
          "Accessing equity",
          "Changing the payment or term structure",
        ],
      },
      {
        heading: "Costs and trade-offs to weigh",
        points: [
          "A charge may apply to end your current term early",
          "Legal and appraisal fees can apply",
          "A longer amortization usually means more total interest",
          "It changes your equity position",
        ],
      },
      {
        heading: "How the review works",
        points: [
          "An assessment of your current mortgage",
          "A comparison of options against your stated goal",
          "A complete application only when you choose to proceed",
        ],
      },
    ] as MortgageSection[],
  },
  {
    slug: "renewals",
    title: "Preparing for a mortgage renewal",
    eyebrow: "Mortgage renewals",
    lead: "Your lender’s renewal letter is not your only option. Here is what is worth comparing before you decide.",
    shortTitle: "Renewals",
    summary:
      "Your renewal letter is not your only option. Here is what is worth comparing.",
    considerations: [
      "Your maturity date and any renewal offer you have received",
      "Whether your needs or plans have changed",
      "Questions about terms and options that need a complete review",
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
          "Your maturity date and any offer received",
          "The offered term length and how it fits your plans",
          "Prepayment and portability features",
          "What changing lenders could involve",
        ],
      },
      {
        heading: "When to start",
        points: [
          "Many borrowers begin 4 to 6 months before maturity",
          "Timelines vary by lender — confirm your exact date",
        ],
      },
    ] as MortgageSection[],
  },
  {
    slug: "first-time-buyers",
    title: "Buying your first home",
    eyebrow: "First-time home buyers",
    lead: "A step-by-step look at your first purchase, from budget to keys, and what the application will ask for.",
    shortTitle: "First-time buyers",
    summary: "A step-by-step look at your first purchase, from budget to keys.",
    considerations: [
      "The difference between early planning, a pre-approval and final lender approval",
      "Purchase costs and responsibilities beyond the mortgage itself",
      "How to provide detailed financial and identity information securely",
    ],
    sections: [
      {
        eyebrow: "Stages of a first purchase",
        heading: "From planning to possession",
        points: [
          "Planning and budget",
          "An early discussion or pre-approval",
          "An offer with conditions",
          "Final lender approval",
          "Closing and possession",
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
    lead: "Investment mortgages work differently from a principal residence. Here is what matters before you commit.",
    shortTitle: "Investment properties",
    summary:
      "Investment mortgages work differently from a principal residence.",
    considerations: [
      "The intended use of the property and your general timeline",
      "Questions to prepare for the mortgage application",
      "Whether separate tax, accounting or legal advice may be appropriate",
    ],
    sections: [
      {
        eyebrow: "How investment financing can differ",
        heading: "Generally different from a residence",
        points: [
          "Minimum down payments are often higher",
          "Qualification may consider projected rental income within set limits",
          "Rates and fees can differ",
          "Lender guidelines vary",
        ],
      },
      {
        heading: "What to prepare",
        points: [
          "Property type and location",
          "Expected rents",
          "Your existing property portfolio",
          "Your financing goals",
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
      "Share your name, contact details and a short note about what you need.",
  },
  {
    title: "Continue securely",
    description:
      "Continue in our secure application, where your financial, credit and identity details belong.",
  },
  {
    title: "Review the next step",
    description:
      "A mortgage professional can explain the process after the required information is available.",
  },
] as const;

export const recruitmentContent = {
  hero: {
    eyebrow: "Mortgage agent careers in Ontario",
    title: "Build your mortgage business. Keep more control.",
    lead: "Keeper offers competitive compensation, more earning potential, access to lead opportunities and the autonomy to run your business your way, backed by hands-on coaching, mentorship and dedicated brokerage support.",
    imageAlt:
      "Four professionals collaborating around a table in a modern office setting",
    ctaLabel: "Explore the current opportunity",
    ctaNote: "Review the role before creating an account.",
  },
  benefits: {
    eyebrow: "Why Keeper",
    heading: "What you can build with Keeper",
    lead: "A brokerage relationship designed to give ambitious mortgage professionals room to grow, backed by practical support.",
    items: [
      {
        heading: "More room to earn",
        body: "Competitive compensation creates more room to grow your earning potential.",
      },
      {
        heading: "Run your business your way",
        body: "Keep autonomy over how you build client relationships, with brokerage responsibilities and support clearly in place.",
      },
      {
        heading: "Leads available",
        body: "Access lead opportunities alongside the business and relationships you develop yourself.",
      },
      {
        heading: "Hands-on support",
        body: "Build with coaching, mentorship and dedicated brokerage support behind you.",
      },
      {
        heading: "Broader lender access",
        body: "Work with access to a broad lender network and support navigating available options.",
      },
    ],
  },
  journey: {
    eyebrow: "Candidate journey",
    heading: "What the candidate journey looks like",
    lead: "Start by understanding the opportunity. An account is only needed when you choose to apply.",
    steps: [
      {
        heading: "Review the role",
        body: "Read the details — no account needed.",
      },
      {
        heading: "Create an account and start",
        body: "Start your application and pick it up any time from the candidate portal.",
      },
      {
        heading: "Track your progress",
        body: "See your status and messages in the portal.",
      },
      {
        heading: "Complete onboarding if selected",
        body: "Selected candidates move into our onboarding process.",
      },
    ],
  },
  home: {
    eyebrow: "Mortgage agent careers in Ontario",
    heading: "Build your mortgage business. Keep more control.",
    body: "Explore a Keeper career with competitive compensation, autonomy, lead opportunities and hands-on brokerage support.",
    ctaLabel: "Explore careers at Keeper",
  },
  application: {
    eyebrow: "Application process",
    heading: "How the application works",
    lead: "Choose the path that fits you. Both keep your application tied to this role.",
    steps: [
      {
        heading: "Create your account",
        body: "Create an account or sign in with an existing account from this role.",
      },
      {
        heading: "Complete your application",
        body: "Save your draft and submit it once the required sections are complete.",
      },
      {
        heading: "Track status and messages",
        body: "Your updates stay available in the portal.",
      },
      {
        heading: "Onboard if selected",
        body: "Selection may lead to our onboarding process.",
      },
    ],
  },
} as const;

export function getMortgageService(slug: string) {
  return mortgageServices.find((service) => service.slug === slug);
}
