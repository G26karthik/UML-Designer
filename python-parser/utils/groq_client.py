import json
import logging
import os
import time
import threading
import hashlib
from collections import OrderedDict
from typing import Any, Dict, Optional

import requests

__all__ = [
    "GroqClient",
    "GroqClientError",
    "GroqClientDisabledError",
]


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


class GroqClientError(Exception):
    """Base exception for Groq client interactions."""


class GroqClientDisabledError(GroqClientError):
    """Raised when the Groq client is disabled via configuration or failures."""


class GroqClient:
    """Thin wrapper around the Groq API with retry, caching, and circuit breaking."""

    def __init__(
        self,
        *,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)

        self.enabled = _is_truthy(os.getenv("GROQ_ENABLED", "true"))
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = os.getenv(
            "GROQ_API_URL",
            "https://api.groq.com/openai/v1/chat/completions",
        )
        # Allow legacy GROQ_TIMEOUT env while preferring *_SECONDS
        timeout_env = (
            os.getenv("GROQ_TIMEOUT_SECONDS")
            or os.getenv("GROQ_TIMEOUT")
            or "120"
        )
        self.timeout = max(float(timeout_env), 1.0)
        self.max_retries = max(int(os.getenv("GROQ_MAX_RETRIES", "2")), 0)
        self.backoff_factor = max(float(os.getenv("GROQ_RETRY_BACKOFF", "0.5")), 0.0)

        self.failure_threshold = max(int(os.getenv("GROQ_DISABLE_AFTER_FAILURES", "5")), 0)
        self.cooldown_seconds = max(int(os.getenv("GROQ_DISABLE_COOLDOWN", "300")), 0)

        self.cache_enabled = _is_truthy(os.getenv("GROQ_CACHE_ENABLED", "false"))
        self.cache_ttl = max(int(os.getenv("GROQ_CACHE_TTL", "900")), 1)
        self.cache_max_items = max(int(os.getenv("GROQ_CACHE_MAX_ITEMS", "50")), 1)

        self.session = session or requests.Session()
        self._cache: "OrderedDict[str, tuple[float, Dict[str, Any]]]" = OrderedDict()
        self._lock = threading.Lock()
        self._failure_count = 0
        self._disabled_until = 0.0

        if not self.api_key:
            self.enabled = False
            self.logger.debug("Groq client disabled because GROQ_API_KEY is missing")

        if not self.enabled:
            self.logger.info("Groq client initialised in disabled state")

    @property
    def is_available(self) -> bool:
        if not self.enabled:
            return False
        if not self.api_key:
            return False
        if self._disabled_until and time.time() < self._disabled_until:
            return False
        return True

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.cache_enabled:
            return None
        with self._lock:
            item = self._cache.get(key)
            if not item:
                return None
            expires_at, data = item
            if expires_at < time.time():
                self._cache.pop(key, None)
                return None
            self._cache.move_to_end(key)
            return data

    def _cache_set(self, key: str, data: Dict[str, Any]) -> None:
        if not self.cache_enabled:
            return
        with self._lock:
            expires_at = time.time() + self.cache_ttl
            self._cache[key] = (expires_at, data)
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_max_items:
                self._cache.popitem(last=False)

    @staticmethod
    def _hash_payload(payload: Dict[str, Any]) -> str:
        try:
            normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        except TypeError:
            normalized = repr(payload)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            raise GroqClientDisabledError("Groq client disabled by configuration")
        if not self.api_key:
            raise GroqClientDisabledError("Groq client disabled because GROQ_API_KEY is missing")
        if self._disabled_until and time.time() < self._disabled_until:
            raise GroqClientDisabledError("Groq client temporarily disabled after repeated failures")

        cache_key = self._hash_payload(payload)
        cached = self._cache_get(cache_key)
        if cached is not None:
            self.logger.debug("Returning cached Groq response for key %s", cache_key[:8])
            return cached

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        last_error: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                self._failure_count = 0
                self._disabled_until = 0.0
                self._cache_set(cache_key, data)
                return data
            except requests.Timeout as exc:
                last_error = exc
                self.logger.warning(
                    "Groq request timed out (attempt %s/%s)",
                    attempt + 1,
                    self.max_retries + 1,
                )
            except requests.HTTPError as exc:
                last_error = exc
                status_code = exc.response.status_code if exc.response else None
                if status_code and status_code < 500:
                    self.logger.error(
                        "Groq request failed with non-retriable status %s", status_code
                    )
                    break
                self.logger.warning(
                    "Groq request failed with HTTP %s (attempt %s/%s)",
                    status_code,
                    attempt + 1,
                    self.max_retries + 1,
                )
            except requests.RequestException as exc:
                last_error = exc
                self.logger.warning(
                    "Groq request error (attempt %s/%s): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )
            except ValueError as exc:
                last_error = exc
                self.logger.error("Groq response JSON decoding failed: %s", exc)
                break

            if attempt < self.max_retries and self.backoff_factor > 0:
                sleep_for = self.backoff_factor * (2 ** attempt)
                time.sleep(sleep_for)

        self._failure_count += 1
        if self.failure_threshold and self._failure_count >= self.failure_threshold:
            self._disabled_until = time.time() + self.cooldown_seconds
            self.logger.error(
                "Groq client disabled for %s seconds after %s consecutive failures",
                self.cooldown_seconds,
                self.failure_threshold,
            )
            self._failure_count = 0
            raise GroqClientDisabledError(
                "Groq client temporarily disabled after repeated failures"
            )

        message = str(last_error) if last_error else "Unknown Groq request failure"
        raise GroqClientError(message)