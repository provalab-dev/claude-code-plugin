#!/usr/bin/env python3
"""
provalab-auth — device-flow OAuth CLI for ProvaLab.io.

Purpose
-------
Sign in from a headless machine (SSH session, container, CI runner)
without needing a browser on the same host. The CLI drives the OAuth
2.0 Device Authorization Grant (RFC 8628) against identity-service:

    $ provalab-auth login
    Open this URL in any browser:
        https://auth.provalab.io/device?user_code=BCDF-GHJK
    Or visit https://auth.provalab.io/device and enter code BCDF-GHJK
    Waiting for approval...
    ✓ Signed in as you@example.com

The resulting access + refresh tokens are stored at
`~/.config/provalab/auth.json`. On every `provalab-auth token` call we
refresh silently when the access token is within 60s of expiry.

The ProvaLab Claude Code plugin's `.mcp.json` uses `headersHelper` to
shell out to `provalab-auth token`, so the plugin never touches the
tokens itself — one login on the VPS covers every subsequent MCP call
and every future session.

Zero-dependency by design (stdlib only) so `curl | python3` install
just works everywhere Python 3.9+ is available.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Optional


# ── Defaults ────────────────────────────────────────────────────────────
DEFAULT_ISSUER = os.environ.get("PROVALAB_AUTH_ISSUER", "https://auth-api.provalab.io")
DEFAULT_CLIENT_ID = os.environ.get("PROVALAB_AUTH_CLIENT_ID", "provalab-cli")
DEFAULT_SCOPE = os.environ.get(
    "PROVALAB_AUTH_SCOPE",
    "openid profile email tms:read tms:write tms:execute infra:read infra:write",
)
CONFIG_PATH = Path(
    os.environ.get("PROVALAB_AUTH_CONFIG")
    or (Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        / "provalab" / "auth.json")
)
REFRESH_LEEWAY_SECONDS = 60  # refresh when access token has less than this left

# Cloudflare's WAF blocks the default `Python-urllib/3.x` UA in front of
# our identity host; identify ourselves explicitly to get through.
USER_AGENT = "provalab-auth/1.0 (+https://plugins.provalab.io)"


# ── HTTP helper (stdlib) ────────────────────────────────────────────────

def _http_post_form(url: str, data: Dict[str, str], timeout: int = 15) -> Dict[str, Any]:
    """POST form-encoded body, always return parsed JSON.

    Raises urllib.error.HTTPError on non-2xx; for OAuth error responses
    (the RFC 8628 400/access_denied family, etc.) the body is still JSON
    and the caller catches HTTPError to read `.read()`.
    """
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json",
                 "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 15) -> Dict[str, Any]:
    merged = {"User-Agent": USER_AGENT}
    if headers:
        merged.update(headers)
    req = urllib.request.Request(url, headers=merged)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Config file ─────────────────────────────────────────────────────────

def _load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {}


def _save_config(data: Dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    # Never leave tokens world-readable.
    os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    tmp.replace(CONFIG_PATH)


def _clear_config() -> None:
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()


# ── OAuth flows ─────────────────────────────────────────────────────────

def _openid_config(issuer: str) -> Dict[str, Any]:
    return _http_get_json(f"{issuer.rstrip('/')}/.well-known/openid-configuration")


def _print_and_wait(user_code: str, verification_uri: str,
                    verification_uri_complete: str) -> None:
    """Rendered in the terminal — kept plain so it works over any TTY."""
    sys.stderr.write("\n")
    sys.stderr.write("  ┌────────────────────────────────────────────────┐\n")
    sys.stderr.write(f"  │  Enter code:   {user_code:<32}│\n")
    sys.stderr.write("  └────────────────────────────────────────────────┘\n\n")
    sys.stderr.write(f"  Open this URL in ANY browser (any device):\n")
    sys.stderr.write(f"     {verification_uri_complete}\n\n")
    sys.stderr.write(f"  Or visit {verification_uri} and enter the code above.\n\n")
    sys.stderr.write("  Waiting for approval")
    sys.stderr.flush()


def cmd_login(args: argparse.Namespace) -> int:
    issuer = args.issuer
    client_id = args.client_id
    scope = args.scope

    # Discover endpoints
    try:
        oidc = _openid_config(issuer)
    except Exception as e:
        print(f"error: could not fetch {issuer}/.well-known/openid-configuration: {e}", file=sys.stderr)
        return 2

    device_url = oidc.get("device_authorization_endpoint")
    token_url = oidc.get("token_endpoint")
    if not device_url or not token_url:
        print("error: identity server does not advertise device_authorization_endpoint", file=sys.stderr)
        print(f"       (server: {issuer}) — is it running the latest build?", file=sys.stderr)
        return 2

    # Step 1: request device + user codes
    try:
        auth = _http_post_form(device_url, {"client_id": client_id, "scope": scope})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"error: device_authorization returned {e.code}: {body}", file=sys.stderr)
        return 2

    device_code = auth["device_code"]
    interval = int(auth.get("interval", 5))
    expires_in = int(auth.get("expires_in", 600))
    deadline = time.time() + expires_in

    _print_and_wait(auth["user_code"], auth["verification_uri"], auth["verification_uri_complete"])

    # Step 2: poll for token
    while time.time() < deadline:
        time.sleep(interval)
        sys.stderr.write("."); sys.stderr.flush()
        try:
            tokens = _http_post_form(token_url, {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": client_id,
            })
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(body).get("detail", body)
            except Exception:
                detail = body
            if detail == "authorization_pending":
                continue
            if detail == "slow_down":
                interval += 5
                continue
            if detail == "access_denied":
                sys.stderr.write("\n\n  ✗ Denied by user.\n")
                return 4
            if detail == "expired_token":
                sys.stderr.write("\n\n  ✗ Code expired before approval. Run login again.\n")
                return 4
            sys.stderr.write(f"\n\n  ✗ Token exchange failed ({e.code}): {detail}\n")
            return 4
        # Success
        _persist_tokens(tokens, issuer=issuer, client_id=client_id, scope=scope)
        _print_success(tokens)
        return 0

    sys.stderr.write("\n\n  ✗ Timed out waiting for approval.\n")
    return 4


def _persist_tokens(tokens: Dict[str, Any], *, issuer: str, client_id: str, scope: str) -> None:
    now = int(time.time())
    data = {
        "issuer": issuer,
        "client_id": client_id,
        "scope": scope,
        "access_token": tokens["access_token"],
        "expires_at": now + int(tokens.get("expires_in", 3600)),
        "refresh_token": tokens.get("refresh_token"),
        "token_type": tokens.get("token_type", "Bearer"),
        "obtained_at": now,
    }
    _save_config(data)


def _print_success(tokens: Dict[str, Any]) -> None:
    sys.stderr.write("\n\n")
    # Try to extract identity from the JWT for a friendly message.
    email = _try_decode_email(tokens.get("access_token", ""))
    if email:
        sys.stderr.write(f"  ✓ Signed in as {email}\n")
    else:
        sys.stderr.write(f"  ✓ Signed in.\n")
    sys.stderr.write(f"    Token cached at {CONFIG_PATH}\n")


def _try_decode_email(jwt_token: str) -> Optional[str]:
    """Best-effort JWT payload parse. Doesn't verify — just for the greeting."""
    try:
        import base64
        parts = jwt_token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("email") or payload.get("preferred_username") or payload.get("sub")
    except Exception:
        return None


def _refresh_if_needed(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return a config dict guaranteed to have a non-expired access_token."""
    now = int(time.time())
    if cfg.get("expires_at", 0) - REFRESH_LEEWAY_SECONDS > now:
        return cfg
    refresh_token = cfg.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("token expired and no refresh_token available; run `provalab-auth login`")
    issuer = cfg.get("issuer", DEFAULT_ISSUER)
    client_id = cfg.get("client_id", DEFAULT_CLIENT_ID)
    token_url = _openid_config(issuer)["token_endpoint"]
    try:
        tokens = _http_post_form(token_url, {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        })
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"refresh failed ({e.code}); run `provalab-auth login`") from e
    _persist_tokens(tokens, issuer=issuer, client_id=client_id, scope=cfg.get("scope", ""))
    return _load_config()


def cmd_token(args: argparse.Namespace) -> int:
    """Print a fresh access token to stdout. Refreshes silently if needed."""
    cfg = _load_config()
    if not cfg.get("access_token"):
        print("error: not signed in. Run `provalab-auth login`.", file=sys.stderr)
        return 3
    try:
        cfg = _refresh_if_needed(cfg)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    print(cfg["access_token"])
    return 0


def cmd_mcp_header(args: argparse.Namespace) -> int:
    """Print 'Authorization: Bearer <token>\\r\\n' for use as .mcp.json headersHelper.

    One invocation replaces the sh -c 'command -v provalab-auth / token / printf'
    gymnastics in .mcp.json — and works unchanged on Windows where sh isn't
    guaranteed. Non-zero exit + stderr diagnostic on any auth problem.
    """
    cfg = _load_config()
    if not cfg.get("access_token"):
        sys.stderr.write("provalab-auth: not signed in — run `provalab-auth login`\n")
        return 3
    try:
        cfg = _refresh_if_needed(cfg)
    except Exception as e:
        sys.stderr.write(f"provalab-auth: {e}\n")
        return 3
    sys.stdout.write(f"Authorization: Bearer {cfg['access_token']}\r\n")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    cfg = _load_config()
    if not cfg.get("access_token"):
        print("Not signed in. Run `provalab-auth login`.")
        return 1
    now = int(time.time())
    exp = cfg.get("expires_at", 0)
    remaining = exp - now
    email = _try_decode_email(cfg["access_token"]) or "unknown"
    print(f"Signed in as:   {email}")
    print(f"Config:         {CONFIG_PATH}")
    print(f"Issuer:         {cfg.get('issuer', '?')}")
    if remaining > 0:
        mins = remaining // 60
        print(f"Access token:   valid for {mins}m")
    else:
        print(f"Access token:   expired (will refresh on next `token` call)")
    print(f"Refresh token:  {'present' if cfg.get('refresh_token') else 'absent'}")
    return 0


def cmd_logout(args: argparse.Namespace) -> int:
    _clear_config()
    print(f"Cleared {CONFIG_PATH}.")
    return 0


# ── Argparse ────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="provalab-auth",
        description="Device-flow OAuth CLI for ProvaLab.io.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="Start device flow, print URL + code, wait for approval.")
    login.add_argument("--issuer", default=DEFAULT_ISSUER,
                       help=f"OAuth issuer (default: {DEFAULT_ISSUER})")
    login.add_argument("--client-id", default=DEFAULT_CLIENT_ID,
                       help=f"OAuth client_id (default: {DEFAULT_CLIENT_ID})")
    login.add_argument("--scope", default=DEFAULT_SCOPE,
                       help="Space-separated OAuth scopes")
    login.set_defaults(func=cmd_login)

    tok = sub.add_parser("token", help="Print a fresh access token to stdout (refreshes if needed).")
    tok.set_defaults(func=cmd_token)

    mh = sub.add_parser("mcp-header",
                        help="Print 'Authorization: Bearer <token>\\r\\n' for .mcp.json headersHelper.")
    mh.set_defaults(func=cmd_mcp_header)

    status = sub.add_parser("status", help="Show current sign-in state.")
    status.set_defaults(func=cmd_status)

    lo = sub.add_parser("logout", help="Delete the local token cache.")
    lo.set_defaults(func=cmd_logout)

    return p


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
