"use client";

import { createBrowserClient } from "@supabase/ssr";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Button, ErrorSummary, FormField } from "@keeper/ui";
import type { MfaReturnTo } from "@/lib/mfa-return";

type Stage = "loading" | "enroll" | "verify" | "verified" | "error";
type Enrollment = {
  factorId: string;
  qrCode: string;
  secret: string;
};

const GENERIC_ERROR =
  "Multi-factor authentication could not be completed. Keep this page open and try again.";

export function normalizeTotpQrSource(rawQr: unknown): string | null {
  if (typeof rawQr !== "string") return null;
  const normalized = rawQr.trimEnd();
  if (!normalized) return null;
  const dataUriPrefix = /^data:image\/svg\+xml(?:;[^,]*)?,/i.exec(normalized);
  if (dataUriPrefix) {
    return normalized.slice(dataUriPrefix[0].length).trim() ? normalized : null;
  }
  if (normalized.startsWith("data:")) return null;
  const svg = normalized.trimStart();
  if (!svg.startsWith("<svg") || !svg.endsWith("</svg>")) return null;
  return `data:image/svg+xml;utf-8,${encodeURIComponent(svg)}`;
}

export function MfaEnrollment({ returnTo }: { returnTo: MfaReturnTo }) {
  const candidateFlow = returnTo.startsWith("/candidate");
  const supabase = useMemo(
    () =>
      createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321",
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "local-placeholder",
      ),
    [],
  );
  const [stage, setStage] = useState<Stage>("loading");
  const [factorId, setFactorId] = useState<string | null>(null);
  const [staleFactorIds, setStaleFactorIds] = useState<string[]>([]);
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isEnrolling, setIsEnrolling] = useState(false);

  useEffect(() => {
    let active = true;
    async function inspectFactors() {
      try {
        const assurance =
          await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
        if (assurance.error || !assurance.data)
          throw new Error("assurance unavailable");
        if (assurance.data.currentLevel === "aal2") {
          if (active) setStage("verified");
          return;
        }
        const factors = await supabase.auth.mfa.listFactors();
        if (factors.error || !factors.data)
          throw new Error("factors unavailable");
        const verified = factors.data.totp.find(
          (factor) => factor.status === "verified",
        );
        if (verified) {
          if (active) {
            setFactorId(verified.id);
            setStage("verify");
          }
          return;
        }
        if (active) {
          setStaleFactorIds(
            factors.data.all
              .filter(
                (factor) =>
                  factor.factor_type === "totp" &&
                  factor.status === "unverified",
              )
              .map((factor) => factor.id),
          );
          setStage("enroll");
        }
      } catch {
        if (active) {
          setError(GENERIC_ERROR);
          setStage("error");
        }
      }
    }
    void inspectFactors();
    return () => {
      active = false;
    };
  }, [supabase]);

  async function beginEnrollment() {
    if (isEnrolling) return;
    setIsEnrolling(true);
    setError(null);
    try {
      for (const staleFactorId of staleFactorIds) {
        const removal = await supabase.auth.mfa.unenroll({
          factorId: staleFactorId,
        });
        if (removal.error) throw new Error("stale factor removal failed");
        setStaleFactorIds((current) =>
          current.filter((factorId) => factorId !== staleFactorId),
        );
      }
      const result = await supabase.auth.mfa.enroll({
        factorType: "totp",
        friendlyName: candidateFlow
          ? "Keeper Financial candidate documents"
          : "Keeper Financial administration",
        issuer: "Keeper Financial",
      });
      if (result.error || !result.data) throw new Error("enrollment failed");
      const enrolledFactorId = result.data.id;
      const qrCode = normalizeTotpQrSource(result.data.totp.qr_code);
      if (!qrCode) {
        setStaleFactorIds((current) =>
          current.includes(enrolledFactorId)
            ? current
            : [...current, enrolledFactorId],
        );
        const removal = await supabase.auth.mfa.unenroll({
          factorId: enrolledFactorId,
        });
        if (!removal.error) {
          setStaleFactorIds((current) =>
            current.filter((factorId) => factorId !== enrolledFactorId),
          );
        }
        throw new Error("invalid enrollment QR code");
      }
      setEnrollment({
        factorId: enrolledFactorId,
        qrCode,
        secret: result.data.totp.secret,
      });
      setFactorId(enrolledFactorId);
      setStage("verify");
    } catch {
      setError(GENERIC_ERROR);
    } finally {
      setIsEnrolling(false);
    }
  }

  async function verify(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!factorId || !/^\d{6}$/.test(code)) {
      setError("Enter the six-digit code from your authenticator app.");
      return;
    }
    try {
      const result = await supabase.auth.mfa.challengeAndVerify({
        factorId,
        code,
      });
      if (result.error || !result.data?.access_token) {
        throw new Error("verification failed");
      }
      const refreshed = await supabase.auth.refreshSession();
      if (refreshed.error || !refreshed.data.session) {
        throw new Error("session refresh failed");
      }
      const assurance =
        await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
      if (assurance.error || assurance.data?.currentLevel !== "aal2") {
        throw new Error("aal2 verification failed");
      }
      setCode("");
      setEnrollment(null);
      setStage("verified");
    } catch {
      setError(
        "The verification code was not accepted. Check the current code and try again.",
      );
    }
  }

  if (stage === "loading") {
    return <p role="status">Checking multi-factor authentication…</p>;
  }
  if (stage === "verified") {
    return (
      <section aria-labelledby="mfa-complete-title">
        <h2 id="mfa-complete-title">Multi-factor authentication verified</h2>
        <p role="status">
          This browser session now has AAL2. Application authorization is still
          checked separately.
        </p>
        <Link className="button button-primary" href={returnTo}>
          Continue to{" "}
          {returnTo === "/admin"
            ? "administration"
            : candidateFlow && returnTo.includes("#documents")
              ? "candidate documents"
              : "the candidate portal"}
        </Link>
      </section>
    );
  }
  if (stage === "enroll") {
    return (
      <section aria-labelledby="mfa-enroll-title">
        <h2 id="mfa-enroll-title">Enroll an authenticator app</h2>
        <p>
          Use a TOTP authenticator controlled by the local operator. No
          service-role credential is required.
        </p>
        <ErrorSummary errors={error ? [error] : []} />
        <Button type="button" onClick={beginEnrollment} disabled={isEnrolling}>
          {isEnrolling ? "Preparing enrollment…" : "Begin TOTP enrollment"}
        </Button>
      </section>
    );
  }
  if (stage === "error") {
    return (
      <section role="alert" className="error-summary">
        <h2>Multi-factor authentication is unavailable</h2>
        <p>{error ?? GENERIC_ERROR}</p>
        <p>
          Return to sign in and retry with the local Supabase Auth service
          running.
        </p>
      </section>
    );
  }
  return (
    <section aria-labelledby="mfa-verify-title">
      <h2 id="mfa-verify-title">
        {enrollment
          ? "Add Keeper Financial to your authenticator"
          : "Enter an authenticator code"}
      </h2>
      {enrollment ? (
        <div>
          <Image
            src={enrollment.qrCode.trimEnd()}
            alt="TOTP enrollment QR code"
            width={240}
            height={240}
            unoptimized
          />
          <p>
            If scanning is unavailable, enter this setup key manually:{" "}
            <code>{enrollment.secret}</code>
          </p>
          <p>
            Keep the setup key private. It is shown only for this enrollment.
          </p>
        </div>
      ) : null}
      <form onSubmit={verify}>
        <ErrorSummary errors={error ? [error] : []} />
        <FormField id="totp-code" label="Six-digit authenticator code">
          <input
            id="totp-code"
            name="code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            minLength={6}
            maxLength={6}
            required
            value={code}
            onChange={(event) =>
              setCode(event.target.value.replace(/\D/g, "").slice(0, 6))
            }
          />
        </FormField>
        <Button type="submit">Verify authenticator</Button>
      </form>
    </section>
  );
}
