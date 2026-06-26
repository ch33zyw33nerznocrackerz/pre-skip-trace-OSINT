from __future__ import annotations

import json
import re
from pathlib import Path

URL_RE = re.compile(r"https?://[^\s\]\)\"'<>]+", re.IGNORECASE)

SOCIAL_HOST_HINTS = (
    "twitter.com",
    "x.com",
    "instagram.com",
    "facebook.com",
    "linkedin.com",
    "tiktok.com",
    "youtube.com",
    "reddit.com",
    "pinterest.com",
    "snapchat.com",
    "github.com",
    "gitlab.com",
    "medium.com",
    "twitch.tv",
    "threads.net",
    "mastodon",
    "vk.com",
    "telegram",
    "t.me",
    "discord",
    "spotify.com",
    "soundcloud.com",
    "flickr.com",
    "vimeo.com",
    "patreon.com",
    "cash.app",
    "venmo.com",
    "paypal.me",
    "about.me",
    "gravatar.com",
    "keybase.io",
    "behance.net",
    "dribbble.com",
    "dev.to",
    "hackernews",
    "news.ycombinator.com",
)


def _clean_url(url: str) -> str:
    return url.rstrip(".,;)")


def extract_urls(text: str) -> set[str]:
    if not text:
        return set()
    return {_clean_url(u) for u in URL_RE.findall(text)}


def extract_profile_urls(text: str, *, social_only: bool = False) -> set[str]:
    urls = extract_urls(text)
    if not social_only:
        return urls
    out: set[str] = set()
    for url in urls:
        lower = url.lower()
        if any(hint in lower for hint in SOCIAL_HOST_HINTS):
            out.add(url)
    return out


def parse_tool_output(tool_id: str, stdout: str, output_dir: str | None = None) -> set[str]:
    """Extract profile URLs from FOSS social tool output."""
    profiles = extract_profile_urls(stdout, social_only=True)

    if output_dir:
        out_path = Path(output_dir)
        if out_path.is_dir():
            for json_file in out_path.glob("**/*.json"):
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8", errors="ignore"))
                    profiles.update(_urls_from_json(data))
                except (json.JSONDecodeError, OSError):
                    continue
            for txt in out_path.glob("**/*.txt"):
                try:
                    profiles.update(extract_profile_urls(txt.read_text(encoding="utf-8", errors="ignore")))
                except OSError:
                    continue

    if tool_id == "sherlock":
        for line in stdout.splitlines():
            if "[+]" in line and "http" in line:
                profiles.update(extract_profile_urls(line, social_only=True))

    return profiles


def _urls_from_json(data: object) -> set[str]:
    urls: set[str] = set()
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, str) and val.startswith("http"):
                urls.add(_clean_url(val))
            elif isinstance(val, dict) and "url" in val and isinstance(val["url"], str):
                urls.add(_clean_url(val["url"]))
            else:
                urls.update(_urls_from_json(val))
    elif isinstance(data, list):
        for item in data:
            urls.update(_urls_from_json(item))
    return urls
