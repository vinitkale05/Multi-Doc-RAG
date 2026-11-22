import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sqlalchemy import select
from app.core.database import init_db, AsyncSessionLocal
from app.core.security import hash_password
from app.models import Tenant, User, Collection, Document, Chunk
from app.services.ingestion.pipeline import ingestion_pipeline


SAMPLE_DOCS = [
    {
        "filename": "MSA_Acme_Corporation.txt",
        "mime_type": "text/plain",
        "content": """MASTER SERVICES AGREEMENT (ACME CORPORATION)
1. Term and Renewal
This Master Services Agreement ("Agreement") shall commence on the Effective Date and continue for a period of one (1) year.
The agreement renews automatically for successive one-year terms unless either party provides written notice of non-renewal at least thirty (30) days prior to the expiration of the then-current term.

2. Service Level Guarantees
Acme commits to a 99.9% monthly uptime SLA across all primary API endpoints. If monthly uptime falls below 99.9%, Client is entitled to a 10% service credit.
Support response times are tiered: Critical issues will be responded to within 15 minutes; standard tickets within 4 hours.

3. Termination for Convenience
Either party may terminate this Agreement without cause by providing sixty (60) days prior written notice to the other party."""
    },
    {
        "filename": "Cloud_Security_Runbook.txt",
        "mime_type": "text/plain",
        "content": """CLOUD SECURITY RUNBOOK: KEY ROTATION PROCEDURES
Section 1: Production API Key Rotation
When rotating production master keys or service credentials, follow these sequential steps:
1. Generate a new secondary key pair in AWS KMS / GCP Cloud KMS with rotation tag.
2. Update the secret value in HashiCorp Vault under the production cluster path.
3. Deploy canary pods to verify authentication against the secondary key.
4. After 24 hours of stable traffic with zero 401/403 authorization anomalies, revoke and delete the primary key.

Section 2: Security Incident Protocol
In case of suspected credential exfiltration, immediately revoke active tokens via Redis session invalidation and alert the SOC team."""
    },
    {
        "filename": "Vendor_Support_Tiers_2026.csv",
        "mime_type": "text/csv",
        "content": """Tier,Monthly_Cost,Response_Time,Dedicated_TAM,SLA_Uptime
Standard,$200,4 hours,No,99.5%
Professional,$500,1 hour,No,99.9%
Enterprise,$1200,15 minutes,Yes,99.99%"""
    }
]


async def seed():
    print("Initializing database and seeding demo tenant, users, and documents...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Create or get Default Tenant
        t_q = select(Tenant).where(Tenant.id == "tenant_default")
        tenant = (await session.execute(t_q)).scalars().first()
        if not tenant:
            tenant = Tenant(
                id="tenant_default",
                name="MIT-ADT University AI Lab",
                plan="enterprise",
                quota_tokens=5000000,
                quota_storage=10 * 1024 * 1024 * 1024
            )
            session.add(tenant)
            await session.flush()

        # 2. Upsert Admin and Researcher Users
        admin_q = select(User).where(User.email == "admin@rag.local")
        admin_user = (await session.execute(admin_q)).scalars().first()
        if admin_user:
            admin_user.password_hash = hash_password("AdminPass123!")
        else:
            admin_user = User(
                id="user_admin_01",
                email="admin@rag.local",
                password_hash=hash_password("AdminPass123!"),
                role="admin",
                tenant_id=tenant.id
            )
            session.add(admin_user)

        member_q = select(User).where(User.email == "researcher@rag.local")
        member_user = (await session.execute(member_q)).scalars().first()
        if member_user:
            member_user.password_hash = hash_password("MemberPass123!")
        else:
            member_user = User(
                id="user_member_01",
                email="researcher@rag.local",
                password_hash=hash_password("MemberPass123!"),
                role="member",
                tenant_id=tenant.id
            )
            session.add(member_user)

        # Also add vinit.kale@mitadt.edu.in
        vinit_q = select(User).where(User.email == "vinit.kale@mitadt.edu.in")
        vinit_user = (await session.execute(vinit_q)).scalars().first()
        if vinit_user:
            vinit_user.password_hash = hash_password("SecurePassword123!")
        else:
            vinit_user = User(
                id="user_vinit_01",
                email="vinit.kale@mitadt.edu.in",
                password_hash=hash_password("SecurePassword123!"),
                role="admin",
                tenant_id=tenant.id
            )
            session.add(vinit_user)

        await session.flush()

        # 3. Create or get Collection
        col_q = select(Collection).where(Collection.id == "col_contracts_and_runbooks")
        col = (await session.execute(col_q)).scalars().first()
        if not col:
            col = Collection(
                id="col_contracts_and_runbooks",
                tenant_id=tenant.id,
                name="Enterprise Contracts & Runbooks",
                description="Verified collection containing MSAs, SLAs, security runbooks, and vendor pricing.",
                chunk_config={"chunk_size": 700, "chunk_overlap": 100}
            )
            session.add(col)
            await session.flush()

        # 4. Ingest sample documents if missing
        for doc_info in SAMPLE_DOCS:
            doc_q = select(Document).where(Document.filename == doc_info["filename"], Document.collection_id == col.id)
            existing_doc = (await session.execute(doc_q)).scalars().first()
            if existing_doc and existing_doc.status == "READY":
                print(f"  -> Already indexed: {existing_doc.filename}")
                continue

            raw_bytes = doc_info["content"].encode("utf-8")
            doc = Document(
                collection_id=col.id,
                filename=doc_info["filename"],
                mime_type=doc_info["mime_type"],
                size=len(raw_bytes),
                sha256="seed_hash_" + doc_info["filename"][:10],
                storage_uri=f"file://./storage_data/{doc_info['filename']}",
                status="QUEUED"
            )
            session.add(doc)
            await session.flush()

            await ingestion_pipeline.ingest_document(
                db=session,
                document_id=doc.id,
                content_bytes=raw_bytes,
                filename=doc.filename,
                mime_type=doc.mime_type,
                tenant_id=tenant.id
            )
            print(f"  -> Ingested: {doc.filename} (Status: {doc.status}, Page Count: {doc.page_count})")

        await session.commit()

    print("\nSeeding Complete!")
    print("Demo Admin: admin@rag.local / AdminPass123!")
    print("Demo Member: researcher@rag.local / MemberPass123!")
    print("Author Admin: vinit.kale@mitadt.edu.in / SecurePassword123!")
    print("Ready to run tests and launch services.")


if __name__ == "__main__":
    asyncio.run(seed())
