import os
import sys
import json
import io
import pytest

# Ensure backend dir is importable
TEST_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if TEST_BACKEND_DIR not in sys.path:
    sys.path.insert(0, TEST_BACKEND_DIR)

import openai

from main import call_openai_generate


class FakeResp:
    def __init__(self, content: str):
        class Message:
            def __init__(self, c):
                self.content = c

        class Choice:
            def __init__(self, c):
                self.message = Message(c)

        self.choices = [Choice(content)]


def test_openai_happy_path(monkeypatch):
    # valid JSON response
    valid = [
        {"question": "Q1", "options": ["A","B","C","D"], "answer_index": 0},
        {"question": "Q2", "options": ["A","B","C","D"], "answer_index": 1},
    ]
    def fake_create(*args, **kwargs):
        return FakeResp(json.dumps(valid))

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)
    os.environ["OPENAI_API_KEY"] = "test"
    out = call_openai_generate("some text", 2)
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["question"] == "Q1"


def test_openai_bad_json_then_recovery(monkeypatch):
    # first response invalid, second is valid
    valid = [
        {"question": "R1", "options": ["A","B","C","D"], "answer_index": 2},
    ]
    responses = iter(["not a json", json.dumps(valid)])

    def fake_create(*args, **kwargs):
        try:
            c = next(responses)
        except StopIteration:
            c = json.dumps(valid)
        return FakeResp(c)

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)
    os.environ["OPENAI_API_KEY"] = "test"
    out = call_openai_generate("some text", 1)
    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0]["question"] == "R1"


def test_openai_all_fail_fallback(monkeypatch):
    # always return unparsable content -> should fallback to dummy generator
    def fake_create(*args, **kwargs):
        return FakeResp("<html>error</html>")

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)
    os.environ["OPENAI_API_KEY"] = "test"
    out = call_openai_generate("short doc sentence.", 2)
    assert isinstance(out, list)
    assert len(out) == 2


def test_openai_invalid_item_then_recovery(monkeypatch):
    # first response contains an item with wrong number of options (3), second response is valid
    invalid = [
        {"question": "Bad", "options": ["A", "B", "C"], "answer_index": 0}
    ]
    valid = [
        {"question": "Fixed", "options": ["A", "B", "C", "D"], "answer_index": 1}
    ]
    responses = iter([json.dumps(invalid), json.dumps(valid)])

    def fake_create(*args, **kwargs):
        try:
            c = next(responses)
        except StopIteration:
            c = json.dumps(valid)
        return FakeResp(c)

    monkeypatch.setattr(openai.ChatCompletion, "create", fake_create)
    os.environ["OPENAI_API_KEY"] = "test"
    out = call_openai_generate("doc text", 1)
    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0]["question"] == "Fixed"
