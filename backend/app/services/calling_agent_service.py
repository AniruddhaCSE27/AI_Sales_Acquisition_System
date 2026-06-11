from __future__ import annotations

import json
import re

from app.core.config import settings
from app.schemas import CallingAgentRequest
from app.services.twilio_service import TwilioService


class CallingAgentService:
    def generate_script(self, payload: CallingAgentRequest) -> dict:
        fallback = self._fallback_script(payload)
        if not settings.openai_api_key:
            return fallback
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "Create a compliant sales call script. Return JSON with opening_line, qualification_questions, objection_handling, closing_line, and full_script.",
                    },
                    {"role": "user", "content": json.dumps(payload.model_dump(exclude={"consent"}))},
                ],
            )
            generated = json.loads(response.choices[0].message.content or "{}")
            if all(key in generated for key in fallback):
                return generated
        except Exception:
            pass
        return fallback

    def simulate(self, payload: CallingAgentRequest) -> dict[str, str]:
        script = self.generate_script(payload)
        reply = self._customer_reply(payload)
        objection = self.detect_objection(" ".join([payload.objective, payload.product, reply]))
        suggested_response = self.objection_response(objection, payload.product)
        next_response = suggested_response
        lead_score = self.lead_score(payload, objection)
        interest_level = "High" if lead_score >= 75 else "Medium" if lead_score >= 50 else "Low"
        return {
            "ai_agent_message": script["opening_line"],
            "customer_possible_reply": reply,
            "next_ai_response": next_response,
            "call_summary": f"Simulated {payload.tone.lower()} {payload.language} call with {payload.lead_name} about {payload.product}. The lead requested more information before committing.",
            "interest_level": interest_level,
            "sentiment": "Positive" if lead_score >= 70 else "Neutral",
            "lead_score": lead_score,
            "detected_objection": objection,
            "ai_suggested_response": suggested_response,
            "next_best_action": f"Send a concise {payload.product} overview and schedule a consented follow-up focused on {payload.objective.lower()}.",
        }

    def start_real_call(self, payload: CallingAgentRequest) -> dict:
        if not payload.consent:
            raise ValueError("Consent is required before starting a real call.")
        if not self.valid_phone(payload.phone_number):
            raise ValueError("Enter a valid phone number including country code.")
        if not all((settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number)):
            return {
                "started": False,
                "status": "not_configured",
                "message": "Real calling is not configured. Add Twilio credentials to enable live calls.",
                "call_sid": None,
            }
        call_sid = TwilioService().start_call(payload.phone_number)
        return {"started": True, "status": "initiated", "message": "Real call initiated.", "call_sid": call_sid}

    @staticmethod
    def valid_phone(value: str) -> bool:
        return bool(re.fullmatch(r"\+?[1-9]\d{7,14}", re.sub(r"[\s()-]", "", value)))

    @staticmethod
    def twilio_configured() -> bool:
        return all((settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number))

    @staticmethod
    def detect_objection(text: str) -> str:
        lowered = text.lower()
        categories = {
            "Pricing": ("price", "pricing", "cost", "budget", "expensive", "fee"),
            "Timing": ("timing", "later", "busy", "not now", "timeline"),
            "Competitor": ("competitor", "other provider", "another company", "alternative"),
            "Need": ("need", "not sure", "not interested", "why"),
            "Trust": ("trust", "proof", "reviews", "credible", "guarantee"),
        }
        for category, terms in categories.items():
            if any(term in lowered for term in terms):
                return category
        return "Need"

    @staticmethod
    def objection_response(objection: str, product: str) -> str:
        responses = {
            "Pricing": f"I understand budget matters. Let me explain the value of {product} and the available options without any pressure.",
            "Timing": "Absolutely. What timing would be more convenient for a short, consented follow-up?",
            "Competitor": f"That makes sense. I can give you a concise, factual comparison so you can decide whether {product} fits your priorities.",
            "Need": f"Let us first clarify the outcome you want, then we can determine honestly whether {product} is relevant.",
            "Trust": "I understand. I can share verifiable details, customer evidence, and clear next steps before you decide.",
        }
        return responses[objection]

    @staticmethod
    def lead_score(payload: CallingAgentRequest, objection: str) -> float:
        score = 55
        if payload.objective:
            score += 12
        if payload.consent:
            score += 10
        if objection in {"Pricing", "Timing"}:
            score += 8
        return float(min(score, 100))

    def _fallback_script(self, payload: CallingAgentRequest) -> dict:
        name = payload.lead_name.strip().split()[0]
        if payload.language == "Hindi":
            opening = f"Namaste {name}, main LeadForge team se bol raha hoon. Kya abhi {payload.product} ke baare mein do minute baat karna theek rahega?"
            closing = f"Dhanyavaad {name}. Main aapko jaankari bhejta hoon aur aapki sahmati se agla samay nirdharit karunga."
        elif payload.language == "Hinglish":
            opening = f"Hi {name}, main LeadForge team se bol raha hoon. Kya abhi {payload.product} ke baare mein two minutes baat karna convenient hai?"
            closing = f"Thanks {name}. Main details share karta hoon aur aapki consent se next follow-up schedule karunga."
        else:
            opening = f"Hello {name}, this is the LeadForge team. Is now a convenient time for a brief conversation about {payload.product}?"
            closing = f"Thank you, {name}. I will share the relevant details and schedule the next step only with your agreement."

        questions = [
            f"What are you hoping to achieve with {payload.product}?",
            "What is your expected timeline for making a decision?",
            "Who else is involved in the decision?",
            "Is there a budget range or constraint we should consider?",
        ]
        objections = [
            "Price: acknowledge the concern, clarify value, and offer relevant options without pressure.",
            "Timing: ask what timing would be more suitable and agree on a consented follow-up.",
            "Need more information: summarize the key benefit and offer a concise written overview.",
        ]
        full_script = "\n\n".join(
            [
                f"OPENING\n{opening}",
                "QUALIFICATION\n" + "\n".join(f"- {question}" for question in questions),
                "OBJECTION HANDLING\n" + "\n".join(f"- {item}" for item in objections),
                f"OBJECTIVE\nGuide the conversation toward: {payload.objective}.",
                f"CLOSING\n{closing}",
            ]
        )
        return {
            "opening_line": opening,
            "qualification_questions": questions,
            "objection_handling": objections,
            "closing_line": closing,
            "full_script": full_script,
        }

    @staticmethod
    def _customer_reply(payload: CallingAgentRequest) -> str:
        return f"I am interested in {payload.product}, but I need to understand the pricing and next steps before deciding."
