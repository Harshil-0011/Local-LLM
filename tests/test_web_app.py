import importlib

from fastapi.testclient import TestClient


def _load_web_app(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCAL_PERPLEX_HISTORY_DIR", str(tmp_path / "history"))
    monkeypatch.setenv("LOCAL_PERPLEX_DOCUMENT_DIR", str(tmp_path / "documents"))
    monkeypatch.setenv("LOCAL_PERPLEX_GRAPH_DIR", str(tmp_path / "graph"))
    module = importlib.import_module("local_perplex.ui.web.app")
    module = importlib.reload(module)
    module.engine.ollama_online = False
    module.engine.available_models = []
    module.engine.refresh_status = lambda: {
        "ollama_online": False,
        "available_models": [],
        "current_model": module.engine.model,
    }
    return module


def test_index_graph_and_status_routes(monkeypatch, tmp_path):
    web_app = _load_web_app(monkeypatch, tmp_path)
    client = TestClient(web_app.app)

    assert client.get("/").status_code == 200
    assert client.get("/graph").status_code == 200

    status = client.get("/api/status")
    assert status.status_code == 200
    assert status.json()["ollama_online"] is False
    assert "graph" in status.json()


def test_ask_without_mode_returns_offline_page_not_422(monkeypatch, tmp_path):
    web_app = _load_web_app(monkeypatch, tmp_path)
    client = TestClient(web_app.app)

    response = client.post("/ask", data={"question": "hello"})

    assert response.status_code == 200
    assert "Ollama is not running" in response.text
