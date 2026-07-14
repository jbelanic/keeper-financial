import Link from "next/link";
export default function NotFound() {
  return (
    <main id="main-content" className="container section">
      <h1>Page not found</h1>
      <p>
        The requested public resource is unavailable or is not approved for
        publication.
      </p>
      <Link className="button-link" href="/">
        Return home
      </Link>
    </main>
  );
}
