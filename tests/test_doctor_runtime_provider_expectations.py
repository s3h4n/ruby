from __future__ import annotations

import copy
import json
from pathlib import Path

from ruby.config.settings import DEFAULT_CONFIG
from ruby.setup import doctor


def _write_config(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _patch_doctor_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(doctor, "check_ollama_tags", lambda _url: (True, "connected"))
    monkeypatch.setattr(doctor, "_check_whisper_cli", lambda _cli: (True, "runnable"))
    monkeypatch.setattr(doctor.importlib, "import_module", lambda _name: object())

    class _FakeRecorder:
        def __init__(self, sample_rate: int) -> None:
            self.sample_rate = sample_rate

        def check_microphone_access(self) -> None:
            return None

    monkeypatch.setattr(doctor, "AudioRecorder", _FakeRecorder)


def test_doctor_reports_missing_runtime_directories(tmp_path: Path, monkeypatch) -> None:
    _patch_doctor_dependencies(monkeypatch)

    config_path = tmp_path / "config.json"
    payload = copy.deepcopy(DEFAULT_CONFIG)
    payload["providers"]["stt"]["whisper_cli"] = "whisper.cpp/build/bin/whisper-cli"
    payload["providers"]["stt"]["model"] = "whisper.cpp/models/ggml-base.en.bin"
    _write_config(config_path, payload)

    report = doctor.run_doctor(config_path)
    assert "FAIL runtime-dir" in report
    assert "create runtime directories" in report


def test_doctor_reports_openrouter_key_requirement(tmp_path: Path, monkeypatch) -> None:
    _patch_doctor_dependencies(monkeypatch)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    config_path = tmp_path / "config.json"
    payload = copy.deepcopy(DEFAULT_CONFIG)
    payload["providers"]["llm"]["provider"] = "openrouter"
    _write_config(config_path, payload)

    report = doctor.run_doctor(config_path)
    assert "FAIL openrouter-api-key" in report
    assert "OPENROUTER_API_KEY" in report
