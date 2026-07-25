import { approvedPublicFacts, getPublicSiteConfig } from "@/lib/site-config";

describe("controlled public configuration", () => {
  it("uses only the owner-approved facts when environment values are missing", () => {
    const config = getPublicSiteConfig({});
    expect(config.legalName).toBe("Keeper Financial Inc.");
    expect(config.regulatoryText).toBe("FSCO # 13696");
    expect(config.address).toBe(approvedPublicFacts.address);
    expect(config.email).toBe(approvedPublicFacts.email);
    expect(config.phoneDisplay).toBe(approvedPublicFacts.phoneDisplay);
    expect(config.mortgageApplicationUrl).toBe(
      approvedPublicFacts.mortgageApplicationUrl,
    );
    expect(config.principalBroker).toBeUndefined();
    expect(config.bookingUrl).toBeUndefined();
    expect(JSON.stringify(config)).not.toMatch(/pending owner|13372|NMLS/i);
  });

  it("fails optional booking and unverified values closed", () => {
    const config = getPublicSiteConfig({
      NEXT_PUBLIC_BOOKING_URL: "javascript:alert(1)",
      NEXT_PUBLIC_PRINCIPAL_BROKER: "   ",
      NEXT_PUBLIC_BROKERAGE_REGULATORY_TEXT: "   ",
    });
    expect(config.bookingUrl).toBeUndefined();
    expect(config.principalBroker).toBeUndefined();
    expect(config.regulatoryText).toBe(approvedPublicFacts.regulatoryText);
  });

  it("accepts only the live loopback HTTP site origin exception", () => {
    expect(
      getPublicSiteConfig({ NEXT_PUBLIC_SITE_URL: "http://localhost:3000" })
        .siteUrl,
    ).toBe("http://localhost:3000/");
    expect(
      getPublicSiteConfig({ NEXT_PUBLIC_SITE_URL: "http://remote.example" })
        .siteUrl,
    ).toBe(approvedPublicFacts.siteUrl);
  });

  it("accepts only exact local or production borrower application origins", () => {
    expect(
      getPublicSiteConfig({
        NEXT_PUBLIC_MORTGAGE_APPLICATION_URL: "http://apply.localhost:3000",
      }).mortgageApplicationUrl,
    ).toBe("http://apply.localhost:3000/");
    expect(
      getPublicSiteConfig({
        NEXT_PUBLIC_MORTGAGE_APPLICATION_URL:
          "https://apply.keeperfinancial.ca.evil.example",
      }).mortgageApplicationUrl,
    ).toBe(approvedPublicFacts.mortgageApplicationUrl);
  });
});
