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
