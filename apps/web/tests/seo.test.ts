import accessibilityPage, {
  metadata as accessibilityMetadata,
} from "@/app/(public)/accessibility/page";
import { metadata as aboutMetadata } from "@/app/(public)/about/page";
import { metadata as agentsMetadata } from "@/app/(public)/agents/page";
import { metadata as applyMetadata } from "@/app/(public)/apply/page";
import { metadata as careersMetadata } from "@/app/(public)/careers/page";
import { metadata as complaintsMetadata } from "@/app/(public)/complaints/page";
import { metadata as contactMetadata } from "@/app/(public)/contact/page";
import { metadata as howItWorksMetadata } from "@/app/(public)/how-it-works/page";
import {
  generateMetadata as generateMortgageMetadata,
  generateStaticParams,
} from "@/app/(public)/mortgages/[slug]/page";
import { metadata as mortgagesMetadata } from "@/app/(public)/mortgages/page";
import { metadata as homeMetadata } from "@/app/(public)/page";
import { metadata as privacyMetadata } from "@/app/(public)/privacy/page";
import robots from "@/app/robots";
import sitemap from "@/app/sitemap";
import { SITEMAP_ROUTES } from "@/lib/routes";

const staticMetadata = [
  homeMetadata,
  mortgagesMetadata,
  howItWorksMetadata,
  aboutMetadata,
  contactMetadata,
  applyMetadata,
  agentsMetadata,
  careersMetadata,
  privacyMetadata,
  complaintsMetadata,
  accessibilityMetadata,
];

describe("public discovery metadata", () => {
  it("gives every finished public page a unique title and description", async () => {
    // Referencing the page export prevents a metadata-only test from masking a broken page module.
    expect(accessibilityPage).toBeTypeOf("function");
    const mortgageMetadata = await Promise.all(
      generateStaticParams().map(({ slug }) =>
        generateMortgageMetadata({ params: Promise.resolve({ slug }) }),
      ),
    );
    const allMetadata = [...staticMetadata, ...mortgageMetadata];
    const titles = allMetadata.map((item) => item.title);
    const descriptions = allMetadata.map((item) => item.description);

    expect(titles.every((title) => typeof title === "string")).toBe(true);
    expect(
      descriptions.every((description) => typeof description === "string"),
    ).toBe(true);
    expect(new Set(titles).size).toBe(titles.length);
    expect(new Set(descriptions).size).toBe(descriptions.length);
    expect(
      allMetadata.every(
        (item) => item.alternates?.canonical && item.openGraph?.description,
      ),
    ).toBe(true);
  });

  it("lists only intended public routes in the sitemap", () => {
    const urls = sitemap().map((entry) => new URL(entry.url).pathname);
    expect(urls).toEqual([...SITEMAP_ROUTES]);
    expect(urls.some((route) => route.startsWith("/candidate"))).toBe(false);
    expect(urls.some((route) => route.startsWith("/admin"))).toBe(false);
    expect(urls.some((route) => route.includes("[slug]"))).toBe(false);
  });

  it("blocks private portal and sign-in areas from crawlers", () => {
    const rules = robots().rules;
    expect(rules).not.toBeInstanceOf(Array);
    if (Array.isArray(rules))
      throw new Error("Expected one global robots rule");
    expect(rules.disallow).toEqual(
      expect.arrayContaining(["/candidate/", "/admin/", "/auth/"]),
    );
  });
});
