"""
MOSS-TTS-Nano ONNX CPU Runtime for tts-cli.

Provides standalone on-device inference for MOSS-TTS-Nano (100M LLM + 20M Cat
Tokenizer) using onnxruntime CPU execution provider.
"""

from __future__ import annotations

import json
import logging
import math
import shutil
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import onnxruntime as ort
import scipy.signal
import sentencepiece as spm
import soundfile as sf

from .normalizer import normalize_text_for_speech

logger = logging.getLogger(__name__)

SAMPLE_MODE_GREEDY = "greedy"
SAMPLE_MODE_FIXED = "fixed"
SAMPLE_MODE_FULL = "full"
EXECUTION_PROVIDER_CPU = "cpu"

DEFAULT_MOSS_TTS_REPO_ID = "OpenMOSS-Team/MOSS-TTS-Nano-100M-ONNX"
DEFAULT_MOSS_CODEC_REPO_ID = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"

SENTENCE_END_PUNCTUATION = set(".!?。！？；;")
CLAUSE_SPLIT_PUNCTUATION = set(",，、；;：:")
CLOSING_PUNCTUATION = set("\"'”’)]}）】》」』")


def _resolve_default_model_dir() -> Path:
    return Path.home() / ".tts-cli" / "models"


def ensure_moss_models_downloaded(model_dir: Path | None = None) -> Path:
    """Ensure MOSS-TTS ONNX models and tokenizer are downloaded and available."""
    target_dir = model_dir or _resolve_default_model_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    tts_dir = target_dir / "MOSS-TTS-Nano-100M-ONNX"
    codec_dir = target_dir / "MOSS-Audio-Tokenizer-Nano-ONNX"

    # Check if files already exist
    tts_manifest = tts_dir / "browser_poc_manifest.json"
    codec_meta = codec_dir / "codec_browser_onnx_meta.json"

    if tts_manifest.exists() and codec_meta.exists():
        return target_dir

    logger.info("Downloading MOSS-TTS-Nano ONNX models from Hugging Face...")
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError("huggingface_hub required to download MOSS-TTS models") from exc

    tts_dir.mkdir(parents=True, exist_ok=True)
    codec_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(DEFAULT_MOSS_TTS_REPO_ID, local_dir=str(tts_dir))
    snapshot_download(DEFAULT_MOSS_CODEC_REPO_ID, local_dir=str(codec_dir))
    return target_dir


class MossOnnxRuntime:
    """Encapsulates the multi-graph ONNX CPU inference for MOSS-TTS-Nano."""

    def __init__(
        self,
        model_dir: str | Path | None = None,
        thread_count: int = 4,
    ) -> None:
        self.model_dir = ensure_moss_models_downloaded(Path(model_dir) if model_dir else None)
        self.tts_dir = self.model_dir / "MOSS-TTS-Nano-100M-ONNX"
        self.codec_dir = self.model_dir / "MOSS-Audio-Tokenizer-Nano-ONNX"

        manifest_path = self.tts_dir / "browser_poc_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

        codec_meta_path = self.codec_dir / "codec_browser_onnx_meta.json"
        with open(codec_meta_path, "r", encoding="utf-8") as f:
            self.codec_meta = json.load(f)

        tokenizer_path = self.tts_dir / self.manifest["model_files"].get("tokenizer_model", "tokenizer.model")
        self.sp_model = spm.SentencePieceProcessor(model_file=str(tokenizer_path))

        self.thread_count = thread_count
        self.session_options = ort.SessionOptions()
        self.session_options.intra_op_num_threads = thread_count
        self.session_options.inter_op_num_threads = 1

        self._sessions: dict[str, ort.InferenceSession] = {}
        self._init_sessions()

    def _get_session(self, key: str, path: Path) -> ort.InferenceSession:
        if key not in self._sessions:
            self._sessions[key] = ort.InferenceSession(
                str(path),
                sess_options=self.session_options,
                providers=["CPUExecutionProvider"],
            )
        return self._sessions[key]

    def _init_sessions(self) -> None:
        model_files = self.manifest["model_files"]
        self.prefill_sess = self._get_session("prefill", self.tts_dir / model_files["prefill"])
        self.decode_step_sess = self._get_session("decode_step", self.tts_dir / model_files["decode_step"])
        self.local_fixed_sess = self._get_session("local_fixed", self.tts_dir / model_files["local_fixed_sampled_frame"])
        self.codec_encode_sess = self._get_session("codec_encode", self.codec_dir / "moss_audio_tokenizer_encode.onnx")
        self.codec_decode_sess = self._get_session("codec_decode", self.codec_dir / "moss_audio_tokenizer_decode_full.onnx")

    def encode_text(self, text: str) -> list[int]:
        return list(self.sp_model.encode(text, out_type=int))

    def load_and_resample_reference_audio(self, audio_path: str | Path) -> np.ndarray:
        data, sample_rate = sf.read(str(Path(audio_path).expanduser().resolve()), dtype="float32")
        if data.ndim == 1:
            data = data[None, :]  # (1, samples)
        else:
            data = data.T  # (channels, samples)
        
        target_sample_rate = int(self.codec_meta["codec_config"]["sample_rate"])
        target_channels = int(self.codec_meta["codec_config"]["channels"])

        if sample_rate != target_sample_rate:
            gcd = math.gcd(sample_rate, target_sample_rate)
            up = target_sample_rate // gcd
            down = sample_rate // gcd
            data = scipy.signal.resample_poly(data, up, down, axis=-1).astype(np.float32)

        current_channels = int(data.shape[0])
        if current_channels == 1 and target_channels > 1:
            data = np.repeat(data, target_channels, axis=0)
        elif current_channels > 1 and target_channels == 1:
            data = np.mean(data, axis=0, keepdims=True)

        return data[None, :, :].astype(np.float32, copy=False)  # (1, channels, samples)

    def encode_reference_audio(self, audio_path: str | Path) -> list[list[int]]:
        waveform = self.load_and_resample_reference_audio(audio_path)
        waveform_length = int(waveform.shape[-1])
        inputs = {
            "waveform": waveform,
            "waveform_length": np.array([waveform_length], dtype=np.int64),
        }
        outputs = self.codec_encode_sess.run(None, inputs)
        codes = outputs[0]  # shape: (1, num_codebooks, time_steps)
        # Convert to list of list of ints
        result: list[list[int]] = []
        for t in range(codes.shape[2]):
            frame_tokens = [int(codes[0, cb, t]) for cb in range(codes.shape[1])]
            result.append(frame_tokens)
        return result

    def synthesize(
        self,
        text: str,
        prompt_audio_path: str | Path,
        output_audio_path: str | Path | None = None,
        max_new_frames: int = 400,
    ) -> np.ndarray:
        """Synthesize speech audio from text and reference voice prompt."""
        # 1. Normalize text
        clean_text = normalize_text_for_speech(text)
        text_tokens = self.encode_text(clean_text)

        # 2. Encode reference audio prompt
        prompt_audio_codes = self.encode_reference_audio(prompt_audio_path)

        # 3. Prefill pass
        prompt_speech_len = len(prompt_audio_codes)
        text_len = len(text_tokens)

        # Flatten audio codes
        audio_tokens_3d = np.zeros((1, prompt_speech_len, 16), dtype=np.int32)
        for t, frame in enumerate(prompt_audio_codes):
            for cb, val in enumerate(frame[:16]):
                audio_tokens_3d[0, t, cb] = val

        text_tokens_2d = np.array([text_tokens], dtype=np.int32)

        prefill_inputs = {
            "text_tokens": text_tokens_2d,
            "prompt_speech_tokens": audio_tokens_3d,
        }

        prefill_outs = self.prefill_sess.run(None, prefill_inputs)
        # prefill_outs returns: first_audio_logits, kv_cache_tensors...
        first_token_logits = prefill_outs[0]  # shape: (1, vocab_size)
        kv_caches = prefill_outs[1:]

        # Fixed sampling / argmax for next token
        next_token = int(np.argmax(first_token_logits[0]))
        generated_frames: list[list[int]] = []

        # Local fixed sampling for 16 codebooks
        local_inputs = {
            "global_token": np.array([[next_token]], dtype=np.int32),
        }
        local_out = self.local_fixed_sess.run(None, local_inputs)[0]
        generated_frames.append([int(v) for v in local_out[0, 0, :16]])

        # 4. Autoregressive decode loop
        cur_token = next_token
        for step in range(max_new_frames):
            decode_inputs = {
                "input_token": np.array([[cur_token]], dtype=np.int32),
            }
            # Feed previous kv_caches
            input_names = [inp.name for inp in self.decode_step_sess.get_inputs()]
            for name, kv in zip(input_names[1:], kv_caches):
                decode_inputs[name] = kv

            decode_outs = self.decode_step_sess.run(None, decode_inputs)
            step_logits = decode_outs[0]
            kv_caches = decode_outs[1:]

            cur_token = int(np.argmax(step_logits[0]))
            # Stop token check if end of sequence
            if cur_token == self.manifest.get("eos_token_id", 2):
                break

            local_inputs = {"global_token": np.array([[cur_token]], dtype=np.int32)}
            local_out = self.local_fixed_sess.run(None, local_inputs)[0]
            generated_frames.append([int(v) for v in local_out[0, 0, :16]])

        # 5. Decode generated audio tokens with Cat Audio Decoder
        num_frames = len(generated_frames)
        code_tensor = np.zeros((1, 16, num_frames), dtype=np.int64)
        for t, frame in enumerate(generated_frames):
            for cb, val in enumerate(frame):
                code_tensor[0, cb, t] = val

        decoder_inputs = {
            "codes": code_tensor,
        }
        decoder_outs = self.codec_decode_sess.run(None, decoder_inputs)
        waveform = decoder_outs[0]  # shape: (1, 2, num_samples)

        # 6. Save to file if path given
        sample_rate = int(self.codec_meta["codec_config"]["sample_rate"])
        if output_audio_path:
            out_p = Path(output_audio_path).expanduser().resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            # soundfile expects (samples, channels)
            audio_data = waveform[0].T
            sf.write(str(out_p), audio_data, sample_rate)

        return waveform
