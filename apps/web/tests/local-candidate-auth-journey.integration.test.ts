import { createClient } from "@supabase/supabase-js";
import { createBrowserClient } from "@supabase/ssr";
import { createHmac } from "node:crypto";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const NodeWebSocket = createRequire(import.meta.url)("ws") as typeof WebSocket;

const enabled = process.env.KEEPER_RUN_LOCAL_AUTH_E2E === "1";

type MailpitSearch = {
  messages?: Array<{ ID?: string; Id?: string; id?: string }>;
};
type MailpitMessage = { HTML?: string; Text?: string };

const webOrigin =
  process.env.KEEPER_LOCAL_WEB_ORIGIN ?? "http://localhost:3000";
const apiOrigin =
  process.env.KEEPER_LOCAL_API_ORIGIN ?? "http://localhost:8000";
const supabaseUrl =
  process.env.KEEPER_LOCAL_SUPABASE_URL ?? "http://127.0.0.1:54321";
const mailpitOrigin =
  process.env.KEEPER_LOCAL_MAILPIT_ORIGIN ?? "http://127.0.0.1:54324";
const posting = process.env.KEEPER_LOCAL_E2E_POSTING ?? "";
const anonKey =
  process.env.KEEPER_LOCAL_SUPABASE_ANON_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
  "";
const onboardingEmail = process.env.KEEPER_LOCAL_ONBOARDING_E2E_EMAIL ?? "";
const onboardingPassword =
  process.env.KEEPER_LOCAL_ONBOARDING_E2E_PASSWORD ?? "";
const firefoxBidi = process.env.KEEPER_LOCAL_FIREFOX_BIDI ?? "";
const standardPdfPath = process.env.KEEPER_LOCAL_E2E_PDF_PATH ?? "";
const standardDocxPath = process.env.KEEPER_LOCAL_E2E_DOCX_PATH ?? "";

type BidiMessage = {
  id?: number;
  type?: string;
  result?: Record<string, unknown>;
  error?: string;
};

async function browserSignInSettles(
  email: string,
  password: string,
  expectedApplicationId: string,
): Promise<void> {
  if (!firefoxBidi) return;
  const socket = new NodeWebSocket(firefoxBidi);
  const pending = new Map<
    number,
    {
      resolve: (result: Record<string, unknown>) => void;
      reject: (message: string) => void;
    }
  >();
  let commandId = 0;
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(String(event.data)) as BidiMessage;
    if (!message.id || !pending.has(message.id)) return;
    const promise = pending.get(message.id);
    pending.delete(message.id);
    if (message.type === "error")
      promise?.reject(message.error ?? "browser command failed");
    else promise?.resolve(message.result ?? {});
  });
  await new Promise<void>((resolve, reject) => {
    socket.addEventListener("open", () => resolve(), { once: true });
    socket.addEventListener("error", () => reject(), { once: true });
  });
  const call = (method: string, params: Record<string, unknown>) =>
    new Promise<Record<string, unknown>>((resolve, reject) => {
      commandId += 1;
      pending.set(commandId, {
        resolve,
        reject: (message) => reject(new Error(message)),
      });
      socket.send(JSON.stringify({ id: commandId, method, params }));
    });
  try {
    await call("session.new", {
      capabilities: { alwaysMatch: { acceptInsecureCerts: true } },
    });
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const created = await call("browsingContext.create", { type: "tab" });
      const context = String(created.context ?? "");
      if (!context) throw new Error("browser context unavailable");
      await call("browsingContext.setViewport", {
        context,
        viewport: { width: 1280, height: 900 },
        devicePixelRatio: 1,
      });
      await call("browsingContext.navigate", {
        context,
        url: `${webOrigin}/auth/sign-in?posting=${encodeURIComponent(posting)}`,
        wait: "complete",
      });
      await call("script.evaluate", {
        expression: `(() => {
          const email = document.querySelector('#email');
          const password = document.querySelector('#password');
          const form = document.querySelector('form[action="/auth/sign-in/submit"]');
          if (!(email instanceof HTMLInputElement) || !(password instanceof HTMLInputElement) || !(form instanceof HTMLFormElement)) return false;
          email.value = ${JSON.stringify(email)};
          password.value = ${JSON.stringify(password)};
          form.requestSubmit();
          return true;
        })()`,
        target: { context },
        awaitPromise: true,
      });

      let settled = false;
      for (let check = 0; check < 100; check += 1) {
        const evaluated = await call("script.evaluate", {
          expression: `JSON.stringify({
            url: location.pathname,
            ready: document.readyState,
            loading: document.body?.textContent?.includes('Loading Keeper Financial') ?? false,
            requirements: document.body?.textContent?.includes('100 to 2,000 characters') ?? false,
            sectionPosition: getComputedStyle(document.querySelector('.progress-nav')).position
          })`,
          target: { context },
          awaitPromise: true,
        });
        const remote = evaluated.result as { value?: unknown } | undefined;
        const state = JSON.parse(String(remote?.value ?? "{}")) as {
          url?: string;
          ready?: string;
          loading?: boolean;
          requirements?: boolean;
          sectionPosition?: string;
        };
        if (
          state.url === `/candidate/applications/${expectedApplicationId}` &&
          state.ready === "complete" &&
          state.loading === false &&
          state.requirements === true &&
          state.sectionPosition !== "sticky" &&
          state.sectionPosition !== "fixed"
        ) {
          settled = true;
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
      if (settled && attempt === 2) {
        const started = await call("script.evaluate", {
          expression: `JSON.stringify((() => {
            const button = [...document.querySelectorAll('button')].find((node) => node.textContent?.trim() === 'Save draft');
            if (!(button instanceof HTMLButtonElement)) return {started: false};
            button.scrollIntoView({block: 'center'});
            button.focus();
            const scrollY = window.scrollY;
            button.click();
            return {started: true, scrollY};
          })())`,
          target: { context },
          awaitPromise: true,
        });
        const startedRemote = started.result as { value?: unknown } | undefined;
        const saveStart = JSON.parse(String(startedRemote?.value ?? "{}")) as {
          started?: boolean;
          scrollY?: number;
        };
        if (!saveStart.started || typeof saveStart.scrollY !== "number") {
          throw new Error("browser draft save could not start");
        }
        let saveSettled = false;
        let finalSaveState = "unavailable";
        for (let check = 0; check < 100; check += 1) {
          const evaluated = await call("script.evaluate", {
            expression: `JSON.stringify((() => {
              const feedback = document.querySelector('.save-feedback');
              const button = [...document.querySelectorAll('button')].find((node) => node.textContent?.trim() === 'Saved');
              return {
                feedback: feedback?.textContent?.trim(),
                polite: feedback?.getAttribute('aria-live'),
                scrollY: window.scrollY,
                focused: button === document.activeElement
              };
            })())`,
            target: { context },
            awaitPromise: true,
          });
          const remote = evaluated.result as { value?: unknown } | undefined;
          const state = JSON.parse(String(remote?.value ?? "{}")) as {
            feedback?: string;
            polite?: string;
            scrollY?: number;
            focused?: boolean;
          };
          finalSaveState = JSON.stringify({
            feedback: state.feedback ?? "absent",
            polite: state.polite ?? "absent",
            focused: state.focused ?? false,
            scrollDelta: Math.round(
              (state.scrollY ?? saveStart.scrollY) - saveStart.scrollY,
            ),
          });
          if (
            state.feedback === "Draft saved." &&
            state.polite === "polite" &&
            state.focused === true &&
            Math.abs((state.scrollY ?? 0) - saveStart.scrollY) <= 1
          ) {
            saveSettled = true;
            break;
          }
          await new Promise((resolve) => setTimeout(resolve, 50));
        }
        if (!saveSettled) {
          throw new Error(
            `browser draft-save feedback did not settle in place (${finalSaveState})`,
          );
        }
      }
      await call("browsingContext.close", { context });
      if (!settled) {
        throw new Error("fresh candidate browser sign-in did not settle");
      }
    }
  } finally {
    try {
      await call("session.end", {});
    } catch {
      // The browser process is disposable; a closed session needs no retry.
    }
    socket.close();
  }
}

async function browserUploadsStandardDocuments(
  email: string,
  password: string,
  applicationId: string,
  totpSecret: string,
): Promise<number> {
  if (!firefoxBidi || !standardPdfPath || !standardDocxPath) return 0;
  const socket = new NodeWebSocket(firefoxBidi);
  const pending = new Map<
    number,
    {
      resolve: (result: Record<string, unknown>) => void;
      reject: (message: string) => void;
    }
  >();
  let commandId = 0;
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(String(event.data)) as BidiMessage;
    if (!message.id || !pending.has(message.id)) return;
    const promise = pending.get(message.id);
    pending.delete(message.id);
    if (message.type === "error")
      promise?.reject(message.error ?? "browser command failed");
    else promise?.resolve(message.result ?? {});
  });
  await new Promise<void>((resolve, reject) => {
    socket.addEventListener("open", () => resolve(), { once: true });
    socket.addEventListener("error", () => reject(), { once: true });
  });
  const call = (method: string, params: Record<string, unknown>) =>
    new Promise<Record<string, unknown>>((resolve, reject) => {
      commandId += 1;
      pending.set(commandId, {
        resolve,
        reject: (message) => reject(new Error(message)),
      });
      socket.send(JSON.stringify({ id: commandId, method, params }));
    });
  let context = "";
  let stage = "session";
  try {
    await call("session.new", {
      capabilities: { alwaysMatch: { acceptInsecureCerts: true } },
    });
    const created = await call("browsingContext.create", { type: "tab" });
    context = String(created.context ?? "");
    if (!context) throw new Error("browser context unavailable");
    await call("browsingContext.setViewport", {
      context,
      viewport: { width: 1280, height: 900 },
      devicePixelRatio: 1,
    });
    stage = "sign-in";
    await call("browsingContext.navigate", {
      context,
      url: `${webOrigin}/auth/sign-in?posting=${encodeURIComponent(posting)}`,
      wait: "complete",
    });
    await call("script.evaluate", {
      expression: `(() => {
        const email = document.querySelector('#email');
        const password = document.querySelector('#password');
        const form = document.querySelector('form[action="/auth/sign-in/submit"]');
        if (!(email instanceof HTMLInputElement) || !(password instanceof HTMLInputElement) || !(form instanceof HTMLFormElement)) return false;
        email.value = ${JSON.stringify(email)};
        password.value = ${JSON.stringify(password)};
        form.requestSubmit();
        return true;
      })()`,
      target: { context },
      awaitPromise: true,
    });
    stage = "sign-in-settle";
    let signedIn = false;
    for (let check = 0; check < 100; check += 1) {
      const evaluated = await call("script.evaluate", {
        expression: `location.pathname === ${JSON.stringify(`/candidate/applications/${applicationId}`)}`,
        target: { context },
        awaitPromise: true,
      });
      const remote = evaluated.result as { value?: unknown } | undefined;
      if (remote?.value === true) {
        signedIn = true;
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    if (!signedIn) throw new Error("browser document sign-in did not settle");

    const returnTo = `/candidate/applications/${applicationId}#documents`;
    stage = "mfa-navigation";
    await call("browsingContext.navigate", {
      context,
      url: `${webOrigin}/auth/mfa?returnTo=${encodeURIComponent(returnTo)}`,
      wait: "complete",
    });
    stage = "mfa-challenge";
    let challengeReady = false;
    for (let check = 0; check < 100; check += 1) {
      const evaluated = await call("script.evaluate", {
        expression: `document.querySelector('#totp-code') instanceof HTMLInputElement`,
        target: { context },
        awaitPromise: true,
      });
      const remote = evaluated.result as { value?: unknown } | undefined;
      if (remote?.value === true) {
        challengeReady = true;
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    if (!challengeReady) throw new Error("browser MFA challenge did not load");
    stage = "mfa-verification";
    const code = totpCode(totpSecret);
    await call("script.evaluate", {
      expression: `(() => {
        const input = document.querySelector('#totp-code');
        if (!(input instanceof HTMLInputElement)) return false;
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
        setter?.call(input, ${JSON.stringify(code)});
        input.dispatchEvent(new Event('input', {bubbles: true}));
        input.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
      })()`,
      target: { context },
      awaitPromise: true,
    });
    await call("script.evaluate", {
      expression: `(() => {
        const form = document.querySelector('#totp-code')?.closest('form');
        if (!(form instanceof HTMLFormElement)) return false;
        form.requestSubmit();
        return true;
      })()`,
      target: { context },
      awaitPromise: true,
    });
    stage = "mfa-settle";
    let verified = false;
    for (let check = 0; check < 100; check += 1) {
      const evaluated = await call("script.evaluate", {
        expression: `document.body?.textContent?.includes('Multi-factor authentication verified') ?? false`,
        target: { context },
        awaitPromise: true,
      });
      const remote = evaluated.result as { value?: unknown } | undefined;
      if (remote?.value === true) {
        verified = true;
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    if (!verified) throw new Error("browser MFA verification did not settle");

    stage = "document-navigation";
    await call("browsingContext.navigate", {
      context,
      url: `${webOrigin}${returnTo}`,
      wait: "complete",
    });
    for (const path of [standardPdfPath, standardDocxPath]) {
      stage = "document-input";
      let sharedId = "";
      for (let check = 0; check < 100; check += 1) {
        const evaluated = await call("script.evaluate", {
          expression: `document.querySelector('#candidate-document-file')`,
          target: { context },
          awaitPromise: true,
          resultOwnership: "root",
        });
        const remote = evaluated.result as { sharedId?: unknown } | undefined;
        sharedId = typeof remote?.sharedId === "string" ? remote.sharedId : "";
        if (sharedId) break;
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
      if (!sharedId) throw new Error("browser document input did not load");
      stage = "document-selection";
      await call("input.setFiles", {
        context,
        element: { sharedId },
        files: [path],
      });
      stage = "document-upload-start";
      let uploadStarted = false;
      for (let check = 0; check < 100; check += 1) {
        const evaluated = await call("script.evaluate", {
          expression: `(() => {
            const button = [...document.querySelectorAll('button')].find((node) => node.textContent?.trim() === 'Upload document');
            if (!(button instanceof HTMLButtonElement) || button.disabled) return false;
            button.click();
            return true;
          })()`,
          target: { context },
          awaitPromise: true,
        });
        const remote = evaluated.result as { value?: unknown } | undefined;
        if (remote?.value === true) {
          uploadStarted = true;
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
      if (!uploadStarted)
        throw new Error("browser document upload could not start");
      stage = "document-upload-settle";
      let uploaded = false;
      for (let check = 0; check < 200; check += 1) {
        const evaluated = await call("script.evaluate", {
          expression: `document.querySelector('#documents [aria-live="polite"]')?.textContent?.includes('Document uploaded, scanned, and listed successfully.') ?? false`,
          target: { context },
          awaitPromise: true,
        });
        const remote = evaluated.result as { value?: unknown } | undefined;
        if (remote?.value === true) {
          uploaded = true;
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
      if (!uploaded) throw new Error("browser document upload did not settle");
    }
    return 2;
  } catch {
    throw new Error(`browser standard document journey failed at ${stage}`);
  } finally {
    if (context) {
      try {
        await call("browsingContext.close", { context });
      } catch {
        // A failed disposable context needs no retry.
      }
    }
    try {
      await call("session.end", {});
    } catch {
      // The browser process is disposable; a closed session needs no retry.
    }
    socket.close();
  }
}

async function safeFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch {
    throw new Error("local candidate-auth integration service is unavailable");
  }
}

async function confirmationUrl(email: string): Promise<string> {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const search = await safeFetch(
      `${mailpitOrigin}/api/v1/search?query=${encodeURIComponent(`to:${email}`)}`,
      { cache: "no-store" },
    );
    if (search.ok) {
      const result = (await search.json()) as MailpitSearch;
      const message = result.messages?.[0];
      const id = message?.ID ?? message?.Id ?? message?.id;
      if (id) {
        const detail = await safeFetch(
          `${mailpitOrigin}/api/v1/message/${id}`,
          {
            cache: "no-store",
          },
        );
        if (detail.ok) {
          const body = (await detail.json()) as MailpitMessage;
          const content = `${body.HTML ?? ""}\n${body.Text ?? ""}`.replaceAll(
            "&amp;",
            "&",
          );
          const match = content.match(
            /https?:\/\/[^"'<>\s]+\/auth\/v1\/verify[^"'<>\s]+/,
          );
          if (match) return match[0];
        }
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("local confirmation message was not captured");
}

function cookieHeader(response: Response): string {
  const headers = response.headers as Headers & {
    getSetCookie?: () => string[];
  };
  const values = headers.getSetCookie?.() ?? [
    response.headers.get("set-cookie") ?? "",
  ];
  return values
    .filter(Boolean)
    .map((value) => value.split(";", 1)[0])
    .join("; ");
}

async function registerAndConfirm(
  email: string,
  password: string,
  callback: string,
): Promise<Response> {
  const supabase = createBrowserClient(supabaseUrl, anonKey);
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: callback },
  });
  if (error) throw new Error("local synthetic registration failed");
  const pkceCookies = document.cookie;
  if (!pkceCookies)
    throw new Error("local synthetic registration did not persist PKCE state");
  const verify = await safeFetch(await confirmationUrl(email), {
    redirect: "manual",
  });
  const callbackLocation = verify.headers.get("location");
  if (!callbackLocation)
    throw new Error("local confirmation did not return a callback");
  return safeFetch(callbackLocation, {
    redirect: "manual",
    headers: { cookie: pkceCookies },
  });
}

async function postingSignIn(
  email: string,
  password: string,
): Promise<Response> {
  return safeFetch(`${webOrigin}/auth/sign-in/submit`, {
    method: "POST",
    redirect: "manual",
    headers: {
      origin: webOrigin,
      "content-type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      email,
      password,
      posting,
      returnTo: "/candidate",
    }),
  });
}

async function genericSignIn(
  email: string,
  password: string,
): Promise<Response> {
  return safeFetch(`${webOrigin}/auth/sign-in/submit`, {
    method: "POST",
    redirect: "manual",
    headers: {
      origin: webOrigin,
      "content-type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({ email, password, returnTo: "/candidate" }),
  });
}

async function passwordAccessToken(
  email: string,
  password: string,
): Promise<string> {
  const supabase = createClient(supabaseUrl, anonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
      storageKey: "keeper-local-e2e-direct-token",
    },
  });
  const result = await supabase.auth.signInWithPassword({ email, password });
  const accessToken = result.data.session?.access_token;
  if (result.error || !accessToken)
    throw new Error("local synthetic sign-in failed");
  return accessToken;
}

function applicationId(location: string): string {
  const match = location.match(/\/candidate\/applications\/([^/?#]+)/);
  if (!match?.[1]) throw new Error("candidate application location is invalid");
  return match[1];
}

function boundedRedirectResult(location: string): string {
  try {
    const url = new URL(location, webOrigin);
    const error = url.searchParams.get("error") ?? "none";
    const hasPosting = url.searchParams.get("posting") === posting;
    return `error=${error}; posting=${hasPosting ? "preserved" : "absent"}`;
  } catch {
    return "error=malformed-redirect; posting=absent";
  }
}

function totpCode(secret: string): string {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const normalized = secret.toUpperCase().replace(/[^A-Z2-7]/g, "");
  let bits = "";
  for (const character of normalized) {
    const value = alphabet.indexOf(character);
    if (value < 0) throw new Error("local synthetic TOTP setup was invalid");
    bits += value.toString(2).padStart(5, "0");
  }
  const key = Buffer.from(
    Array.from({ length: Math.floor(bits.length / 8) }, (_, index) =>
      Number.parseInt(bits.slice(index * 8, index * 8 + 8), 2),
    ),
  );
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30_000)));
  const digest = createHmac("sha1", key).update(counter).digest();
  const offset = digest[digest.length - 1] & 0x0f;
  const value =
    (((digest[offset] & 0x7f) << 24) |
      ((digest[offset + 1] & 0xff) << 16) |
      ((digest[offset + 2] & 0xff) << 8) |
      (digest[offset + 3] & 0xff)) %
    1_000_000;
  return value.toString().padStart(6, "0");
}

function syntheticPdf(): Uint8Array {
  const objects = [
    "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
    "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
    "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1 1] /Resources << >> /Contents 4 0 R >>\nendobj\n",
    "4 0 obj\n<< /Length 0 >>\nstream\n\nendstream\nendobj\n",
  ];
  let body = "%PDF-1.4\n";
  const offsets: number[] = [];
  for (const object of objects) {
    offsets.push(body.length);
    body += object;
  }
  const xrefOffset = body.length;
  body += "xref\n0 5\n0000000000 65535 f \n";
  body += offsets
    .map((offset) => `${offset.toString().padStart(10, "0")} 00000 n \n`)
    .join("");
  body += `trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;
  return new TextEncoder().encode(body);
}

function candidateDocumentUpload(
  content: Uint8Array,
  extension: "pdf" | "docx",
  mime: string,
): { body: Buffer; contentType: string } {
  const boundary = "keeper-synthetic-document-boundary";
  const prefix =
    `--${boundary}\r\n` +
    'Content-Disposition: form-data; name="category"\r\n\r\n' +
    `resume\r\n--${boundary}\r\n` +
    `Content-Disposition: form-data; name="file"; filename="synthetic-standard.${extension}"\r\n` +
    `Content-Type: ${mime}\r\n\r\n`;
  const suffix = `\r\n--${boundary}--\r\n`;
  return {
    body: Buffer.concat([
      Buffer.from(prefix),
      Buffer.from(content),
      Buffer.from(suffix),
    ]),
    contentType: `multipart/form-data; boundary=${boundary}`,
  };
}

function syntheticDocumentUpload(): { body: Buffer; contentType: string } {
  return candidateDocumentUpload(syntheticPdf(), "pdf", "application/pdf");
}

describe.skipIf(!enabled)(
  "genuine local candidate authentication journey",
  () => {
    beforeAll(() => {
      if (!anonKey || !posting) {
        throw new Error(
          "local auth E2E requires an anon key and published synthetic posting",
        );
      }
    });

    it("confirms registration through Mailpit, persists callback cookies, and enters the application", async () => {
      const suffix = `${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
      const email = `keeper-registration-${suffix}@example.test`;
      const password = `Synthetic-${crypto.randomUUID()}-Pass`;
      const callback = `${webOrigin}/auth/callback?posting=${encodeURIComponent(posting)}`;
      const response = await registerAndConfirm(email, password, callback);
      const location = response.headers.get("location") ?? "";
      if (!location.includes("/candidate/applications/")) {
        throw new Error(
          `posting-bound callback did not enter the candidate application (${boundedRedirectResult(location)})`,
        );
      }
      const cookies = cookieHeader(response);
      if (!cookies)
        throw new Error("callback did not persist a server session cookie");
      const subsequent = await safeFetch(location, {
        headers: { cookie: cookies },
        redirect: "manual",
      });
      if (subsequent.status !== 200) {
        throw new Error(
          "persisted callback session failed on a subsequent request",
        );
      }
      const applicationPage = await subsequent.text();
      if (!applicationPage.includes("100 to 2,000 characters")) {
        throw new Error("candidate application requirements were not visible");
      }
      if (applicationPage.includes('href="/candidate/onboarding"')) {
        throw new Error("unassigned candidate was shown onboarding navigation");
      }
      const retry = await postingSignIn(email, password);
      const retryLocation = retry.headers.get("location") ?? "";
      if (!retryLocation.includes("/candidate/applications/")) {
        throw new Error(
          `existing-user retry did not reuse the application start boundary (${boundedRedirectResult(retryLocation)})`,
        );
      }
      if (applicationId(retryLocation) !== applicationId(location)) {
        throw new Error(
          "existing-user retry created a different nonterminal attempt",
        );
      }

      try {
        await browserSignInSettles(email, password, applicationId(location));
      } catch {
        throw new Error("browser sign-in stabilization failed");
      }

      const accessToken = await passwordAccessToken(email, password);
      const authorization = { Authorization: `Bearer ${accessToken}` };
      const availability = await safeFetch(
        `${apiOrigin}/api/v1/candidate/onboarding/availability`,
        { headers: authorization, cache: "no-store" },
      );
      if (
        availability.status !== 200 ||
        ((await availability.json()) as { available?: boolean }).available !==
          false
      ) {
        throw new Error("unassigned candidate availability was not stable");
      }
      const dashboard = await safeFetch(
        `${apiOrigin}/api/v1/candidate/onboarding`,
        { headers: authorization, cache: "no-store" },
      );
      const dashboardBody = (await dashboard.json()) as {
        assignment?: unknown;
        activation_ready?: boolean;
      };
      if (
        dashboard.status !== 200 ||
        dashboardBody.assignment !== null ||
        dashboardBody.activation_ready !== false
      ) {
        throw new Error("unassigned candidate dashboard was not stable");
      }

      const id = applicationId(location);
      const current = await safeFetch(
        `${apiOrigin}/api/v1/candidate/applications/${id}`,
        { headers: authorization, cache: "no-store" },
      );
      const currentBody = (await current.json()) as { revision?: number };
      if (!current.ok || typeof currentBody.revision !== "number") {
        throw new Error(
          "candidate application could not be read for draft validation",
        );
      }
      const saved = await safeFetch(
        `${apiOrigin}/api/v1/candidate/applications/${id}`,
        {
          method: "PATCH",
          headers: { ...authorization, "content-type": "application/json" },
          body: JSON.stringify({
            expected_revision: currentBody.revision,
            given_name: "Synthetic",
            family_name: "Candidate",
            preferred_name: null,
            phone: "+14165550100",
            city: "London",
            region: "Ontario",
            country_code: "CA",
            preferred_contact_method: "email",
            available_from: null,
            referral_source: null,
            referral_detail: null,
            interest_statement:
              "This synthetic statement contains enough bounded text to satisfy the approved candidate application minimum safely.",
            relevant_experience: null,
            employment: [],
            education: [],
            privacy_acknowledged: true,
            information_accuracy_confirmed: true,
          }),
        },
      );
      const savedBody = (await saved.json()) as { revision?: number };
      if (!saved.ok || typeof savedBody.revision !== "number") {
        throw new Error("valid synthetic candidate draft did not save");
      }
      const submitted = await safeFetch(
        `${apiOrigin}/api/v1/candidate/applications/${id}/submit`,
        {
          method: "POST",
          headers: { ...authorization, "content-type": "application/json" },
          body: JSON.stringify({ expected_revision: savedBody.revision }),
        },
      );
      if (!submitted.ok) {
        throw new Error("valid synthetic candidate application did not submit");
      }

      const mfaClient = createClient(supabaseUrl, anonKey, {
        auth: { persistSession: false, autoRefreshToken: false },
      });
      const signedIn = await mfaClient.auth.signInWithPassword({
        email,
        password,
      });
      if (signedIn.error) throw new Error("candidate MFA sign-in failed");
      let factorId: string | null = null;
      try {
        const enrolled = await mfaClient.auth.mfa.enroll({
          factorType: "totp",
          friendlyName: "Keeper Financial candidate documents E2E",
          issuer: "Keeper Financial",
        });
        factorId = enrolled.data?.id ?? null;
        const secret = enrolled.data?.totp.secret;
        if (enrolled.error || !factorId || !secret) {
          throw new Error("candidate MFA enrollment failed");
        }
        const verified = await mfaClient.auth.mfa.challengeAndVerify({
          factorId,
          code: totpCode(secret),
        });
        if (verified.error || !verified.data?.access_token) {
          throw new Error("candidate MFA verification failed");
        }
        const assurance =
          await mfaClient.auth.mfa.getAuthenticatorAssuranceLevel();
        if (assurance.data?.currentLevel !== "aal2") {
          throw new Error("candidate MFA session did not reach AAL2");
        }
        let browserUploadCount = 0;
        try {
          browserUploadCount = await browserUploadsStandardDocuments(
            email,
            password,
            id,
            secret,
          );
        } catch (error) {
          if (
            error instanceof Error &&
            error.message.startsWith(
              "browser standard document journey failed at ",
            )
          ) {
            throw error;
          }
          throw new Error("browser document upload journey failed");
        }
        const documents = await safeFetch(
          `${apiOrigin}/api/v1/candidate/applications/${id}/documents`,
          {
            headers: { Authorization: `Bearer ${verified.data.access_token}` },
            cache: "no-store",
          },
        );
        if (!documents.ok) {
          throw new Error("candidate AAL2 document metadata access failed");
        }
        const uploadCases = [syntheticDocumentUpload()];
        if (standardPdfPath) {
          uploadCases.push(
            candidateDocumentUpload(
              readFileSync(standardPdfPath),
              "pdf",
              "application/pdf",
            ),
          );
        }
        if (standardDocxPath) {
          uploadCases.push(
            candidateDocumentUpload(
              readFileSync(standardDocxPath),
              "docx",
              "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
          );
        }
        const uploadedIds: string[] = [];
        for (const upload of uploadCases) {
          const uploaded = await safeFetch(
            `${apiOrigin}/api/v1/candidate/applications/${id}/documents`,
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${verified.data.access_token}`,
                "content-type": upload.contentType,
              },
              body: upload.body,
            },
          );
          const uploadedBody = (await uploaded.json()) as {
            id?: string;
            scan_status?: string;
            quarantined?: boolean;
            detail?: string;
          };
          if (
            uploaded.status !== 201 ||
            !uploadedBody.id ||
            uploadedBody.scan_status !== "clean" ||
            uploadedBody.quarantined !== false
          ) {
            throw new Error(
              `clean synthetic candidate document upload failed (${uploaded.status}; ${uploadedBody.detail ?? "unexpected response"})`,
            );
          }
          uploadedIds.push(uploadedBody.id);
        }
        const invalidCases: Array<{
          upload: { body: Buffer; contentType: string };
          detail: string;
        }> = [
          {
            upload: candidateDocumentUpload(
              new TextEncoder().encode("%PDF-1.7\n%%EOF\n"),
              "pdf",
              "application/pdf",
            ),
            detail: "pdf_structure_invalid",
          },
        ];
        if (standardDocxPath) {
          const standardDocx = readFileSync(standardDocxPath);
          invalidCases.push({
            upload: candidateDocumentUpload(
              standardDocx.subarray(0, standardDocx.length - 20),
              "docx",
              "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            detail: "docx_structure_invalid",
          });
        }
        for (const invalid of invalidCases) {
          const rejected = await safeFetch(
            `${apiOrigin}/api/v1/candidate/applications/${id}/documents`,
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${verified.data.access_token}`,
                "content-type": invalid.upload.contentType,
              },
              body: invalid.upload.body,
            },
          );
          const rejectedBody = (await rejected.json()) as { detail?: string };
          if (
            rejected.status !== 422 ||
            rejectedBody.detail !== invalid.detail
          ) {
            throw new Error("invalid candidate document did not fail safely");
          }
        }
        const refreshedDocuments = await safeFetch(
          `${apiOrigin}/api/v1/candidate/applications/${id}/documents`,
          {
            headers: { Authorization: `Bearer ${verified.data.access_token}` },
            cache: "no-store",
          },
        );
        const refreshedBody = (await refreshedDocuments.json()) as {
          items?: Array<{ id?: string }>;
        };
        if (
          !refreshedDocuments.ok ||
          refreshedBody.items?.length !==
            uploadedIds.length + browserUploadCount ||
          !uploadedIds.every((uploadedId) =>
            refreshedBody.items?.some((item) => item.id === uploadedId),
          )
        ) {
          throw new Error(
            "uploaded candidate document metadata did not refresh",
          );
        }
        const publicDownload = await safeFetch(
          `${apiOrigin}/api/v1/documents/${uploadedIds[0]}/download`,
          { cache: "no-store" },
        );
        if (publicDownload.status !== 401) {
          throw new Error(
            "candidate document exposed an unauthorized download",
          );
        }
        const adminDenied = await safeFetch(
          `${apiOrigin}/api/v1/auth/access?area=admin`,
          {
            headers: { Authorization: `Bearer ${verified.data.access_token}` },
            cache: "no-store",
          },
        );
        if (adminDenied.status !== 403) {
          throw new Error("candidate identity received administrator access");
        }
      } finally {
        if (factorId) {
          const cleanup = await mfaClient.auth.mfa.unenroll({ factorId });
          if (cleanup.error) {
            throw new Error("candidate MFA factor cleanup failed");
          }
        }
        await mfaClient.auth.signOut();
      }
    }, 60_000);

    it("recovers a confirmed unmapped identity only through posting-bound sign-in", async () => {
      const suffix = `${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
      const email = `keeper-unmapped-${suffix}@example.test`;
      const password = `Synthetic-${crypto.randomUUID()}-Pass`;
      const confirmation = await registerAndConfirm(
        email,
        password,
        `${webOrigin}/auth/callback`,
      );
      if (
        !confirmation.headers.get("location")?.includes("error=verification")
      ) {
        throw new Error("unmapped confirmation did not remain fail closed");
      }
      const generic = await genericSignIn(email, password);
      if (!generic.headers.get("location")?.endsWith("/candidate")) {
        throw new Error(
          "generic sign-in did not retain its bounded portal return",
        );
      }
      const accessToken = await passwordAccessToken(email, password);
      const denied = await safeFetch(
        `${apiOrigin}/api/v1/auth/access?area=candidate`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          cache: "no-store",
        },
      );
      if (denied.status !== 403) {
        throw new Error("generic sign-in provisioned an unmapped identity");
      }
      const recovered = await postingSignIn(email, password);
      if (
        !recovered.headers.get("location")?.includes("/candidate/applications/")
      ) {
        throw new Error(
          `posting-bound existing-user recovery did not provision the application (${boundedRedirectResult(recovered.headers.get("location") ?? "")})`,
        );
      }
      const allowed = await safeFetch(
        `${apiOrigin}/api/v1/auth/access?area=candidate`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          cache: "no-store",
        },
      );
      if (allowed.status !== 200) {
        throw new Error(
          "candidate access did not resolve after posting-bound provisioning",
        );
      }
    }, 30_000);

    it.skipIf(!onboardingEmail || !onboardingPassword)(
      "enters onboarding across a fresh request for a supported assigned candidate fixture",
      async () => {
        const signIn = await postingSignIn(onboardingEmail, onboardingPassword);
        const cookies = cookieHeader(signIn);
        if (!cookies)
          throw new Error(
            "assigned candidate sign-in did not persist a session",
          );
        const onboarding = await safeFetch(
          `${webOrigin}/candidate/onboarding`,
          {
            headers: { cookie: cookies },
            redirect: "manual",
          },
        );
        if (onboarding.status !== 200) {
          throw new Error(
            "assigned candidate could not enter onboarding on a fresh request",
          );
        }
        const body = await onboarding.text();
        if (!body.includes("Your onboarding")) {
          throw new Error("assigned candidate onboarding page did not render");
        }
      },
      30_000,
    );
  },
);
