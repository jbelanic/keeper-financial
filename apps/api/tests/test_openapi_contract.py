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
