"""provalab-auth hardening (#233) and email display (#237).

Run: python3 -m pytest tests/ -q   (stdlib + pytest only; no network)
"""
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SRC = Path(__file__).resolve().parents[1] / "plugins" / "provalab" / "bin" / "provalab_auth.py"


@pytest.fixture
def pa(tmp_path, monkeypatch):
    monkeypatch.setenv("PROVALAB_AUTH_CONFIG", str(tmp_path / "cfg" / "auth.json"))
    spec = importlib.util.spec_from_file_location("provalab_auth_under_test", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _signed_in(pa, **extra):
    pa._save_config({"issuer": "https://id.test", "client_id": "provalab-cli",
                     "access_token": "h.eyJzdWIiOiJ1LTEifQ.s", "refresh_token": "r-1",
                     "expires_at": 9_999_999_999, **extra})


def test_token_file_is_never_world_readable_even_while_being_written(pa, monkeypatch):
    seen = []
    real_write = os.write

    def spy(fd, data):
        seen.append(stat.S_IMODE(os.fstat(fd).st_mode))
        return real_write(fd, data)

    monkeypatch.setattr(os, "write", spy)
    _signed_in(pa)
    assert seen and all(m & 0o077 == 0 for m in seen), [oct(m) for m in seen]
    assert stat.S_IMODE(pa.CONFIG_PATH.stat().st_mode) == 0o600
    assert stat.S_IMODE(pa.CONFIG_PATH.parent.stat().st_mode) & 0o077 == 0


def test_logout_when_not_signed_in_says_so(pa, capsys):
    assert pa.cmd_logout(SimpleNamespace()) == 0
    out = capsys.readouterr().out
    assert "not signed in" in out.lower()
    assert "cleared" not in out.lower()


def test_logout_revokes_refresh_token_then_removes_file(pa, monkeypatch, capsys):
    _signed_in(pa)
    calls = []
    monkeypatch.setattr(pa, "_openid_config", lambda issuer: {"revocation_endpoint": "https://id.test/revoke"})
    monkeypatch.setattr(pa, "_http_post_form", lambda url, data, timeout=15: calls.append((url, data)) or {})
    assert pa.cmd_logout(SimpleNamespace()) == 0
    assert calls == [("https://id.test/revoke", {"token": "r-1", "token_type_hint": "refresh_token",
                                                   "client_id": "provalab-cli"})]
    assert not pa.CONFIG_PATH.exists()
    assert "signed out" in capsys.readouterr().out.lower()


def test_logout_still_removes_local_tokens_if_revocation_fails(pa, monkeypatch, capsys):
    _signed_in(pa)
    monkeypatch.setattr(pa, "_openid_config", lambda issuer: {"revocation_endpoint": "https://id.test/revoke"})

    def boom(*a, **k):
        raise OSError("offline")

    monkeypatch.setattr(pa, "_http_post_form", boom)
    assert pa.cmd_logout(SimpleNamespace()) == 0
    assert not pa.CONFIG_PATH.exists()
    assert "could not" in capsys.readouterr().out.lower()


def test_status_shows_email_from_userinfo(pa, monkeypatch, capsys):
    _signed_in(pa)
    monkeypatch.setattr(pa, "_openid_config", lambda issuer: {"userinfo_endpoint": "https://id.test/userinfo"})
    monkeypatch.setattr(pa, "_http_get_json", lambda url, headers=None, timeout=15: {"sub": "u-1", "email": "qa@example.com"})
    assert pa.cmd_status(SimpleNamespace()) == 0
    out = capsys.readouterr().out
    assert "qa@example.com" in out
    assert "u-1" not in out


def test_status_falls_back_quietly_when_userinfo_unavailable(pa, monkeypatch, capsys):
    _signed_in(pa)

    def boom(*a, **k):
        raise OSError("offline")

    monkeypatch.setattr(pa, "_openid_config", boom)
    assert pa.cmd_status(SimpleNamespace()) == 0
    assert "Signed in" in capsys.readouterr().out
