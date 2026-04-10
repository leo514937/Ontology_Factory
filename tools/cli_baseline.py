from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.qagent_unified_config import apply_unified_llm_env

COMMON_PYTHONPATHS = (
    REPO_ROOT,
    REPO_ROOT / "WIKI_MG" / "src",
    REPO_ROOT / "storage" / "src",
    REPO_ROOT / "wiki_agent" / "src",
    REPO_ROOT / "ontology_core" / "src",
    REPO_ROOT / "evolution" / "src",
    REPO_ROOT / "relation" / "src",
    REPO_ROOT / "ner" / "src",
    REPO_ROOT / "dls" / "src",
    REPO_ROOT / "preprocess",
    REPO_ROOT / "pipeline" / "src",
    REPO_ROOT / "aft" / "aft-main" / "src",
)
DEPENDENCY_MANIFEST_PATH = REPO_ROOT / "agent_runtime_dependencies.json"
DEFAULT_PREPROCESS_CONFIG = REPO_ROOT / "preprocess" / "config.no_models.yaml"
DEFAULT_DATABASE_PATH = REPO_ROOT / "storage" / "data" / "classification_store.sqlite3"
DEFAULT_XIAOGUGIT_ROOT = REPO_ROOT / "xiaogugit" / "storage"


@dataclass(frozen=True)
class CliSpec:
    name: str
    module: str
    min_python: tuple[int, int]
    help_args: tuple[str, ...]
    description: str


CLI_SPECS: dict[str, CliSpec] = {
    "wikimg": CliSpec(
        name="wikimg",
        module="wikimg",
        min_python=(3, 10),
        help_args=("--help",),
        description="Layered wiki CLI.",
    ),
    "ner": CliSpec(
        name="ner",
        module="ner.cli",
        min_python=(3, 10),
        help_args=("extract", "--help"),
        description="Named entity extraction CLI.",
    ),
    "entity-relation": CliSpec(
        name="entity-relation",
        module="entity_relation.cli",
        min_python=(3, 10),
        help_args=("extract", "--help"),
        description="Relation extraction CLI.",
    ),
    "ontology-store": CliSpec(
        name="ontology-store",
        module="ontology_store.cli",
        min_python=(3, 10),
        help_args=("query", "--help"),
        description="Storage query CLI.",
    ),
    "ontology-core": CliSpec(
        name="ontology-core",
        module="ontology_core.cli",
        min_python=(3, 10),
        help_args=("search", "--help"),
        description="Canonical ontology search CLI.",
    ),
    "ontology-negotiator": CliSpec(
        name="ontology-negotiator",
        module="ontology_negotiator.cli",
        min_python=(3, 10),
        help_args=("classify", "--help"),
        description="Ontology negotiator CLI.",
    ),
    "pipeline": CliSpec(
        name="pipeline",
        module="pipeline.cli",
        min_python=(3, 10),
        help_args=("--help",),
        description="Unified ingest and wiki pipeline CLI.",
    ),
    "mm-denoise": CliSpec(
        name="mm-denoise",
        module="mm_denoise.cli",
        min_python=(3, 10),
        help_args=("--help",),
        description="Document preprocessing and denoise CLI.",
    ),
    "xiaogugit": CliSpec(
        name="xiaogugit",
        module="xiaogugit",
        min_python=(3, 9),
        help_args=("--help",),
        description="Git-backed ontology versioning CLI.",
    ),
    "aft-review": CliSpec(
        name="aft-review",
        module="ontology_audit_hub.review_cli",
        min_python=(3, 11),
        help_args=("--help",),
        description="AFT GitHub review CLI.",
    ),
    "aft-qa": CliSpec(
        name="aft-qa",
        module="ontology_audit_hub.qa_cli",
        min_python=(3, 11),
        help_args=("--help",),
        description="AFT QA and ingestion CLI.",
    ),
}


def _python_version_label(version: tuple[int, int]) -> str:
    return f"{version[0]}.{version[1]}"


def _current_python_tuple() -> tuple[int, int]:
    return sys.version_info[:2]


def supports_current_python(spec: CliSpec) -> bool:
    return _current_python_tuple() >= spec.min_python


def build_env(existing: dict[str, str] | None = None) -> dict[str, str]:
    env = apply_unified_llm_env(existing)
    pythonpath_entries = [str(path) for path in COMMON_PYTHONPATHS]
    existing_pythonpath = env.get("PYTHONPATH", "").strip()
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    return env


def build_command(cli_name: str, args: Sequence[str]) -> list[str]:
    spec = CLI_SPECS[cli_name]
    return [sys.executable, "-m", spec.module, *args]


def run_cli(
    cli_name: str,
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: int = 30,
    ) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        build_command(cli_name, args),
        cwd=str(cwd or REPO_ROOT),
        env=build_env(),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def collect_dependency_status(entries: Sequence[dict[str, object]]) -> dict[str, object]:
    checked: list[dict[str, object]] = []
    required_missing: list[dict[str, str]] = []
    optional_missing: list[dict[str, str]] = []
    for entry in entries:
        module = str(entry.get("module", "")).strip()
        package = str(entry.get("package", module)).strip() or module
        optional = bool(entry.get("optional", False))
        available = bool(module) and importlib.util.find_spec(module) is not None
        item = {
            "module": module,
            "package": package,
            "optional": optional,
            "available": available,
        }
        checked.append(item)
        if available:
            continue
        missing_item = {"module": module, "package": package}
        if optional:
            optional_missing.append(missing_item)
        else:
            required_missing.append(missing_item)
    return {
        "checked": checked,
        "optional": [item for item in checked if item["optional"]],
        "required_missing": required_missing,
        "optional_missing": optional_missing,
    }


def _load_dependency_manifest() -> dict[str, object]:
    if not DEPENDENCY_MANIFEST_PATH.exists():
        return {}
    return json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))


def _dependency_entries_for_cli(cli_name: str) -> list[dict[str, object]]:
    manifest = _load_dependency_manifest()
    common_required = list(manifest.get("common", {}).get("required", [])) if isinstance(manifest, dict) else []
    cli_config = {}
    if isinstance(manifest, dict):
        cli_config = dict(manifest.get("clis", {}).get(cli_name, {}) or {})
    entries: list[dict[str, object]] = []
    for item in common_required:
        entries.append({**dict(item), "optional": False})
    for item in cli_config.get("required", []):
        entries.append({**dict(item), "optional": False})
    for item in cli_config.get("optional", []):
        entries.append({**dict(item), "optional": True})
    return entries


def _default_paths_for_cli(cli_name: str) -> dict[str, str]:
    defaults: dict[str, str] = {}
    if cli_name in {"mm-denoise", "pipeline"}:
        defaults["config_path"] = str(DEFAULT_PREPROCESS_CONFIG)
    if cli_name in {"ontology-store", "ontology-core", "pipeline"}:
        defaults["database_path"] = str(DEFAULT_DATABASE_PATH)
    if cli_name in {"xiaogugit", "pipeline"}:
        defaults["xiaogugit_root"] = str(DEFAULT_XIAOGUGIT_ROOT)
    return defaults


def _help_check(cli_name: str) -> dict[str, object]:
    spec = CLI_SPECS[cli_name]
    completed = run_cli(cli_name, spec.help_args, timeout=20)
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "command": build_command(cli_name, spec.help_args),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def doctor_cli(
    cli_name: str,
    *,
    include_help: bool = True,
    include_smoke: bool = True,
) -> dict[str, object]:
    spec = CLI_SPECS[cli_name]
    dependency_status = collect_dependency_status(_dependency_entries_for_cli(cli_name))
    payload: dict[str, object] = {
        "cli": cli_name,
        "module": spec.module,
        "description": spec.description,
        "interpreter": sys.executable,
        "python": {
            "current": _python_version_label(_current_python_tuple()),
            "required": _python_version_label(spec.min_python),
            "supported": supports_current_python(spec),
        },
        "defaults": _default_paths_for_cli(cli_name),
        "dependencies": dependency_status,
        "checks": {},
    }
    if include_help:
        payload["checks"]["help"] = _help_check(cli_name)
    if include_smoke:
        payload["checks"]["smoke"] = smoke_cli(cli_name)
    return payload


def doctor_clis(
    cli_names: Sequence[str] | None = None,
    *,
    include_help: bool = True,
    include_smoke: bool = True,
) -> list[dict[str, object]]:
    names = list(cli_names) if cli_names else list(CLI_SPECS)
    return [
        doctor_cli(name, include_help=include_help, include_smoke=include_smoke)
        for name in names
    ]


def _smoke_args(cli_name: str) -> list[str]:
    spec = CLI_SPECS[cli_name]
    if cli_name == "xiaogugit":
        raise ValueError("xiaogugit smoke args are built from a temporary directory")
    if cli_name == "wikimg":
        raise ValueError("wikimg smoke args are built from a temporary directory")
    return list(spec.help_args)


def smoke_cli(cli_name: str) -> dict[str, object]:
    spec = CLI_SPECS[cli_name]
    if not supports_current_python(spec):
        return {
            "cli": cli_name,
            "status": "skipped",
            "reason": (
                f"requires Python >= {_python_version_label(spec.min_python)}, "
                f"current interpreter is {_python_version_label(_current_python_tuple())}"
            ),
        }

    if cli_name == "xiaogugit":
        smoke_args = ["--root-dir", "<tempdir>", "project", "list"]
        with tempfile.TemporaryDirectory(prefix="cli-baseline-xiaogugit-") as temp_dir:
            completed = run_cli(
                cli_name,
                ["--root-dir", temp_dir, "project", "list"],
            )
    elif cli_name == "wikimg":
        smoke_args = ["init"]
        with tempfile.TemporaryDirectory(prefix="cli-baseline-wikimg-") as temp_dir:
            completed = run_cli(cli_name, ["init"], cwd=Path(temp_dir))
    else:
        smoke_args = _smoke_args(cli_name)
        completed = run_cli(cli_name, smoke_args)

    payload = {
        "cli": cli_name,
        "command": build_command(cli_name, smoke_args),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    payload["status"] = "passed" if completed.returncode == 0 else "failed"
    return payload


def smoke_clis(cli_names: Sequence[str] | None = None) -> list[dict[str, object]]:
    names = list(cli_names) if cli_names else list(CLI_SPECS)
    return [smoke_cli(name) for name in names]


def _render_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _strip_remainder(args: Sequence[str]) -> list[str]:
    remainder = list(args)
    if remainder and remainder[0] == "--":
        return remainder[1:]
    return remainder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified startup and smoke-test baseline for repository CLIs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List supported CLI specs.")

    run_parser = subparsers.add_parser("run", help="Run one CLI with the shared interpreter/PYTHONPATH baseline.")
    run_parser.add_argument("cli", choices=sorted(CLI_SPECS))
    run_parser.add_argument("args", nargs=argparse.REMAINDER)

    smoke_parser = subparsers.add_parser("smoke", help="Run smoke checks for one or more CLIs.")
    smoke_parser.add_argument(
        "--cli",
        dest="cli_names",
        action="append",
        choices=sorted(CLI_SPECS),
        help="Limit smoke checks to specific CLIs.",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Inspect runtime dependencies, defaults, and help/smoke status.")
    doctor_parser.add_argument(
        "--cli",
        dest="cli_names",
        action="append",
        choices=sorted(CLI_SPECS),
        help="Limit doctor checks to specific CLIs.",
    )
    doctor_parser.add_argument("--skip-help", action="store_true", help="Skip --help verification.")
    doctor_parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke verification.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "list":
        _render_json(
            [
                {
                    "name": spec.name,
                    "module": spec.module,
                    "min_python": _python_version_label(spec.min_python),
                    "description": spec.description,
                }
                for spec in CLI_SPECS.values()
            ]
        )
        return 0

    if args.command == "run":
        cli_args = _strip_remainder(args.args)
        completed = run_cli(args.cli, cli_args)
        _render_json(
            {
                "cli": args.cli,
                "command": build_command(args.cli, cli_args),
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        return completed.returncode

    if args.command == "smoke":
        results = smoke_clis(args.cli_names)
        _render_json(results)
        return 1 if any(result["status"] == "failed" for result in results) else 0

    if args.command == "doctor":
        results = doctor_clis(
            args.cli_names,
            include_help=not args.skip_help,
            include_smoke=not args.skip_smoke,
        )
        _render_json(results)
        has_required_missing = any(item["dependencies"]["required_missing"] for item in results)
        has_failed_checks = any(
            check.get("status") == "failed"
            for item in results
            for check in item.get("checks", {}).values()
            if isinstance(check, dict)
        )
        return 1 if has_required_missing or has_failed_checks else 0

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
