from __future__ import annotations

from ruby.core import schemas


def test_tools_modules_expose_expected_classes() -> None:
    from ruby.tools.files import FileTools
    from ruby.tools.system import SystemTools

    assert FileTools.__name__ == "FileTools"
    assert SystemTools.__name__ == "SystemTools"


def test_kokoro_provider_module_path_exists() -> None:
    from ruby.providers.tts.kokoro import KokoroTTSProvider

    assert KokoroTTSProvider.__name__ == "KokoroTTSProvider"


def test_core_schemas_export_tool_result() -> None:
    assert hasattr(schemas, "ToolResult")
