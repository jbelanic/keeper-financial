"""seed approved borrower consent wording

Revision ID: 20260728_0001
Revises: 20260726_0015
Create Date: 2026-07-28

Replaces the v1-draft placeholder consent catalog row with the owner-approved
borrower privacy/credit-use disclosure (borrower-privacy-credit-disclosure-2026-07-27-v1)
from docs/28 section 6. Keeps the placeholder row but deactivates it for audit
continuity. real_data_approved stays False: approved wording alone does not enable
real-data submission (gated by BORROWER_REAL_DATA_ENABLED + catalog real_data_approved
in production mode).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "20260728_0001"
down_revision = "20260726_0015"
branch_labels = None
depends_on = None

APPROVED_VERSION = "borrower-privacy-credit-disclosure-2026-07-27-v1"

APPROVED_WORDING = "\n".join(
    [
        "Keeper Financial Inc. collects applicant information to create and administer your account, receive and review mortgage applications for the mortgage products you select, communicate with you about those applications, protect the portal, maintain application and access records, and operate the mortgage application process.",
        "We collect your verified account email and authentication/security metadata; the contact details you provide; the mortgage product and application details you select; your mortgage request, applicant identity and contact information, date of birth, Social Insurance Number, marital status, dependants, address history, employment and income, subject and other property details, assets and liabilities, notes, and any supporting documents you choose to upload with their file metadata; privacy acknowledgements; and application status, applicant-visible communications, history, and audit records. The Social Insurance Number and financial information are collected only as necessary to assess your mortgage request and are protected with application-level encryption; they are not shown in full to reviewers by default and are disclosed only to authorized brokerage administrators and the assigned mortgage agent reviewing your application.",
        "You can access your own applicant record. Within Keeper Financial, access is limited to authorized brokerage administrators and mortgage-application reviewers who need the information for the mortgage application process, security, support, or records administration. Internal notes are not shown to applicants. Service providers that host or support identity, application, database, private file-storage, security, monitoring, or communications functions may process information only to provide those services under Keeper Financial's direction and applicable safeguards. Applicant information is not provided to service providers for their own independent marketing.",
        "Submitted applications, supporting documents, acknowledgement records, and security/audit records are retained under Keeper Financial's approved, policy-controlled retention categories for only as long as reasonably needed for the mortgage application process, records administration, security, dispute handling, and applicable obligations, including a seven-year retention period for submitted applications. Retention may differ for abandoned drafts, withdrawn applications, documents, and security or audit records. Records are deleted or de-identified when the applicable approved policy permits, subject to a documented legal or security hold. This notice does not promise an unsupported fixed legal retention period.",
        "Required fields are needed to identify and contact you, assess your mortgage request, associate the application with the selected product, review the application, and record that this disclosure was shown. If you omit required information or do not acknowledge this disclosure, you may save a draft but cannot submit the application. Optional answers and optional documents may be omitted without preventing submission, although reviewers will not have information you choose not to provide.",
        "For privacy questions or requests, contact support@keeperfinancial.ca. Do not email sensitive documents; use the authenticated portal for permitted uploads.",
        "Version: borrower-privacy-credit-disclosure-2026-07-27-v1",
    ]
)

APPROVED_DIGEST = hashlib.sha256(APPROVED_WORDING.encode("utf-8")).hexdigest()


def upgrade() -> None:
    # Deactivate the placeholder row; retain it for audit continuity.
    op.execute(
        sa.text(
            "UPDATE borrower_consent_catalog "
            "SET is_active = FALSE, effective_to = :ts "
            "WHERE consent_version = 'v1-draft' AND is_active = TRUE"
        ).bindparams(ts=datetime.now(UTC))
    )

    op.bulk_insert(
        sa.table(
            "borrower_consent_catalog",
            sa.column("id", sa.Uuid()),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
            sa.column("consent_version", sa.String()),
            sa.column("wording_digest", sa.String()),
            sa.column("wording_text", sa.Text()),
            sa.column("is_active", sa.Boolean()),
            sa.column("real_data_approved", sa.Boolean()),
            sa.column("effective_from", sa.DateTime(timezone=True)),
        ),
        [
            {
                "id": uuid.uuid4(),
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "consent_version": APPROVED_VERSION,
                "wording_digest": APPROVED_DIGEST,
                "wording_text": APPROVED_WORDING,
                "is_active": True,
                "real_data_approved": False,
                "effective_from": datetime.now(UTC),
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM borrower_consent_catalog "
            "WHERE consent_version = :ver AND wording_digest = :dig"
        ).bindparams(ver=APPROVED_VERSION, dig=APPROVED_DIGEST)
    )
    op.execute(
        sa.text(
            "UPDATE borrower_consent_catalog "
            "SET is_active = TRUE, effective_to = NULL "
            "WHERE consent_version = 'v1-draft'"
        )
    )
