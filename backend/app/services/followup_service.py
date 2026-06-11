from __future__ import annotations

from app.models import CustomerMemory, Lead


class FollowUpService:
    def generate(self, lead: Lead, memory: CustomerMemory | None = None, objective: str | None = None, tone: str = "professional") -> dict[str, str]:
        course = lead.course_interest or "your preferred program"
        objective_text = objective or (memory.next_action if memory and memory.next_action else None) or "schedule the next counselling step"
        objection_text = ""
        if memory and memory.objections:
            objection_text = f" I can also help clarify {', '.join(memory.objections)} concerns."
        name = lead.name.split()[0] if lead.name else "there"
        whatsapp = f"Hi {name}, this is a quick follow-up on {course}. {objective_text.capitalize()}.{objection_text} What time works for a short call?"
        subject = f"Next steps for {course}"
        body = (
            f"Hi {lead.name},\n\n"
            f"Thank you for your interest in {course}. Based on our last conversation, the best next step is to {objective_text}."
            f"{objection_text}\n\n"
            "Please reply with a convenient time and I will coordinate the next step.\n\n"
            "Regards,\nLeadForge AI Sales Team"
        )
        script = (
            f"Open: Confirm you are speaking with {lead.name} and reference {course}.\n"
            f"Context: Summarize the last discussion in one sentence.\n"
            f"Need: Ask about timeline, budget, and decision maker.\n"
            f"Handle: Address {', '.join(memory.objections) if memory and memory.objections else 'course fit and fee'} clearly.\n"
            f"Close: Ask for agreement to {objective_text}."
        )
        return {"whatsapp_message": whatsapp, "email_subject": subject, "email_body": body, "call_script": script, "tone": tone}
