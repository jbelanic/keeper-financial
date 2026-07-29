import { render, screen } from "@testing-library/react";
import BorrowerApplicationLayout from "@/app/(borrower)/mortgage-application/layout";
import { siteConfig } from "@/lib/site-config";

function publicPath(path: string) {
  return new URL(path, siteConfig.siteUrl).toString();
}

describe("borrower application layout", () => {
  it("offers an obvious escape path back to the public get-started page", () => {
    render(
      <BorrowerApplicationLayout>
        <p>Application body</p>
      </BorrowerApplicationLayout>,
    );

    expect(
      screen.getByRole("link", { name: "Exit application" }),
    ).toHaveAttribute("href", publicPath("/apply"));
  });
});
