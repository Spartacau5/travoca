import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "pFZP5JQG7iQjIQuC4Bku")
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    PIPECAT_HOST: str = os.getenv("PIPECAT_HOST", "0.0.0.0")
    PIPECAT_PORT: int = int(os.getenv("PIPECAT_PORT", "7860"))

    def validate(self):
        required = [
            ("ANTHROPIC_API_KEY", self.ANTHROPIC_API_KEY),
            ("DEEPGRAM_API_KEY", self.DEEPGRAM_API_KEY),
            ("ELEVENLABS_API_KEY", self.ELEVENLABS_API_KEY),
            ("SUPABASE_URL", self.SUPABASE_URL),
            ("SUPABASE_SERVICE_KEY", self.SUPABASE_SERVICE_KEY),
        ]
        missing = [name for name, val in required if not val]
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")


settings = Settings()
