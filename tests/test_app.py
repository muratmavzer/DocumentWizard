from pathlib import Path

from streamlit.testing.v1 import AppTest

from belgeiz.models import DocumentResult, SourceChunk
from belgeiz.service import BelgeIzService


def test_remove_button_drops_document_and_returns_to_empty_state():
    service = BelgeIzService()
    chunk = SourceChunk("src-demo", "yanlis-belge.pdf", 1, "Deneme metni")
    service.documents = [DocumentResult("yanlis-belge.pdf", 1, [chunk])]
    service.chunks = [chunk]

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=10)
    app.session_state["service"] = service
    app.session_state["messages"] = []
    app.session_state["ollama_check"] = None
    app.session_state["uploader_version"] = 0
    app.run()

    remove = next(button for button in app.button if button.label == "Çıkar")
    remove.click().run()

    assert not app.exception
    assert app.session_state["service"] is None
    assert all(button.label != "Çıkar" for button in app.button)
