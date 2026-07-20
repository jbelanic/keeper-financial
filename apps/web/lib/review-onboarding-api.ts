import type { components } from "@keeper/contracts";

// Phase 1D contract types (generated from the authoritative OpenAPI contract).
export type CandidateQueueResponse =
  components["schemas"]["CandidateQueueResponse"];
export type CandidateReviewSummary =
  components["schemas"]["CandidateReviewSummary"];
export type CandidateDetailResponse =
  components["schemas"]["CandidateDetailResponse"];
export type CandidateDecisionRequest =
  components["schemas"]["CandidateDecisionRequest"];
export type InterviewStatusUpdate =
  components["schemas"]["InterviewStatusUpdate"];
export type InformationRequestCreate =
  components["schemas"]["InformationRequestCreate"];
export type InformationRequestResponse =
  components["schemas"]["InformationRequestResponse"];
export type PlanSummary = components["schemas"]["PlanSummary"];
export type PlanWithTasks = components["schemas"]["PlanWithTasks"];
export type PlanCreateIn = components["schemas"]["PlanCreateIn"];
export type AdminOnboardingAssignmentSummary =
  components["schemas"]["AdminOnboardingAssignmentSummary"];
export type AdminOnboardingAssignmentDetail =
  components["schemas"]["AdminOnboardingAssignmentDetail"];
export type CandidateOnboardingDashboard =
  components["schemas"]["CandidateOnboardingDashboard"];
export type CandidateOnboardingAvailability =
  components["schemas"]["CandidateOnboardingAvailability"];
export type CandidateOnboardingTaskResponse =
  components["schemas"]["CandidateOnboardingTaskResponse"];
export type ActivationGateResponse =
  components["schemas"]["ActivationGateResponse"];
export type PolicyAcknowledgementResponse =
  components["schemas"]["PolicyAcknowledgementResponse"];
export type EsignEnvelopeResponse =
  components["schemas"]["EsignEnvelopeResponse"];
export type ControlledDocumentResponse =
  components["schemas"]["ControlledDocumentResponse"];
export type OnboardingAssignmentResponse =
  components["schemas"]["OnboardingAssignmentResponse"];
export type OnboardingTaskResponse =
  components["schemas"]["OnboardingTaskResponse"];

export const apiBaseUrl = () =>
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.API_INTERNAL_URL ??
  "http://localhost:8000";

// Server-side fetch helper is re-exported from the shared portal helper so we
// keep a single bearer/session transport.
export { portalServerJson } from "./portal-server-api";
