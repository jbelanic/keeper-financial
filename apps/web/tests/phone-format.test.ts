import { describe, expect, it } from "vitest";
import {
  formatPhoneDisplay,
  isAcceptablePhoneInput,
  nanpNationalNumber,
  PHONE_INPUT_PATTERN,
  phoneTelHref,
} from "@/lib/phone";

describe("North American phone display", () => {
  it("renders one standard form however the number was stored", () => {
    expect(formatPhoneDisplay("+15191234567")).toBe("(519) 123-4567");
    expect(formatPhoneDisplay("519-123-4567")).toBe("(519) 123-4567");
    expect(formatPhoneDisplay("5191234567")).toBe("(519) 123-4567");
    expect(formatPhoneDisplay("(519) 123-4567")).toBe("(519) 123-4567");
  });

  it("leaves a value it cannot read untouched instead of hiding it", () => {
    expect(formatPhoneDisplay("555-123")).toBe("555-123");
    expect(formatPhoneDisplay(null)).toBe("");
  });

  it("builds a dialable tel link", () => {
    expect(phoneTelHref("+15191234567")).toBe("tel:+15191234567");
    expect(phoneTelHref("(519) 123-4567")).toBe("tel:+15191234567");
    expect(phoneTelHref("+442079460958")).toBe("tel:+442079460958");
  });
});

describe("phone entry acceptance", () => {
  it("accepts the way people type a Canadian or US number", () => {
    for (const typed of [
      "5195550123",
      "519-555-0123",
      "(519) 555-0123",
      "+1 519 555 0123",
    ]) {
      expect(isAcceptablePhoneInput(typed)).toBe(true);
      expect(nanpNationalNumber(typed)).toBe("5195550123");
    }
  });

  it("accepts an explicit international number", () => {
    expect(isAcceptablePhoneInput("+44 20 7946 0958")).toBe(true);
  });

  it("refuses junk, letters and a bare digit run that is not a number", () => {
    expect(isAcceptablePhoneInput("519-555")).toBe(false);
    expect(isAcceptablePhoneInput("call me")).toBe(false);
    expect(isAcceptablePhoneInput("44123456789")).toBe(false);
    expect(isAcceptablePhoneInput("")).toBe(false);
  });

  it("declares a browser pattern that is valid under the Unicode Sets flag", () => {
    expect(() => new RegExp(PHONE_INPUT_PATTERN, "v")).not.toThrow();
  });
});
