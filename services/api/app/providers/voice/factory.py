from app.config.settings import Settings
from app.providers.voice.base import SpeechToTextProvider, TextToSpeechProvider, VoiceProviderUnavailable


def create_stt_provider(settings: Settings) -> SpeechToTextProvider:
    raise VoiceProviderUnavailable("stt_unavailable")


def create_tts_provider(settings: Settings) -> TextToSpeechProvider:
    raise VoiceProviderUnavailable("tts_unavailable")
