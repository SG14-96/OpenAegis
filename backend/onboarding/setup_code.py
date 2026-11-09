"""
One-time setup code guarding first-admin creation.

A brand-new install has no users, so POST /api/v1/setup/admin can't require
a login. Instead, the server prints a short code to its own log on boot and
the setup wizard asks for it — proving the person creating the admin can
see the server's console (docker logs), not just reach it on the network.

The code lives only in memory: it's regenerated on every boot while no
users exist, rotated after repeated wrong guesses, and discarded once the
first admin is created.
"""
from __future__ import annotations

import logging
import secrets
import threading

logger = logging.getLogger(__name__)

# No 0/O, 1/I/L — the code is read off a terminal and typed by hand.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_LENGTH = 8
# 31^8 ≈ 8.5e11 codes; rotating after this many misses makes guessing hopeless.
MAX_FAILED_ATTEMPTS = 5


def _normalize(code: str) -> str:
    return "".join(ch for ch in code.upper() if ch.isalnum())


class SetupCode:
    def __init__(self) -> None:
        self._code: str | None = None
        self._failures = 0
        self._lock = threading.Lock()

    @property
    def active(self) -> bool:
        return self._code is not None

    def issue(self) -> None:
        """Generate a fresh code and print it to the server log."""
        with self._lock:
            self._rotate()

    def verify(self, candidate: str) -> bool:
        """
        Check a submitted code. Rotates to a new code (printed to the log)
        after MAX_FAILED_ATTEMPTS wrong guesses in a row.
        """
        with self._lock:
            if self._code is None:
                return False
            if secrets.compare_digest(_normalize(candidate), self._code):
                self._failures = 0
                return True
            self._failures += 1
            if self._failures >= MAX_FAILED_ATTEMPTS:
                logger.warning("Too many incorrect setup codes; issuing a new one.")
                self._rotate()
            return False

    def consume(self) -> None:
        """Discard the code once the first admin exists."""
        with self._lock:
            self._code = None
            self._failures = 0

    def _rotate(self) -> None:
        self._code = "".join(secrets.choice(_ALPHABET) for _ in range(_LENGTH))
        self._failures = 0
        display = f"{self._code[:4]}-{self._code[4:]}"
        banner = "=" * 60
        logger.warning(
            "\n%s\n  OpenAegis first-run setup\n  No users exist yet. Open the web UI and enter this\n"
            "  setup code to create the administrator account:\n\n      %s\n%s",
            banner, display, banner,
        )
