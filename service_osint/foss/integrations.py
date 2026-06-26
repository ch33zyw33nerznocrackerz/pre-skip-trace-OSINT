from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from service_osint.core.errors import error_dict
from service_osint.foss.models import FossTarget, FossTool, load_foss_tools

DOCKER_CWD: dict[str, str] = {
    "SPIDERFOOT_DIR": "/tools/spiderfoot",
    "PHOTON_DIR": "/tools/Photon",
}


def _foss_tool_from_dict(t: dict) -> FossTool:
    fields = {f.name for f in FossTool.__dataclass_fields__.values()}
    return FossTool(**{k: v for k, v in t.items() if k in fields})


def get_foss_tool(tool_id: str) -> FossTool | None:
    for tool in list_foss_tools():
        if tool.id == tool_id:
            return tool
    return None


def list_foss_tools(*, category: str | None = None) -> list[FossTool]:
    tools = [_foss_tool_from_dict(t) for t in load_foss_tools()]
    if category:
        tools = [t for t in tools if t.category == category]
    return tools


def use_docker_foss() -> bool:
    return os.getenv("FOSS_DOCKER", "").strip().lower() in {"1", "true", "yes"}


def _resolve_command(tool: FossTool, target: FossTarget, output_dir: Path) -> list[str]:
    replacements = {
        "{email}": target.email or "",
        "{domain}": target.resolved_domain or "",
        "{url}": target.url or "",
        "{username}": target.username or "",
        "{phone}": target.phone or "",
        "{output_dir}": str(output_dir),
    }
    return [part.format(**{k.strip("{}"): v for k, v in replacements.items()}) for part in tool.command]


def _argv_for_tool(tool: FossTool, inner_cmd: list[str]) -> list[str]:
    if tool.runner == "binary":
        return inner_cmd
    if tool.runner == "python":
        return ["python", *inner_cmd]
    if inner_cmd and inner_cmd[0].endswith(".py"):
        return ["python", *inner_cmd]
    return inner_cmd


def _compose_file() -> Path:
    raw = os.getenv("DOCKER_COMPOSE_FILE", "docker/docker-compose.yml")
    path = Path(raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _docker_command(
    tool: FossTool,
    argv: list[str],
    *,
    output_dir: Path | None = None,
) -> list[str]:
    compose = _compose_file()
    service = os.getenv("FOSS_DOCKER_SERVICE", "foss")
    workdir = tool.docker_cwd or DOCKER_CWD.get(tool.cwd_env or "", "") or "/tools"
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose),
        "--profile",
        "tools",
        "run",
        "--rm",
        "-T",
    ]
    if output_dir is not None:
        host_out = str(output_dir.resolve())
        cmd.extend(["-v", f"{host_out}:{host_out}"])
    for key in ("CHAOS_API_KEY",):
        val = os.getenv(key)
        if val:
            cmd.extend(["-e", f"{key}={val}"])
    cmd.extend(["-w", workdir, service, *argv])
    return cmd


def _work_dir(tool: FossTool) -> str | None:
    if use_docker_foss():
        return tool.docker_cwd or DOCKER_CWD.get(tool.cwd_env or "")
    if tool.cwd_env:
        path = os.environ.get(tool.cwd_env)
        if path and Path(path).is_dir():
            return path
        return None
    return None


def _is_binary_tool(tool: FossTool) -> bool:
    if tool.runner == "binary":
        return True
    if tool.runner == "python":
        return False
    if tool.cwd_env:
        return False
    return bool(tool.command) and not tool.command[0].endswith(".py")


def check_tool_available(tool: FossTool) -> tuple[bool, str]:
    if use_docker_foss():
        compose = _compose_file()
        if not compose.is_file():
            return False, f"Compose file not found: {compose}"
        if not shutil.which("docker"):
            return False, "docker not found in PATH"
        return True, f"docker:{tool.docker_cwd or tool.cwd_env or '/tools'}"

    if tool.cwd_env:
        wd = os.environ.get(tool.cwd_env)
        if not wd or not Path(wd).is_dir():
            return False, f"Set {tool.cwd_env} or FOSS_DOCKER=1 (see docker/docker-compose.yml)"
    if not tool.command:
        return False, "No command defined"

    if _is_binary_tool(tool):
        path = shutil.which(tool.command[0])
        return (True, path) if path else (False, f"pip install — {tool.install}")

    binary = tool.command[0]
    if tool.cwd_env:
        script = Path(os.environ.get(tool.cwd_env, "")) / binary
        if script.is_file():
            return True, str(script)
    if shutil.which("python") or shutil.which("python3"):
        return True, "python"
    return False, f"Install tool: {tool.install}"


def run_foss_tool(
    tool_id: str,
    target: FossTarget,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> dict:
    tool = get_foss_tool(tool_id)
    if not tool:
        return error_dict(f"Unknown tool: {tool_id}", hint="Run `osint foss list`.")

    available, detail = check_tool_available(tool)
    if not available and not dry_run:
        return error_dict(
            detail,
            hint=f"See `osint foss install-guide` or set FOSS_DOCKER=1.",
            install=tool.install,
            repo=tool.repo,
            tool=tool_id,
        )

    out = output_dir or Path.cwd() / "out" / "foss" / tool_id
    out.mkdir(parents=True, exist_ok=True)
    inner_cmd = _resolve_command(tool, target, out)
    argv = _argv_for_tool(tool, inner_cmd)

    if dry_run:
        cmd = _docker_command(tool, argv, output_dir=out) if use_docker_foss() else argv
        return {
            "success": True,
            "dry_run": True,
            "tool": tool.id,
            "command": cmd,
            "available": available,
            "detail": detail,
        }

    try:
        if use_docker_foss():
            cmd = _docker_command(tool, argv, output_dir=out)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=tool.timeout_seconds,
            )
        else:
            cwd = _work_dir(tool)
            cmd = argv
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=tool.timeout_seconds,
                cwd=cwd,
            )
        return {
            "success": result.returncode == 0,
            "tool": tool.id,
            "command": cmd,
            "returncode": result.returncode,
            "stdout": result.stdout[-8000:] if result.stdout else "",
            "stderr": result.stderr[-4000:] if result.stderr else "",
            "output_dir": str(out),
        }
    except subprocess.TimeoutExpired:
        return error_dict(
            f"Tool timed out after {tool.timeout_seconds}s",
            hint="Increase timeout in config or reduce scan scope.",
            tool=tool.id,
        )
    except OSError as exc:
        return error_dict(str(exc), hint="Check tool install and PATH.", tool=tool.id)


def foss_tools_for_target(target: FossTarget) -> list[str]:
    """Map available seed fields to crawl/scan tool ids."""
    ids: list[str] = []
    if target.email:
        ids.append("spiderfoot-email")
    if target.resolved_domain:
        ids.append("spiderfoot-domain")
        ids.append("subfinder")
    if target.url:
        ids.append("photon")
    return ids


def export_install_guide(path: Path | None = None) -> str:
    lines = [
        "# FOSS OSINT tools (SpiderFoot, Photon, social PAI)\n",
        "## Docker (recommended)\n",
        "```bash",
        "docker compose -f docker/docker-compose.yml up -d",
        "docker compose -f docker/docker-compose.yml --profile tools up -d foss",
        "```",
        "Set `FOSS_DOCKER=1` and `SEARXNG_URL=http://127.0.0.1:8080` in `.env`.\n",
        "Social PAI: `osint social scan \"Jane Doe\" --email jane@example.com`\n",
    ]
    for tool in list_foss_tools():
        available, _ = check_tool_available(tool)
        status = "ready" if available else "not configured"
        lines.append(f"## {tool.name} ({status})")
        lines.append(f"- **ID:** `{tool.id}`")
        lines.append(f"- **Repo:** {tool.repo}")
        lines.append(f"- **Install:** {tool.install}")
        lines.append(f"- **Description:** {tool.description}\n")

    content = "\n".join(lines)
    if path:
        path.write_text(content, encoding="utf-8")
    return content

