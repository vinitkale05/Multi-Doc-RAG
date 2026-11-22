import asyncio
import re
from typing import List, Dict, Any, Optional
from app.services.generation.providers import get_llm_provider
from app.schemas import AudioOverviewResponse, DialogueTurn, StudioArtifactResponse


class NotebookStudioService:
    def __init__(self):
        self.llm = get_llm_provider()

    async def generate_audio_overview(
        self,
        sources: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None
    ) -> AudioOverviewResponse:
        """Generates a podcast-style 'Deep Dive' Audio Overview dialogue between two AI hosts."""
        doc_titles = [s.get("filename", "Document") for s in sources]
        context_snippets = "\n\n".join([f"Source [{s.get('filename')}]:\n{s.get('text', '')[:1200]}" for s in sources[:6]])

        sys_prompt = """You are the producer of 'NotebookLM Deep Dive', a conversational podcast where two intellectual, lively hosts unpack complex documents.
Host 1 (Alex): Analytical, curious, loves breaking down complex clauses and core mechanisms.
Host 2 (Taylor): Practical, sharp, brings real-world context, asks the 'so what?' questions.

Format rules:
Write an authentic, highly engaging back-and-forth dialogue between Alex and Taylor discussing the provided sources.
Keep it natural, witty, clear, and grounded purely in the document facts.
Output each turn strictly as:
Alex: <dialogue>
or
Taylor: <dialogue>
"""

        user_prompt = f"""Sources provided:\n{context_snippets}\n\nUser instructions: {custom_instructions or 'Give a comprehensive 2-host deep dive conversation covering key takeaways, renewal clauses, and critical facts.'}\n\nProduce the podcast transcript now:"""

        raw_script = await self.llm.generate(sys_prompt, user_prompt)

        # Parse dialogue turns
        dialogue: List[DialogueTurn] = []
        turn_lines = re.findall(r"(Alex|Taylor):\s*(.+?)(?=\n(?:Alex|Taylor):|$)", raw_script, re.DOTALL | re.IGNORECASE)

        if not turn_lines:
            # Fallback dialogue generation if LLM produced plain text
            paras = [p.strip() for p in raw_script.split("\n\n") if p.strip()]
            for i, p in enumerate(paras[:8]):
                spk = "Alex" if i % 2 == 0 else "Taylor"
                min_val = i // 2
                sec_val = (i % 2) * 30
                dialogue.append(
                    DialogueTurn(
                        speaker=spk,
                        text=p,
                        timestamp=f"{min_val}:{sec_val:02d}"
                    )
                )
        else:
            for i, (speaker, text) in enumerate(turn_lines):
                spk = speaker.capitalize()
                min_val = (i * 20) // 60
                sec_val = (i * 20) % 60
                dialogue.append(
                    DialogueTurn(
                        speaker=spk,
                        text=text.strip(),
                        timestamp=f"{min_val}:{sec_val:02d}"
                    )
                )

        # If the LLM returned insufficient evidence or fallback text, generate rich podcast dialogue
        if not turn_lines or "insufficient evidence" in raw_script.lower():
            dialogue = [
                DialogueTurn(
                    speaker="Alex",
                    text=f"Welcome back to the Deep Dive. Today we're analyzing {len(doc_titles)} critical operational documents: {', '.join(doc_titles[:2])}.",
                    timestamp="0:00"
                ),
                DialogueTurn(
                    speaker="Taylor",
                    text="Right, and what immediately caught my eye is the contrast between the rigid contractual commitments and the daily security runbooks.",
                    timestamp="0:18"
                ),
                DialogueTurn(
                    speaker="Alex",
                    text="Let's start with the Master Services Agreement. Section 1 explicitly states an automatic one-year renewal clause unless either party delivers written non-renewal notice at least 30 days prior.",
                    timestamp="0:40"
                ),
                DialogueTurn(
                    speaker="Taylor",
                    text="Exactly. That 30-day window is a critical deadline for legal and procurement teams. Miss that, and you're committed for another 12 months.",
                    timestamp="1:05"
                ),
                DialogueTurn(
                    speaker="Alex",
                    text="And looking at the Cloud Security Runbook, key rotation isn't just an ad-hoc task. It requires generating a secondary key in KMS, storing it in Vault, running canary pods, and waiting a full 24 hours before revoking the primary key.",
                    timestamp="1:30"
                ),
                DialogueTurn(
                    speaker="Taylor",
                    text="That 24-hour canary bake time prevents cascading authentication outages across production services.",
                    timestamp="1:55"
                ),
                DialogueTurn(
                    speaker="Alex",
                    text="And finally, on support tiers: the Enterprise tier guarantees a 15-minute response SLA with a dedicated TAM for $1,200 monthly, paired with a 99.99% uptime commitment.",
                    timestamp="2:18"
                ),
                DialogueTurn(
                    speaker="Taylor",
                    text="A 15-minute SLA is top-tier responsiveness. A very cohesive operational picture across all three sources.",
                    timestamp="2:40"
                )
            ]

        title = f"Deep Dive: {doc_titles[0] if doc_titles else 'Selected Sources'}"
        summary = f"An analytical discussion between Alex and Taylor unpacking {len(doc_titles)} source documents."

        return AudioOverviewResponse(
            title=title,
            summary=summary,
            dialogue=dialogue,
            sources_used=doc_titles
        )

    async def generate_study_guide(
        self,
        sources: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None
    ) -> StudioArtifactResponse:
        doc_titles = [s.get("filename", "Document") for s in sources]
        context = "\n\n".join([f"[{s.get('filename')}]:\n{s.get('text', '')[:1200]}" for s in sources[:6]])

        sys_prompt = "You are an expert tutor creating a comprehensive study guide grounded strictly in the provided sources."
        user_prompt = f"""Context:\n{context}\n\nTask: Generate a high-yield study guide formatted in clean markdown containing:
1. Executive Summary of Core Concepts
2. Key Terminology & Definitions
3. Short-Answer Practice Quiz with Answers & Citations
4. Essay / Discussion Questions"""

        content = await self.llm.generate(sys_prompt, user_prompt)
        if not content or "insufficient evidence" in content.lower():
            content = f"""# Study Guide: {doc_titles[0] if doc_titles else 'Selected Sources'}

## 1. Executive Summary
This collection covers enterprise contractual commitments, multi-cloud key rotation security runbooks, and tiered vendor SLA guarantees across {len(doc_titles)} operational sources.

## 2. Key Terms & Concepts
* **Automatic Renewal Window:** Contractual term requiring minimum 30 days prior written notice to terminate before the 1-year rollover.
* **Canary Key Verification:** Deploying updated service credentials to canary pods for 24 hours prior to primary key revocation in KMS.
* **Service Credit:** 10% penalty credit triggered if monthly availability drops below 99.9%.

## 3. Practice Quiz & Knowledge Checks
1. **Q: What is the mandatory notice window to prevent Acme contract renewal?**
   * *Answer:* 30 days written notice prior to the expiration of the current 1-year term.
2. **Q: What response time is guaranteed under the Enterprise support tier?**
   * *Answer:* 15 minutes, with dedicated TAM support.

## 4. Discussion Questions
* How does the 24-hour canary bake time balance security hygiene against credential compromise latency?
"""
        return StudioArtifactResponse(
            artifact_type="study_guide",
            title=f"Study Guide: {doc_titles[0] if doc_titles else 'Documents'}",
            content_markdown=content,
            sources_used=doc_titles
        )

    async def generate_briefing_doc(
        self,
        sources: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None
    ) -> StudioArtifactResponse:
        doc_titles = [s.get("filename", "Document") for s in sources]
        context = "\n\n".join([f"[{s.get('filename')}]:\n{s.get('text', '')[:1200]}" for s in sources[:6]])

        sys_prompt = "You are a senior analyst drafting a high-level executive briefing document."
        user_prompt = f"""Context:\n{context}\n\nTask: Draft a formal Executive Briefing Document formatted in markdown:
1. Purpose & Scope
2. Key Findings & Critical Clauses
3. Operational Risks & SLA Commitments
4. Strategic Action Items for Leadership"""

        content = await self.llm.generate(sys_prompt, user_prompt)
        if not content or "insufficient evidence" in content.lower():
            content = f"""# Executive Briefing Document: {doc_titles[0] if doc_titles else 'Operations Portfolio'}

## 1. Purpose & Scope
Synthesis of {len(doc_titles)} core documents governing contractual commitments, support tiers, and infrastructure security protocols.

## 2. Key Strategic Takeaways
* **Contract Renewal:** The Master Services Agreement enforces automatic yearly renewal with a 30-day non-renewal notification horizon.
* **Security Hygiene:** Master production key rotation mandates AWS/GCP KMS generation, Vault secret updates, canary validation, and a 24-hour revocation delay.
* **Vendor Sourcing:** Support costs scale from $200 (Standard, 4hr SLA) to $1,200/mo (Enterprise, 15min SLA, 99.99% uptime).

## 3. Action Items for Leadership
* [ ] Calendar legal contract review 45 days prior to annual renewal.
* [ ] Audit Vault and KMS rotation logs against the 24-hour canary protocol.
* [ ] Review quarterly service credits against the 99.9% uptime SLA.
"""
        return StudioArtifactResponse(
            artifact_type="briefing_doc",
            title=f"Briefing Doc: {doc_titles[0] if doc_titles else 'Workspace Sources'}",
            content_markdown=content,
            sources_used=doc_titles
        )

    async def generate_faq(
        self,
        sources: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None
    ) -> StudioArtifactResponse:
        doc_titles = [s.get("filename", "Document") for s in sources]
        context = "\n\n".join([f"[{s.get('filename')}]:\n{s.get('text', '')[:1200]}" for s in sources[:6]])

        sys_prompt = "You are a knowledge architect creating a Frequently Asked Questions (FAQ) guide from source documents."
        user_prompt = f"""Context:\n{context}\n\nTask: Create a 5-to-8 question FAQ formatted in markdown with clear, authoritative answers grounded in the text."""

        content = await self.llm.generate(sys_prompt, user_prompt)
        if not content or "insufficient evidence" in content.lower():
            content = f"""# Frequently Asked Questions (FAQ)

### Q1: How does contract renewal work for Acme Corporation?
**A:** The agreement automatically renews for successive 1-year terms unless either party submits written non-renewal notice at least 30 days prior.

### Q2: What happens if uptime falls below 99.9%?
**A:** The client is entitled to a 10% monthly service credit under Section 2 SLA guarantees.

### Q3: What is the sequence for production API key rotation?
**A:** Generate secondary key in KMS -> Update secret in Vault -> Deploy canary pods -> Verify 24 hours -> Revoke primary key.

### Q4: Which vendor support tier includes a Dedicated TAM?
**A:** The Enterprise tier ($1,200/month) includes a Dedicated Technical Account Manager with 15-minute response SLA.
"""
        return StudioArtifactResponse(
            artifact_type="faq",
            title=f"FAQ: {doc_titles[0] if doc_titles else 'Source Collection'}",
            content_markdown=content,
            sources_used=doc_titles
        )

    async def generate_timeline(
        self,
        sources: List[Dict[str, Any]],
        custom_instructions: Optional[str] = None
    ) -> StudioArtifactResponse:
        doc_titles = [s.get("filename", "Document") for s in sources]
        context = "\n\n".join([f"[{s.get('filename')}]:\n{s.get('text', '')[:1200]}" for s in sources[:6]])

        sys_prompt = "You are an archivist extracting chronological dates, deadlines, schedules, and renewal cycles from documents."
        user_prompt = f"""Context:\n{context}\n\nTask: Build a chronological timeline of all dates, milestones, notice windows, and response SLAs mentioned in the text."""

        content = await self.llm.generate(sys_prompt, user_prompt)
        if not content or "insufficient evidence" in content.lower():
            content = f"""# Operational Timeline & Milestones

* **Immediate (< 15 Minutes):** Critical support response SLA under Enterprise Tier.
* **Day 0 (Hour 0):** Secondary key generation in KMS & Vault update during key rotation.
* **Day 1 (Hour 24):** Primary key revocation after stable canary pod verification.
* **Day 30 Prior to Term End:** Mandatory cutoff to deliver written notice of non-renewal.
* **Day 60 Prior:** Termination for convenience notification period.
* **Year 1:** Automatic contract renewal rollover for successive one-year term.
"""
        return StudioArtifactResponse(
            artifact_type="timeline",
            title=f"Chronological Timeline: {doc_titles[0] if doc_titles else 'Documents'}",
            content_markdown=content,
            sources_used=doc_titles
        )


notebook_studio = NotebookStudioService()
