from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import CallTranscript, Lead, Report, VectorEmbedding
from app.services.embedding_service import EmbeddingService


class RAGService:
    """Tenant-aware retrieval over lead notes, transcripts, reports, and KB rows."""

    def __init__(self) -> None:
        self.embeddings = EmbeddingService()

    def index_workspace(self, db: Session, organization_id: int | None = None) -> dict:
        count = 0
        lead_query = db.query(Lead)
        if organization_id is not None:
            lead_query = lead_query.filter(Lead.organization_id == organization_id)
        for lead in lead_query.limit(1000).all():
            content = " ".join(filter(None, [lead.name, lead.course_interest, lead.city, lead.lead_notes, str(lead.score_explanation)]))
            if content.strip():
                self.upsert(db, organization_id, "lead_notes_embeddings", "lead", lead.id, content, {"status": lead.status.value})
                count += 1

        for transcript in db.query(CallTranscript).limit(1000).all():
            self.upsert(db, organization_id, "call_transcript_embeddings", "call_transcript", transcript.id, transcript.transcript, transcript.analysis)
            count += 1

        report_query = db.query(Report)
        if organization_id is not None:
            report_query = report_query.filter(Report.organization_id == organization_id)
        for report in report_query.limit(500).all():
            self.upsert(db, organization_id, "report_embeddings", "report", report.id, f"{report.title} {report.insights}", report.insights)
            count += 1
        db.commit()
        return {"indexed": count}

    def upsert(self, db: Session, organization_id: int | None, collection: str, entity_type: str, entity_id: int | None, content: str, metadata: dict) -> VectorEmbedding:
        row = (
            db.query(VectorEmbedding)
            .filter(VectorEmbedding.collection == collection, VectorEmbedding.entity_type == entity_type, VectorEmbedding.entity_id == entity_id)
            .first()
        )
        if row is None:
            row = VectorEmbedding(collection=collection, entity_type=entity_type, entity_id=entity_id)
            db.add(row)
        row.organization_id = organization_id
        row.content = content
        row.embedding = self.embeddings.embed_text(content)
        row.metadata_json = metadata or {}
        return row

    def retrieve(self, db: Session, question: str, organization_id: int | None = None, limit: int = 6) -> list[dict]:
        query_embedding = self.embeddings.embed_text(question)
        query = db.query(VectorEmbedding)
        if organization_id is not None:
            query = query.filter(VectorEmbedding.organization_id == organization_id)
        scored = []
        for row in query.order_by(VectorEmbedding.created_at.desc()).limit(2000).all():
            scored.append((self.embeddings.similarity(query_embedding, row.embedding), row))
        return [
            {
                "score": round(score, 4),
                "collection": row.collection,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "content": row.content[:800],
                "metadata": row.metadata_json,
            }
            for score, row in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]
        ]

    def answer(self, db: Session, question: str, organization_id: int | None = None) -> dict:
        contexts = self.retrieve(db, question, organization_id)
        if not contexts:
            self.index_workspace(db, organization_id)
            contexts = self.retrieve(db, question, organization_id)
        context_text = "\n".join(f"- {item['content']}" for item in contexts)
        if not context_text:
            return {"answer": "There is not enough CRM data yet. Add leads, calls, notes, or reports first.", "recommendations": ["Import leads", "Capture call notes", "Generate a weekly report"], "sources": []}
        answer = f"Based on current CRM records: {context_text[:900]}"
        recommendations = ["Prioritize high-score leads", "Review objections by source", "Coach low-conversion follow-up behavior"]
        return {"answer": answer, "recommendations": recommendations, "sources": contexts}
