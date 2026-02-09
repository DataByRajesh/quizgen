"""
Lightweight shim for the OpenAI client so tests and local runs don't fail if
the real `openai` package isn't installed in the interpreter used by pytest.

This shim defines the minimal attributes used by the code (ChatCompletion.create
and api_key). In production, the real `openai` package will shadow this if
installed in site-packages; when running tests we monkeypatch ChatCompletion.create
so this shim is sufficient.
"""
api_key = None


class ChatCompletion:
    @staticmethod
    def create(*args, **kwargs):
        raise RuntimeError("openai package not available; tests should monkeypatch this method")


__all__ = ["api_key", "ChatCompletion"]
