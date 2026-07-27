import Link from "next/link";
export default function NotFound() {
  return (
    <main
      id="main-content"
      className="container section state-page"
      aria-labelledby="not-found-title"
    >
      <h1 id="not-found-title">Page not found</h1>
      <p>
        We could not find that page. Check the address or return to the home
        page.
      </p>
      <Link className="button-link" href="/">
        Return home
      </Link>
    </main>
  );
}
