import pytest
from app.config.settings import Settings
from app.providers.voice.base import VoiceProviderUnavailable
from app.providers.voice.factory import create_stt_provider, create_tts_provider


def test_unconfigured_voice_providers_raise_explicit_errors():
    settings = Settings()
    with pytest.raises(VoiceProviderUnavailable, match="stt_unavailable"):
        create_stt_provider(settings)
    with pytest.raises(VoiceProviderUnavailable, match="tts_unavailable"):
        create_tts_provider(settings)
