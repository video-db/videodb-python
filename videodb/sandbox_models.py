from enum import Enum


class SandboxModel(str, Enum):
    """Models that can run on VideoDB Sandbox compute."""

    # GenAI
    FLUX = "flux"
    OMNIVOICE = "omnivoice"

    # Small tier
    GEMMA_4_E2B = "google/gemma-4-E2B-it"
    GEMMA_4_E2B_FP8 = "google/gemma-4-E2B-it-FP8"
    QWEN_9B = "Qwen/Qwen3.5-9B"
    QWEN_9B_FP8 = "Qwen/Qwen3.5-9B-FP8"
    WHISPER_LARGE_V3_TURBO = "openai/whisper-large-v3-turbo"
    OMNIVOICE_CANONICAL = "k2-fsa/OmniVoice"
    STABLE_AUDIO_OPEN = "stabilityai/stable-audio-open-1.0"

    # Medium tier
    GEMMA_4_26B = "google/gemma-4-26B-A4B-it"
    GEMMA_4_26B_FP8 = "google/gemma-4-26B-A4B-it-FP8"
    QWEN_27B = "Qwen/Qwen3.5-27B"
    QWEN_27B_FP8 = "Qwen/Qwen3.5-27B-FP8"
    FLUX_CANONICAL = "black-forest-labs/FLUX.1-dev"

    # Large tier
    GEMMA_4_31B = "google/gemma-4-31B-it"
    QWEN_122B = "Qwen/Qwen3.5-122B-A10B"
