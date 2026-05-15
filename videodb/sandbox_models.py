from enum import Enum


class SandboxModel(str, Enum):
    """Models that can run on VideoDB Sandbox compute."""

    # GenAI
    FLUX = "flux"
    OMNIVOICE = "omnivoice"

    # Small tier
    GEMMA_4_E2B = "google/gemma-4-E2B-it"
    QWEN_9B = "Qwen/Qwen3.5-9B"
    WHISPER_LARGE_V3_TURBO = "openai/whisper-large-v3-turbo"
    OMNIVOICE_CANONICAL = "k2-fsa/OmniVoice"
    STABLE_AUDIO_OPEN = "stabilityai/stable-audio-open-1.0"

    # Medium tier
    GEMMA_4_26B = "google/gemma-4-26B-A4B-it"
    QWEN_27B = "Qwen/Qwen3.5-27B"
    FLUX_CANONICAL = "black-forest-labs/FLUX.1-dev"
    GEMMA_4_31B = "google/gemma-4-31B-it"

