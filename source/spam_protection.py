"""
Spam protection utilities for Forms Builder.
"""
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SpamResult:
    """Result of spam check."""
    is_spam: bool
    honeypot_triggered: bool
    reasons: List[str]


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}

    def check(self, identifier: str) -> bool:
        """Check if request is allowed. Returns True if allowed, False if rate limited."""
        now = time.time()
        if identifier not in self._requests:
            self._requests[identifier] = []

        # Clean old requests outside the window
        self._requests[identifier] = [
            req_time for req_time in self._requests[identifier]
            if now - req_time < self.window_seconds
        ]

        if len(self._requests[identifier]) >= self.max_requests:
            return False

        self._requests[identifier].append(now)
        return True

    def reset(self, identifier: str) -> None:
        """Reset rate limit for an identifier."""
        if identifier in self._requests:
            del self._requests[identifier]


# Common spam patterns
SPAM_PATTERNS = [
    r"(?i)\b(viagra|cialis|levitra)\b",
    r"(?i)\b(casino|poker|lottery|jackpot)\b",
    r"(?i)\b(weight.loss|diet.pills|fat.burner)\b",
    r"(?i)\b(make.money|earn.cash|work.from.home)\b",
    r"(?i)\b(bitcoin|crypto|investment|trading)\b",
    r"(?i)\b(loan|credit|debt.relief|mortgage)\b",
    r"(?i)\b(insurance|quote|policy)\b",
    r"(?i)\b(free|win|winner|congratulations)\b",
    r"(?i)\b(click.here|visit.site|check.out)\b",
    r"(?i)https?://[^\s]+",  # URLs in text fields
]

# Suspicious field names that might indicate bot behavior
SUSPICIOUS_FIELD_NAMES = [
    "url", "link", "website", "homepage", "site", "blog",
    "http", "https", "ftp",
]

# Common bot user agents (partial matches)
BOT_USER_AGENTS = [
    "bot", "crawler", "spider", "scraper", "curl", "wget",
    "python-requests", "go-http", "java/", "perl", "ruby",
    "phantomjs", "headless", "selenium", "webdriver",
]


def check_spam(
    data: Dict[str, any],
    honeypot_field: str = "website",
    honeypot_enabled: bool = True,
    user_agent: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> SpamResult:
    """
    Check form submission for spam indicators.

    Args:
        data: Form field values
        honeypot_field: Name of the honeypot field
        honeypot_enabled: Whether honeypot check is enabled
        user_agent: Client user agent string
        client_ip: Client IP address

    Returns:
        SpamResult with is_spam flag and reasons
    """
    reasons = []
    honeypot_triggered = False

    # 1. Honeypot field check (hidden field that humans don't fill)
    if honeypot_enabled and honeypot_field in data:
        honeypot_value = data[honeypot_field]
        if honeypot_value and str(honeypot_value).strip():
            honeypot_triggered = True
            reasons.append(f"Honeypot field '{honeypot_field}' was filled")

    # 2. URL detection in form values
    for field_name, value in data.items():
        if value is None:
            continue
        value_str = str(value)
        if field_name != honeypot_field:  # Don't check honeypot field
            for pattern in SPAM_PATTERNS:
                if re.search(pattern, value_str):
                    reasons.append(f"Spam pattern detected in field '{field_name}'")
                    break

    # 3. Suspicious field names (bots often fill hidden/honeypot fields)
    for field_name in data.keys():
        if field_name.lower() in SUSPICIOUS_FIELD_NAMES and field_name != honeypot_field:
            value = data[field_name]
            if value and str(value).strip():
                reasons.append(f"Suspicious field '{field_name}' was filled")

    # 4. User agent check
    if user_agent:
        ua_lower = user_agent.lower()
        for bot_ua in BOT_USER_AGENTS:
            if bot_ua in ua_lower:
                reasons.append(f"Bot-like user agent detected: {bot_ua}")
                break

    # 5. Too many fields filled (possible bot filling all fields)
    filled_fields = sum(1 for v in data.values() if v and str(v).strip())
    if filled_fields > 20:  # Arbitrary threshold
        reasons.append(f"Unusually high number of filled fields: {filled_fields}")

    # 6. Very fast submission (if we had timing, but we don't in this simple version)
    # This would require a timestamp field in the form

    is_spam = len(reasons) > 0

    return SpamResult(
        is_spam=is_spam,
        honeypot_triggered=honeypot_triggered,
        reasons=reasons,
    )


def generate_honeypot_html(field_name: str = "website") -> str:
    """Generate HTML for honeypot field (hidden from humans via CSS)."""
    return f'''
<div class="forms-builder-honeypot" style="display: none; position: absolute; left: -9999px; visibility: hidden;" aria-hidden="true">
    <label for="{field_name}">Website (leave blank)</label>
    <input type="text" id="{field_name}" name="{field_name}" tabindex="-1" autocomplete="off" />
</div>
'''