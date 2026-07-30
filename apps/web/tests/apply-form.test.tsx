import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ApplyForm } from "@/app/(public)/apply/apply-form";

function fillRequiredFields() {
  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: "Synthetic Visitor" },
  });
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "visitor@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Telephone"), {
    target: { value: "+1 416 555 0100" },
  });
  fireEvent.change(screen.getByLabelText("Preferred contact method"), {
    target: { value: "email" },
  });
  fireEvent.change(screen.getByLabelText("General mortgage objective"), {
    target: { value: "renewal" },
  });
  fireEvent.click(
    screen.getByLabelText(/I agree that Keeper Financial may contact me/i),
  );
}

function response(status: number, retryAfter?: string) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(retryAfter ? { "Retry-After": retryAfter } : {}),
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("minimal contact form", () => {
  it("identifies invalid fields, links their errors, and focuses the summary", async () => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    const { container } = render(<ApplyForm />);

    fireEvent.submit(container.querySelector("form")!);

    const summary = await screen.findByRole("alert");
    expect(summary).toHaveTextContent("Name is required.");
    expect(summary).toHaveTextContent("Email is required.");
    expect(summary).toHaveTextContent(
      "Service-contact acknowledgement is required.",
    );
    await waitFor(() => expect(summary).toHaveFocus());

    const name = screen.getByLabelText("Name");
    expect(name).toHaveAttribute("aria-invalid", "true");
    expect(name).toHaveAttribute("aria-describedby", "name-error");
    expect(document.getElementById("name-error")).toHaveTextContent(
      "Name is required.",
    );
    expect(
      screen.getByLabelText(/I agree that Keeper Financial may contact me/i),
    ).toHaveAttribute("aria-describedby", "service_contact_acknowledged-error");
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("shows warnings, a required service control, and unchecked optional marketing", () => {
    render(<ApplyForm />);
    expect(screen.getByText(/Do not include a SIN/i)).toBeInTheDocument();
    expect(
      screen.getByLabelText(/I agree that Keeper Financial may contact me/i),
    ).toBeRequired();
    expect(
      screen.getByLabelText(/optional marketing communications/i),
    ).not.toBeRequired();
    expect(
      screen.getByLabelText(/optional marketing communications/i),
    ).not.toBeChecked();
    expect(screen.queryByLabelText(/Preferred agent/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/bank account/i)).not.toBeInTheDocument();
  });

  it("uses a browser-valid telephone pattern under the Unicode Sets flag", () => {
    render(<ApplyForm />);
    const pattern = screen.getByLabelText("Telephone").getAttribute("pattern");

    expect(pattern).toBe("[0-9+\\.\\(\\) x\\-]+");
    expect(() => new RegExp(pattern!, "v")).not.toThrow();
  });

  it("submits safe attribution as hidden controlled data and resets only on success", async () => {
    const fetcher = vi.fn().mockResolvedValue(response(201));
    vi.stubGlobal("fetch", fetcher);
    const { container } = render(
      <ApplyForm preferredAgentSlug="published-agent" />,
    );
    fillRequiredFields();
    fireEvent.change(screen.getByLabelText("Brief message (optional)"), {
      target: { value: "Please call next week." },
    });

    fireEvent.submit(container.querySelector("form")!);

    await screen.findByRole("status");
    expect(fetcher).toHaveBeenCalledTimes(1);
    const body = JSON.parse(fetcher.mock.calls[0][1].body as string);
    expect(body.preferred_agent_slug).toBe("published-agent");
    expect(body).not.toHaveProperty("service_wording_version");
    expect(screen.getByLabelText("Name")).toHaveValue("");
  });

  it("prevents duplicate submission while the first request is pending", async () => {
    let resolveRequest!: (value: Response) => void;
    const fetcher = vi.fn().mockReturnValue(
      new Promise<Response>((resolve) => {
        resolveRequest = resolve;
      }),
    );
    vi.stubGlobal("fetch", fetcher);
    const { container } = render(<ApplyForm />);
    fillRequiredFields();
    const form = container.querySelector("form")!;

    fireEvent.submit(form);
    fireEvent.submit(form);

    expect(
      await screen.findByRole("button", { name: /Sending/i }),
    ).toBeDisabled();
    expect(fetcher).toHaveBeenCalledTimes(1);
    resolveRequest(response(201));
    await screen.findByRole("status");
  });

  it.each([
    [422, undefined, /Check the required fields/i],
    [429, "37", /wait 37 seconds/i],
    [503, undefined, /mortgage application is temporarily unavailable/i],
    [500, undefined, /could not send your request/i],
  ])(
    "maps HTTP %s to a useful non-internal focused error",
    async (status, retryAfter, message) => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(response(status, retryAfter)),
      );
      const { container } = render(<ApplyForm />);
      fillRequiredFields();
      fireEvent.change(screen.getByLabelText("Name"), {
        target: { value: "Preserved Visitor" },
      });

      fireEvent.submit(container.querySelector("form")!);

      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent(message);
      await waitFor(() => expect(alert).toHaveFocus());
      expect(screen.getByLabelText("Name")).toHaveValue("Preserved Visitor");
    },
  );

  it("preserves values and gives contact guidance on network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));
    const { container } = render(
      <ApplyForm unavailableContact="+1 709 700 7339 or support@example.com" />,
    );
    fillRequiredFields();

    fireEvent.submit(container.querySelector("form")!);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/\+1 709 700 7339 or support@example.com/i);
    expect(screen.getByLabelText("Email")).toHaveValue("visitor@example.com");
  });
});
