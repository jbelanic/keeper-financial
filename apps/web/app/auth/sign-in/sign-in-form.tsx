import { Button, ErrorSummary, FormField } from "@keeper/ui";

const ERROR_MESSAGES: Record<string, string> = {
  credentials:
    "Sign-in failed. Check your credentials and verified account access.",
  "application-access":
    "Your identity was verified, but application access could not be prepared. Try again from this opportunity or contact support.",
  "posting-unavailable":
    "That opportunity is no longer available. Return to careers and select a published opportunity.",
  "admin-access":
    "This authenticated account does not have authorized brokerage administration access.",
  verification:
    "Account verification could not be completed. Retry from the selected opportunity.",
  session: "Your session is no longer valid. Sign in again to continue.",
};

export function SignInForm({
  posting,
  returnTo,
  error,
}: {
  posting?: string;
  returnTo: "/candidate" | "/admin" | "/agent";
  error?: string;
}) {
  const message = error ? ERROR_MESSAGES[error] : undefined;
  return (
    <form method="post" action="/auth/sign-in/submit">
      <ErrorSummary errors={message ? [message] : []} />
      {posting ? <input type="hidden" name="posting" value={posting} /> : null}
      <input type="hidden" name="returnTo" value={returnTo} />
      <FormField id="email" label="Email">
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
        />
      </FormField>
      <FormField id="password" label="Password">
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </FormField>
      <Button type="submit">Sign in securely</Button>
    </form>
  );
}
