from dataclasses import dataclass

from jinja2 import Template

from app.services.twilio_service import TwilioService


@dataclass(frozen=True)
class WhatsAppTemplate:
    name: str
    body: str


class WhatsAppAutomationService:
    TEMPLATES = {
        "follow_up": WhatsAppTemplate("follow_up", "Hi {{ name }}, following up on your interest in {{ course }}. Can we schedule a counselling call today?"),
        "hot_lead_alert": WhatsAppTemplate("hot_lead_alert", "Hot lead alert: {{ name }} scored {{ score }} and needs callback within 15 minutes."),
        "scholarship": WhatsAppTemplate("scholarship", "Hi {{ name }}, scholarship and EMI options are available for {{ course }}. Reply YES for details."),
        "missed_call": WhatsAppTemplate("missed_call", "We missed your call, {{ name }}. A counsellor will call you shortly."),
        "inactive_lead": WhatsAppTemplate("inactive_lead", "Hi {{ name }}, admissions are closing soon for {{ course }}. Would you like help deciding?"),
        "manager_alert": WhatsAppTemplate("manager_alert", "Manager alert: {{ message }}"),
    }

    def __init__(self) -> None:
        self.twilio = TwilioService()

    def render(self, template_name: str, context: dict) -> str:
        template = self.TEMPLATES[template_name]
        return Template(template.body).render(**context)

    def send(self, to_phone: str, template_name: str, context: dict) -> dict:
        message = self.render(template_name, context)
        sid = self.twilio.send_whatsapp(to_phone, message)
        return {"sid": sid, "template": template_name, "message": message, "to": to_phone}
