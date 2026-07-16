from fastapi.testclient import TestClient


def test_phase_1b_openapi_operations_preserve_public_and_admin_boundaries(
    client: TestClient,
) -> None:
    document = client.get("/openapi.json").json()
    paths = document["paths"]
    leads = paths["/api/v1/leads"]
    withdrawal = paths["/api/v1/leads/{lead_id}/marketing-consent/withdrawal"]["post"]
    redirect = paths["/api/v1/integrations/mortgage-application"]["get"]

    assert "security" not in leads["post"]
    create_schema = document["components"]["schemas"]["LeadInquiryCreate"]
    assert create_schema["additionalProperties"] is False
    assert not {
        "service_wording_version",
        "marketing_wording_version",
        "privacy_notice_version",
    }.intersection(create_schema["properties"])
    assert leads["post"]["responses"]["201"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/LeadInquiryCreated")
    assert "429" in leads["post"]["responses"]

    assert leads["get"]["security"] == [{"HTTPBearer": []}]
    assert leads["get"]["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/LeadListResponse")
    assert withdrawal["security"] == [{"HTTPBearer": []}]
    assert withdrawal["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ConsentState"
    )
    assert "404" in withdrawal["responses"]

    assert "security" not in redirect
    assert set(redirect["responses"]) >= {"307", "422", "503"}


def test_phase_1c_openapi_operations_and_candidate_contracts_are_allowlisted(
    client: TestClient,
) -> None:
    document = client.get("/openapi.json").json()
    paths = document["paths"]
    assert "security" not in paths["/api/v1/recruitment/postings"]["get"]
    assert "security" not in paths["/api/v1/recruitment/postings/{slug}"]["get"]
    assert paths["/api/v1/admin/recruitment-postings"]["post"]["security"] == [{"HTTPBearer": []}]
    assert paths["/api/v1/recruitment/postings/{slug}/applications/start"]["post"]["security"] == [
        {"HTTPBearer": []}
    ]
    for route, method in [
        ("/api/v1/candidate/privacy-disclosure", "get"),
        ("/api/v1/candidate/applications", "get"),
        ("/api/v1/candidate/applications/status", "get"),
        ("/api/v1/candidate/applications/{application_id}", "get"),
        ("/api/v1/candidate/applications/{application_id}", "patch"),
        ("/api/v1/candidate/applications/{application_id}/submit", "post"),
        ("/api/v1/candidate/applications/{application_id}/withdraw", "post"),
        ("/api/v1/candidate/applications/{application_id}/documents", "post"),
        ("/api/v1/candidate/applications/{application_id}/documents", "get"),
        (
            "/api/v1/candidate/applications/{application_id}/documents/{document_id}",
            "delete",
        ),
        ("/api/v1/documents/{document_id}/download", "get"),
    ]:
        assert paths[route][method]["security"] == [{"HTTPBearer": []}]
        assert {"401", "403"}.issubset(paths[route][method]["responses"])
    for method in ["get", "post"]:
        assert {"401", "403"}.issubset(
            paths["/api/v1/admin/recruitment-postings"][method]["responses"]
        )
    assert {"401", "403", "404", "409"}.issubset(
        paths["/api/v1/admin/recruitment-postings/{posting_id}"]["patch"]["responses"]
    )
    assert "/api/v1/candidates/{candidate_id}/status" not in paths

    candidate_schema = document["components"]["schemas"]["CandidateApplicationResponse"]
    status_schema = document["components"]["schemas"]["CandidateStatusListResponse"]
    serialized = str(candidate_schema) + str(status_schema)
    for forbidden in ["reason", "internal_notes", "actor_user_id", "audit", "decision"]:
        assert forbidden not in serialized
    draft_schema = document["components"]["schemas"]["ApplicationDraftUpdate"]
    assert draft_schema["additionalProperties"] is False
    assert not {
        "email",
        "recruitment_posting_id",
        "privacy_disclosure_version",
        "state",
        "status",
        "revision",
    }.intersection(draft_schema["properties"])


def test_phase_1d_openapi_operations_enforce_boundaries_and_contracts(
    client: TestClient,
) -> None:
    document = client.get("/openapi.json").json()
    paths = document["paths"]

    # REV-001/004/006: admin candidate review pipeline is admin-only.
    queue = paths["/api/v1/admin/candidates"]["get"]
    assert queue["security"] == [{"HTTPBearer": []}]
    assert {"401", "403", "200"}.issubset(queue["responses"])

    detail = paths["/api/v1/admin/candidates/{candidate_id}"]["get"]
    assert detail["security"] == [{"HTTPBearer": []}]
    assert {"401", "403", "404"}.issubset(detail["responses"])

    decision = paths["/api/v1/admin/candidates/{candidate_id}/decision"]["post"]
    assert decision["security"] == [{"HTTPBearer": []}]
    assert {"401", "403", "409"}.issubset(decision["responses"])

    # ONB-001/002: plan + assignment are admin-only.
    plans_post = paths["/api/v1/admin/onboarding/plans"]["post"]
    assert plans_post["security"] == [{"HTTPBearer": []}]
    assert "201" in plans_post["responses"]

    assign = paths["/api/v1/admin/candidates/{candidate_id}/assign-onboarding"]["post"]
    assert assign["security"] == [{"HTTPBearer": []}]
    assert {"401", "403", "409"}.issubset(assign["responses"])

    # ONB-005/006/008/009: candidate-facing onboarding is candidate-only.
    dash = paths["/api/v1/candidate/onboarding"]["get"]
    assert dash["security"] == [{"HTTPBearer": []}]
    assert {"401", "403"}.issubset(dash["responses"])

    ack = paths["/api/v1/candidate/onboarding/acknowledgements"]["post"]
    assert ack["security"] == [{"HTTPBearer": []}]
    assert {"401", "403"}.issubset(ack["responses"])

    # B7: no internal audit fields leak into candidate-facing contract types.
    dash_schema = document["components"]["schemas"]["CandidateOnboardingDashboard"]
    serialized = str(dash_schema)
    for forbidden in ["actor_user_id", "prior_status", "audit", "internal_notes", "reason"]:
        assert forbidden not in serialized

    # B7: request bodies forbid unknown properties (no silent data capture).
    plan_in = document["components"]["schemas"]["PlanCreateIn"]
    assert plan_in["additionalProperties"] is False
    decision_in = document["components"]["schemas"]["CandidateDecisionRequest"]
    assert decision_in["additionalProperties"] is False


def test_phase_1e_agent_operations_and_public_contracts_are_allowlisted(
    client: TestClient,
) -> None:
    document = client.get("/openapi.json").json()
    paths = document["paths"]

    expected = {
        ("/api/v1/agents", "get"): {"200", "422"},
        ("/api/v1/agents/{slug}", "get"): {"200", "404", "422"},
        ("/api/v1/admin/agent-profiles", "get"): {"200", "401", "403", "422"},
        ("/api/v1/admin/agent-profiles", "post"): {
            "201",
            "401",
            "403",
            "404",
            "409",
            "422",
        },
        ("/api/v1/admin/agent-profiles/{profile_id}", "get"): {
            "200",
            "401",
            "403",
            "404",
            "422",
        },
        ("/api/v1/admin/agent-profiles/{profile_id}", "patch"): {
            "200",
            "401",
            "403",
            "404",
            "409",
            "422",
        },
        ("/api/v1/agents/{profile_id}/status", "post"): {
            "200",
            "401",
            "403",
            "404",
            "409",
            "422",
        },
    }
    for (path, method), responses in expected.items():
        assert set(paths[path][method]["responses"]) == responses

    assert "security" not in paths["/api/v1/agents"]["get"]
    assert "security" not in paths["/api/v1/agents/{slug}"]["get"]
    for path, method in [
        ("/api/v1/admin/agent-profiles", "get"),
        ("/api/v1/admin/agent-profiles", "post"),
        ("/api/v1/admin/agent-profiles/{profile_id}", "get"),
        ("/api/v1/admin/agent-profiles/{profile_id}", "patch"),
        ("/api/v1/agents/{profile_id}/status", "post"),
    ]:
        assert paths[path][method]["security"] == [{"HTTPBearer": []}]

    schemas = document["components"]["schemas"]
    for name in ["AgentProfileCreate", "AgentProfileUpdate", "AgentTransitionRequest"]:
        assert schemas[name]["additionalProperties"] is False

    public_contract = str(schemas["PublicAgentProfile"]) + str(schemas["PublicAgentProfileSummary"])
    for forbidden in [
        "user_id",
        "status",
        "version",
        "approved_by_user_id",
        "approved_at",
        "published_at",
        "created_at",
        "updated_at",
        "internal_notes",
        "actor_user_id",
        "audit",
        "reason",
    ]:
        assert forbidden not in public_contract
