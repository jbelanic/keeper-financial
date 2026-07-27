import type { components } from "@keeper/contracts";
import type { EligibleAgent } from "./agent-api";
import { portalServerJson } from "./portal-server-api";

export type BorrowerReviewQueueItem =
  components["schemas"]["BorrowerReviewQueueItem"];
export type BorrowerReviewQueueResponse =
  components["schemas"]["BorrowerReviewQueueResponse"];

export type BorrowerInternalProjection =
  components["schemas"]["BorrowerInternalProjection"];

export type BorrowerAgentProjection =
  components["schemas"]["BorrowerAgentProjection"];

export type BorrowerAgentInfo = components["schemas"]["BorrowerAgentInfo"];

export type BorrowerDocumentMetadata =
  components["schemas"]["BorrowerDocumentMetadata"];
export type BorrowerDocumentListResponse =
  components["schemas"]["BorrowerDocumentListResponse"];

export async function getBorrowerReviewBootstrap() {
  return Promise.all([
    portalServerJson<BorrowerReviewQueueResponse>(
      "/api/v1/borrower-applications/review-queue",
    ),
    portalServerJson<EligibleAgent[]>("/api/v1/admin/eligible-agents"),
  ]);
}

export async function getAgentAssignedBootstrap() {
  return portalServerJson<BorrowerReviewQueueResponse>(
    "/api/v1/borrower-applications/agent/assigned",
  );
}
