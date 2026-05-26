from app.core.config import settings


class TwilioService:
    def start_call(self, to_phone: str) -> str:
        if not settings.twilio_account_sid:
            return "demo-twilio-call-sid"
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        call = client.calls.create(
            to=to_phone,
            from_=settings.twilio_phone_number,
            url=f"{settings.public_base_url}/api/v1/calls/twilio/voice",
            record=True,
        )
        return call.sid

    def start_streaming_call(self, to_phone: str, lead_id: int | None = None) -> dict:
        stream_url = settings.public_base_url.replace("http://", "ws://").replace("https://", "wss://") + settings.twilio_stream_path
        if not settings.twilio_account_sid:
            return {
                "call_sid": "demo-twilio-call-sid",
                "stream_url": stream_url,
                "lead_id": lead_id,
                "recording_enabled": True,
                "mode": "demo",
            }
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        call = client.calls.create(
            to=to_phone,
            from_=settings.twilio_phone_number,
            url=f"{settings.public_base_url}/api/v1/calls/twilio/voice?lead_id={lead_id or ''}",
            record=True,
        )
        return {"call_sid": call.sid, "stream_url": stream_url, "lead_id": lead_id, "recording_enabled": True, "mode": "live"}

    def send_whatsapp(self, to_phone: str, message: str) -> str:
        if not settings.twilio_account_sid:
            return "demo-whatsapp-message-sid"
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        msg = client.messages.create(from_=f"whatsapp:{settings.twilio_phone_number}", to=f"whatsapp:{to_phone}", body=message)
        return msg.sid
