import { LoadingState } from "@keeper/ui";

export default function PublicLoading() {
  return (
    <section className="container section state-page">
      <LoadingState label="Loading public information" />
    </section>
  );
}
