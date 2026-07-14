import { render, screen } from "@testing-library/react";
import { ApplyForm } from "@/app/(public)/apply/apply-form";

describe("minimal contact form", () => {
  it("shows a sensitive-data warning and separate optional marketing consent", () => {
    render(<ApplyForm />);
    expect(screen.getByText(/Do not include your SIN/i)).toBeInTheDocument();
    expect(
      screen.getByLabelText(/I agree that Keeper Financial may contact me/i),
    ).toBeRequired();
    expect(
      screen.getByLabelText(/optional marketing communications/i),
    ).not.toBeRequired();
    expect(screen.queryByLabelText(/bank account/i)).not.toBeInTheDocument();
  });
});
