from pathlib import Path


def test_windows_launchers_use_cmd_safe_ascii_and_crlf():
    for filename in ("BelgeIz.cmd", "YerelModelKur.cmd"):
        data = Path(filename).read_bytes()
        assert data.isascii(), f"{filename} yalnız ASCII komutlar içermeli"
        assert not data.startswith(b"\xef\xbb\xbf"), f"{filename} BOM içermemeli"
        assert data.count(b"\n") == data.count(b"\r\n"), (
            f"{filename} yalnız Windows CRLF satır sonu kullanmalı"
        )

    primary = Path("BelgeIz.cmd").read_text(encoding="ascii")
    assert "%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" in primary
    assert "-ExecutionPolicy Bypass" in primary


def test_local_model_launcher_offers_every_ui_model():
    launcher = Path("YerelModelKur.cmd").read_text(encoding="ascii")

    assert "choice /C 1234" in launcher
    for model in ("qwen3:1.7b", "qwen3:4b-instruct", "qwen3:8b"):
        assert f"call :pull_one {model}" in launcher
