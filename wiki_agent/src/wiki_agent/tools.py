from __future__ import annotations

import fnmatch
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from ner.providers.hanlp_provider import HanLPNerProvider
from ontology_store import OntologyStore, build_wiki_slug
from wiki_agent.wikimg_backend import WikimgBackend


_BLOCKED_SHELL_PATTERNS = (";", "&&", "||", "|", ">", ">>", "<")
_READONLY_COMMANDS = {"pwd", "ls", "find", "rg", "cat", "sed", "head", "tail", "wc", "sort", "stat"}
_PYTHON_MODULES = {
    "wikimg",
    "ner.cli",
    "entity_relation.cli",
    "ontology_store.cli",
    "ontology_core.cli",
    "ontology_negotiator.cli",
    "pipeline.cli",
    "mm_denoise.cli",
    "xiaogugit",
    "ontology_audit_hub.review_cli",
    "ontology_audit_hub.qa_cli",
}
_BASELINE_REWRITES = {
    "ner.cli": "ner",
    "entity_relation.cli": "entity-relation",
    "ontology_store.cli": "ontology-store",
    "ontology_core.cli": "ontology-core",
    "ontology_negotiator.cli": "ontology-negotiator",
    "pipeline.cli": "pipeline",
    "mm_denoise.cli": "mm-denoise",
    "xiaogugit": "xiaogugit",
}
_PATH_FLAGS_BY_MODULE = {
    "ner.cli": {"--input", "--output"},
    "entity_relation.cli": {"--input", "--output"},
    "ontology_store.cli": {"--database", "--output"},
    "ontology_core.cli": {"--database", "--output"},
    "ontology_negotiator.cli": {"--graph", "--config", "--artifact-root", "--output"},
    "pipeline.cli": {"--input", "--input-dir", "--pipeline-config", "--preprocess-config", "--xiaogugit-root", "--output"},
    "mm_denoise.cli": {"--input", "--config", "--base-dir", "--output-dir"},
    "xiaogugit": {"--root-dir", "--data-file"},
    "ontology_audit_hub.review_cli": {"--request-file"},
    "ontology_audit_hub.qa_cli": {"--request-file", "--file"},
}


class WikiAgentToolbox:
    def __init__(
        self,
        *,
        store: OntologyStore,
        document_id: str,
        doc_name: str,
        clean_text: str,
        run_id: str,
        provider: HanLPNerProvider | None = None,
        workspace_root: str | Path | None = None,
        target_folder: str | Path | None = None,
        document_path: str | Path | None = None,
    ) -> None:
        self.store = store
        self.document_id = document_id
        self.doc_name = doc_name
        self.clean_text = clean_text
        self.run_id = run_id
        self.provider = provider or HanLPNerProvider()
        self.repo_root = Path(__file__).resolve().parents[3]
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.target_folder = Path(target_folder or self.workspace_root).resolve()
        self.document_path = Path(document_path).resolve() if document_path else None
        self.backend = WikimgBackend(self.workspace_root)

    def execute(self, action_name: str, action_input: dict[str, Any] | None = None) -> dict[str, Any]:
        if action_name != "run_command":
            raise ValueError(f"unknown tool: {action_name}")
        payload = action_input or {}
        return self.tool_run_command(str(payload.get("command", "")))

    def ensure_page_slug(self, title: str) -> str:
        base_slug = build_wiki_slug(title)
        existing = self.store.get_page_by_slug(base_slug)
        if existing is None:
            return base_slug
        if _similarity(title.lower(), existing.title.lower()) >= 0.85:
            return existing.slug
        suffix = __import__("hashlib").sha1(title.encode("utf-8")).hexdigest()[:6]
        return f"{base_slug}-{suffix}"

    def choose_layer(self, title: str, page_type: str = "topic") -> str:
        entities = self.store.list_canonical_entities()
        normalized = title.strip().lower()
        best_score = 0.0
        best_canonical_id = ""
        for entity in entities:
            score = max(
                _similarity(normalized, entity.preferred_name.strip().lower()),
                _similarity(normalized, entity.normalized_text.strip().lower()),
            )
            if score > best_score:
                best_score = score
                best_canonical_id = entity.canonical_id
        if best_canonical_id and best_score >= 0.9:
            classification = self.store.get_current_classification(best_canonical_id)
            if classification is not None:
                label = classification.ontology_label.strip()
                if label == "通":
                    return "common"
                if label == "私":
                    return "private"
                if label == "类":
                    return "domain"
        return "domain"

    def tool_run_command(self, command: str) -> dict[str, Any]:
        argv = [_strip_wrapping_quotes(token) for token in shlex.split(str(command).strip(), posix=os.name != "nt")]
        if not argv:
            raise ValueError("empty command")
        if any(pattern in str(command) for pattern in _BLOCKED_SHELL_PATTERNS):
            raise ValueError("shell operators are not allowed")
        self._validate_command(argv)

        env = os.environ.copy()
        env["PYTHONPATH"] = _build_pythonpath(self.workspace_root, self.repo_root, env.get("PYTHONPATH", ""))
        env["PATH"] = _build_tool_path(self.repo_root, env.get("PATH", ""))

        if argv[0] in _READONLY_COMMANDS:
            observation = self._execute_readonly_command(argv)
            observation["command"] = command
            observation["cwd"] = str(self.target_folder)
            return _truncate_observation(observation, max_chars=6000)

        executable_argv = self._normalize_command(argv)
        timeout = self._timeout_for_command(executable_argv)
        try:
            completed = subprocess.run(
                executable_argv,
                cwd=str(self.target_folder),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )
        except FileNotFoundError as error:
            return _truncate_observation(
                {
                    "command": command,
                    "cwd": str(self.target_folder),
                    "returncode": 127,
                    "stdout": "",
                    "stderr": str(error),
                },
                max_chars=6000,
            )
        return _truncate_observation(
            {
                "command": command,
                "cwd": str(self.target_folder),
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            },
            max_chars=6000,
        )

    def _validate_command(self, argv: list[str]) -> None:
        executable = argv[0]
        if executable in _READONLY_COMMANDS:
            self._validate_readonly_command(executable, argv[1:])
            return
        if executable == "wikimg":
            self._validate_wikimg(argv[1:])
            return
        if self._is_python_executable(executable):
            self._validate_python_invocation(argv[1:])
            return
        raise ValueError(f"unsupported command: {executable}")

    def _validate_readonly_command(self, executable: str, args: list[str]) -> None:
        if executable == "find":
            self._validate_find_args(args)
            return
        if executable == "rg":
            self._validate_rg_args(args)
            return
        if executable == "sed":
            self._validate_sed_args(args)
            return
        for arg in args:
            if self._is_candidate_path_arg(arg):
                self._ensure_path_inside_target(arg)

    def _validate_wikimg(self, args: list[str]) -> None:
        if not args:
            raise ValueError("wikimg requires subcommand")
        if "--root" in args:
            idx = args.index("--root")
            if idx + 1 >= len(args):
                raise ValueError("wikimg --root requires a path")
            root = Path(args[idx + 1]).resolve()
            if root != self.workspace_root:
                raise ValueError("wikimg --root must point to current workspace")

    def _validate_python_invocation(self, args: list[str]) -> None:
        if not args:
            raise ValueError("python command requires arguments")
        if args[0] == "-m":
            self._validate_python_module(args)
            return
        self._validate_python_script(args)

    def _validate_python_module(self, args: list[str]) -> None:
        if len(args) < 2 or args[0] != "-m":
            raise ValueError("python commands must use -m")
        module = args[1]
        if module not in _PYTHON_MODULES:
            raise ValueError(f"unsupported python module: {module}")
        self._validate_module_paths(module, args[2:])

    def _validate_python_script(self, args: list[str]) -> None:
        script = Path(args[0])
        resolved = script if script.is_absolute() else (self.repo_root / script).resolve()
        baseline_script = (self.repo_root / "tools" / "cli_baseline.py").resolve()
        if resolved != baseline_script:
            raise ValueError("python script commands must use tools/cli_baseline.py")
        self._validate_cli_baseline(args[1:])

    def _validate_cli_baseline(self, args: list[str]) -> None:
        if not args:
            raise ValueError("cli_baseline requires a subcommand")
        subcommand = args[0]
        if subcommand in {"list", "doctor", "smoke"}:
            return
        if subcommand != "run":
            raise ValueError(f"unsupported cli_baseline subcommand: {subcommand}")
        if len(args) < 2:
            raise ValueError("cli_baseline run requires a CLI name")
        cli_name = args[1]
        cli_args = list(args[2:])
        if cli_args and cli_args[0] == "--":
            cli_args = cli_args[1:]
        module = _baseline_cli_to_module(cli_name)
        if module is None:
            return
        self._validate_module_paths(module, cli_args)

    def _validate_module_paths(self, module: str, args: list[str]) -> None:
        for flag in _PATH_FLAGS_BY_MODULE.get(module, set()):
            for path_arg in self._extract_flag_values(args, flag):
                self._ensure_path_inside_workspace(path_arg)

    def _normalize_command(self, argv: list[str]) -> list[str]:
        if argv[0] == "wikimg":
            return [sys.executable, "-m", "wikimg", *argv[1:]]
        if self._is_python_executable(argv[0]):
            return self._normalize_python_invocation(argv)
        return argv

    def _normalize_python_invocation(self, argv: list[str]) -> list[str]:
        python_executable = sys.executable
        args = list(argv[1:])
        if args[:2] == ["-m", "wikimg"]:
            return [python_executable, "-m", "wikimg", *args[2:]]
        if len(args) >= 2 and args[0] == "-m" and args[1] in _BASELINE_REWRITES:
            cli_name = _BASELINE_REWRITES[args[1]]
            return [
                python_executable,
                str((self.repo_root / "tools" / "cli_baseline.py").resolve()),
                "run",
                cli_name,
                "--",
                *args[2:],
            ]
        if args:
            script = Path(args[0])
            resolved = script if script.is_absolute() else (self.repo_root / script).resolve()
            baseline_script = (self.repo_root / "tools" / "cli_baseline.py").resolve()
            if resolved == baseline_script:
                return [python_executable, str(baseline_script), *args[1:]]
        return [python_executable, *args]

    def _timeout_for_command(self, argv: list[str]) -> int:
        rendered = " ".join(argv)
        if "--help" in argv or " doctor " in f" {rendered} ":
            return 20
        if any(keyword in rendered for keyword in ("mm_denoise", "pipeline", "xiaogugit", "mm-denoise")):
            return 180
        return 60

    def _execute_readonly_command(self, argv: list[str]) -> dict[str, Any]:
        command = argv[0]
        args = argv[1:]
        if command == "pwd":
            return {"returncode": 0, "stdout": str(self.target_folder), "stderr": ""}
        if command == "ls":
            return {"returncode": 0, "stdout": self._readonly_ls(args), "stderr": ""}
        if command == "find":
            return {"returncode": 0, "stdout": self._readonly_find(args), "stderr": ""}
        if command == "rg":
            return {"returncode": 0, "stdout": self._readonly_rg(args), "stderr": ""}
        if command == "cat":
            return {"returncode": 0, "stdout": self._readonly_cat(args), "stderr": ""}
        if command == "sed":
            return {"returncode": 0, "stdout": self._readonly_sed(args), "stderr": ""}
        if command == "head":
            return {"returncode": 0, "stdout": self._readonly_head_tail(args, tail=False), "stderr": ""}
        if command == "tail":
            return {"returncode": 0, "stdout": self._readonly_head_tail(args, tail=True), "stderr": ""}
        if command == "wc":
            return {"returncode": 0, "stdout": self._readonly_wc(args), "stderr": ""}
        if command == "sort":
            return {"returncode": 0, "stdout": self._readonly_sort(args), "stderr": ""}
        if command == "stat":
            return {"returncode": 0, "stdout": self._readonly_stat(args), "stderr": ""}
        raise ValueError(f"unsupported readonly command: {command}")

    def _readonly_ls(self, args: list[str]) -> str:
        paths = [self._resolve_target_path(arg) for arg in args if not arg.startswith("-")] or [self.target_folder]
        lines: list[str] = []
        for path in paths:
            if path.is_dir():
                for item in sorted(path.iterdir(), key=lambda value: value.name.lower()):
                    name = item.name + ("/" if item.is_dir() else "")
                    lines.append(name)
            elif path.exists():
                lines.append(path.name)
        return "\n".join(lines)

    def _readonly_find(self, args: list[str]) -> str:
        search_root = self.target_folder
        name_pattern = "*"
        index = 0
        while index < len(args):
            item = args[index]
            if item == "-name" and index + 1 < len(args):
                name_pattern = args[index + 1]
                index += 2
                continue
            if not item.startswith("-"):
                search_root = self._resolve_target_path(item)
            index += 1
        matches = [
            str(path.relative_to(self.target_folder).as_posix() if path != self.target_folder else Path("."))
            for path in sorted(search_root.rglob(name_pattern))
        ]
        return "\n".join(str(match) for match in matches)

    def _readonly_rg(self, args: list[str]) -> str:
        positional: list[str] = []
        skip_next = False
        options_with_value = {"-g", "-t", "-T", "-f", "-m", "-A", "-B", "-C", "-M", "-j", "--glob", "--type", "--type-not", "--file", "--max-count", "--after-context", "--before-context", "--context", "--max-columns", "--threads"}
        for item in args:
            if skip_next:
                skip_next = False
                continue
            if item in options_with_value:
                skip_next = True
                continue
            if item.startswith("-"):
                continue
            positional.append(item)
        if not positional:
            raise ValueError("rg requires a search pattern")
        pattern = positional[0]
        search_paths = [self._resolve_target_path(item) for item in positional[1:]] or [self.target_folder]
        try:
            matcher = re.compile(pattern)
            search = lambda text: matcher.search(text) is not None
        except re.error:
            search = lambda text: pattern in text

        lines: list[str] = []
        for search_path in search_paths:
            candidates = [search_path] if search_path.is_file() else sorted(search_path.rglob("*"))
            for candidate in candidates:
                if not candidate.is_file():
                    continue
                try:
                    text = candidate.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if search(line):
                        relative = candidate.relative_to(self.target_folder).as_posix()
                        lines.append(f"{relative}:{line_number}:{line}")
        return "\n".join(lines)

    def _readonly_cat(self, args: list[str]) -> str:
        paths = [self._resolve_target_path(arg) for arg in args if not arg.startswith("-")]
        return "".join(path.read_text(encoding="utf-8", errors="replace") for path in paths)

    def _readonly_sed(self, args: list[str]) -> str:
        if len(args) < 3 or args[0] != "-n":
            raise ValueError("readonly sed supports only: sed -n START,ENDp <file>")
        command = args[1]
        match = re.fullmatch(r"(\d+),(\d+)p", command)
        if not match:
            raise ValueError("readonly sed supports only: sed -n START,ENDp <file>")
        start = int(match.group(1))
        end = int(match.group(2))
        path = self._resolve_target_path(args[2])
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = lines[max(0, start - 1) : end]
        return "\n".join(selected)

    def _readonly_head_tail(self, args: list[str], *, tail: bool) -> str:
        count = 10
        files: list[str] = []
        index = 0
        while index < len(args):
            item = args[index]
            if item in {"-n", "--lines"} and index + 1 < len(args):
                count = int(args[index + 1])
                index += 2
                continue
            files.append(item)
            index += 1
        path = self._resolve_target_path(files[0])
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = lines[-count:] if tail else lines[:count]
        return "\n".join(selected)

    def _readonly_wc(self, args: list[str]) -> str:
        lines: list[str] = []
        for item in args:
            if item.startswith("-"):
                continue
            path = self._resolve_target_path(item)
            text = path.read_text(encoding="utf-8", errors="replace")
            line_count = len(text.splitlines())
            word_count = len(text.split())
            char_count = len(text)
            lines.append(f"{line_count} {word_count} {char_count} {path.name}")
        return "\n".join(lines)

    def _readonly_sort(self, args: list[str]) -> str:
        path = self._resolve_target_path(next(item for item in args if not item.startswith("-")))
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(sorted(lines))

    def _readonly_stat(self, args: list[str]) -> str:
        path = self._resolve_target_path(next(item for item in args if not item.startswith("-")))
        info = path.stat()
        return "\n".join(
            [
                f"FullName: {path}",
                f"Length: {info.st_size}",
                f"Mode: {'directory' if path.is_dir() else 'file'}",
                f"LastWriteTime: {info.st_mtime}",
            ]
        )

    def _resolve_target_path(self, value: str) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = (self.target_folder / candidate).resolve()
        else:
            candidate = candidate.resolve()
        return candidate

    def _is_python_executable(self, executable: str) -> bool:
        rendered = str(executable).strip()
        if rendered in {"python", "python3", sys.executable}:
            return True
        return Path(rendered).name.lower() in {"python", "python.exe", "python3", "python3.exe"}

    def _extract_flag_values(self, args: list[str], flag: str) -> list[str]:
        values: list[str] = []
        index = 0
        while index < len(args):
            if args[index] == flag and index + 1 < len(args):
                values.append(args[index + 1])
                index += 2
                continue
            index += 1
        return values

    def _validate_find_args(self, args: list[str]) -> None:
        option_seen = False
        for arg in args:
            if arg.startswith("-"):
                option_seen = True
            if option_seen:
                continue
            if self._is_candidate_path_arg(arg):
                self._ensure_path_inside_target(arg)

    def _validate_rg_args(self, args: list[str]) -> None:
        option_with_value = {
            "-g",
            "-t",
            "-T",
            "-f",
            "-m",
            "-A",
            "-B",
            "-C",
            "-M",
            "-j",
            "--glob",
            "--type",
            "--type-not",
            "--file",
            "--max-count",
            "--after-context",
            "--before-context",
            "--context",
            "--max-columns",
            "--threads",
        }
        positional: list[str] = []
        skip = False
        for arg in args:
            if skip:
                skip = False
                continue
            if arg in option_with_value:
                skip = True
                continue
            if arg.startswith("-"):
                continue
            positional.append(arg)
        for path_arg in positional[1:]:
            if self._is_candidate_path_arg(path_arg):
                self._ensure_path_inside_target(path_arg)

    def _validate_sed_args(self, args: list[str]) -> None:
        positional: list[str] = []
        skip = False
        for arg in args:
            if skip:
                skip = False
                continue
            if arg in {"-e", "-f"}:
                skip = True
                continue
            if arg.startswith("-"):
                continue
            positional.append(arg)
        for path_arg in positional[1:]:
            if self._is_candidate_path_arg(path_arg):
                self._ensure_path_inside_target(path_arg)

    def _is_candidate_path_arg(self, value: str) -> bool:
        stripped = str(value).strip()
        if not stripped or stripped in {".", "./"}:
            return False
        if stripped.startswith("-"):
            return False
        return "/" in stripped or "." in stripped or stripped.isalnum()

    def _ensure_path_inside_target(self, value: str) -> None:
        candidate = self._resolve_target_path(value)
        root = self.target_folder.resolve()
        if candidate == root:
            return
        if root not in candidate.parents:
            raise ValueError(f"path outside target folder is not allowed: {value}")

    def _ensure_path_inside_workspace(self, value: str) -> None:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = (self.target_folder / candidate).resolve()
        else:
            candidate = candidate.resolve()
        root = self.workspace_root.resolve()
        if candidate == root:
            return
        if root not in candidate.parents:
            raise ValueError(f"path outside workspace is not allowed: {value}")


def _baseline_cli_to_module(cli_name: str) -> str | None:
    for module, candidate in _BASELINE_REWRITES.items():
        if candidate == cli_name:
            return module
    return None


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _truncate_observation(payload: dict[str, Any], max_chars: int = 4000) -> dict[str, Any]:
    raw = json_dumps(payload)
    if len(raw) <= max_chars:
        return payload
    return {"truncated": True, "preview": raw[:max_chars]}


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if left in right or right in left:
        return min(len(left), len(right)) / max(len(left), len(right))
    matches = sum(1 for a, b in zip(left, right) if a == b)
    return matches / max(len(left), len(right))


def _build_pythonpath(workspace_root: Path, repo_root: Path, existing: str) -> str:
    paths = [
        workspace_root,
        repo_root,
        repo_root / "WIKI_MG" / "src",
        repo_root / "storage" / "src",
        repo_root / "wiki_agent" / "src",
        repo_root / "ontology_core" / "src",
        repo_root / "evolution" / "src",
        repo_root / "relation" / "src",
        repo_root / "ner" / "src",
        repo_root / "dls" / "src",
        repo_root / "preprocess",
        repo_root / "pipeline" / "src",
        repo_root / "aft" / "aft-main" / "src",
    ]
    rendered = [str(path) for path in paths]
    if existing:
        rendered.append(existing)
    return os.pathsep.join(rendered)


def _build_tool_path(repo_root: Path, existing: str) -> str:
    paths = [
        repo_root / ".venv" / "Scripts",
        repo_root / ".venv" / "bin",
    ]
    rendered = [str(path) for path in paths if path.exists()]
    if existing:
        rendered.append(existing)
    return os.pathsep.join(rendered)


def json_dumps(payload: Any) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
