from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from service_osint.foss import FossTarget, check_tool_available, get_foss_tool, run_foss_tool
from service_osint.pipeline.types import PipelineConfig
from service_osint.social.parse import parse_tool_output
from service_osint.social.username import guess_usernames

# Fast pipeline subset; maigret is slower — included in full scans.
FAST_SOCIAL_TOOLS: list[tuple[str, str]] = [
    ("username", "sherlock"),
    ("username", "socialscan-username"),
    ("email", "holehe"),
    ("email", "socialscan-email"),
    ("phone", "ignorant"),
]

FULL_SOCIAL_TOOLS: list[tuple[str, str]] = [
    *FAST_SOCIAL_TOOLS,
    ("username", "maigret"),
]


@dataclass
class SocialPaiResult:
    profiles: set[str] = field(default_factory=set)
    usernames_tried: list[str] = field(default_factory=list)
    tools_run: int = 0
    tools_skipped: int = 0
    raw_text: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _target_for_field(field: str, target: FossTarget, username: str | None) -> FossTarget | None:
    if field == "username" and username:
        return FossTarget(username=username, email=target.email, phone=target.phone, name=target.name)
    if field == "email" and target.email:
        return target
    if field == "phone" and target.phone:
        return target
    return None


def build_foss_target(config: PipelineConfig, *, username_override: str | None = None) -> FossTarget:
    usernames = guess_usernames(config.subject, config.email)
    if username_override:
        usernames = [username_override, *[u for u in usernames if u != username_override]]
    return FossTarget(
        name=config.subject,
        email=config.email,
        phone=config.phone,
        username=usernames[0] if usernames else None,
        usernames=usernames,
    )


def social_tools_for_config(config: PipelineConfig, *, full: bool = False) -> list[tuple[str, str, str | None]]:
    """Return (field, tool_id, username) tuples to run."""
    target = build_foss_target(config)
    chain = FULL_SOCIAL_TOOLS if full else FAST_SOCIAL_TOOLS
    planned: list[tuple[str, str, str | None]] = []
    primary = target.usernames[0] if target.usernames else target.username

    for field, tool_id in chain:
        if field == "username":
            if not primary:
                continue
            planned.append((field, tool_id, primary))
        elif field == "email" and target.email:
            planned.append((field, tool_id, None))
        elif field == "phone" and target.phone:
            planned.append((field, tool_id, None))
    return planned


def run_social_pai(
    config: PipelineConfig,
    *,
    out_dir: Path | None = None,
    full: bool = False,
    max_usernames: int = 2,
    username_override: str | None = None,
) -> SocialPaiResult:
    """Run social-network PAI tools and aggregate discovered profile URLs."""
    result = SocialPaiResult()
    base = build_foss_target(config, username_override=username_override)
    result.usernames_tried = list(base.usernames[:max_usernames])

    root = out_dir or Path("out") / "social"
    root.mkdir(parents=True, exist_ok=True)

    planned = social_tools_for_config(config, full=full)

    # Extra sherlock passes on alternate username guesses
    for alt in base.usernames[1:max_usernames]:
        planned.append(("username", "sherlock", alt))

    for field, tool_id, username in planned:
        tool = get_foss_tool(tool_id)
        if not tool:
            result.tools_skipped += 1
            continue
        ok, _ = check_tool_available(tool)
        if not ok:
            result.tools_skipped += 1
            result.errors.append(f"{tool_id}: not available")
            continue

        run_target = _target_for_field(field, base, username)
        if run_target is None:
            continue

        tool_out = root / tool_id / (username or field)
        foss_result = run_foss_tool(tool_id, run_target, output_dir=tool_out)
        result.tools_run += 1

        stdout = foss_result.get("stdout") or ""
        stderr = foss_result.get("stderr") or ""
        if stdout:
            result.raw_text.append(stdout)
        if foss_result.get("success") or stdout or stderr:
            profiles = parse_tool_output(
                tool_id,
                "\n".join([stdout, stderr]),
                foss_result.get("output_dir"),
            )
            result.profiles.update(profiles)
        elif foss_result.get("error"):
            result.errors.append(f"{tool_id}: {foss_result['error']}")

    return result
