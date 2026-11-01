import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def data_folder(tmp_path, monkeypatch):
    """Every test gets its own empty save folder."""
    monkeypatch.setenv("TYPESTRIKER_DATA", str(tmp_path))
    return tmp_path


@pytest.fixture(scope="session")
def shared_app(tmp_path_factory):
    os.environ.setdefault("TYPESTRIKER_DATA", str(tmp_path_factory.mktemp("app")))
    from typestriker.app import App
    return App(fullscreen=False)


@pytest.fixture
def app(shared_app):
    shared_app.running = True
    return shared_app
