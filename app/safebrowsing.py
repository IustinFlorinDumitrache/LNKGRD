import logging

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


class UrlChecker:
    def is_safe(self, url: str) -> bool:
        key = get_settings().safe_browsing_api_key
        if not key:
            log.warning("SAFE_BROWSING_API_KEY not set - skipping URL check")
            return True

        body = {
            "client": {"clientId": "linkguard", "clientVersion": "0.1.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        try:
            resp = httpx.post(ENDPOINT, params={"key": key}, json=body, timeout=5.0)
            resp.raise_for_status()
        except httpx.HTTPError:
            log.exception("Safe Browsing check failed - allowing URL")
            return True

        #
        return not resp.json().get("matches")


def get_url_checker() -> UrlChecker:
    return UrlChecker()