"""Generate deterministic dependency lockfiles and wheels for CI."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:  # Python >= 3.11
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover - bootstrap tomli
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "tomli==2.0.1"]
        )
        import tomli as tomllib  # type: ignore[no-redef]

try:
    from packaging.specifiers import SpecifierSet
except ModuleNotFoundError:  # pragma: no cover - bootstrap packaging for dependency doctor
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "packaging==25.0"]
    )
    from packaging.specifiers import SpecifierSet


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"
CONSTRAINTS_DIR = ROOT / "constraints"
WHEELS_DIR = ROOT / "wheels"
REQUIREMENTS_IN = ROOT / "requirements.in"
REQUIREMENTS_DEV_IN = ROOT / "requirements-dev.in"
REQUIREMENTS_TXT = ROOT / "requirements.txt"
REQUIREMENTS_DEV_TXT = ROOT / "requirements-dev.txt"
ENV_HEALTH_REPORT = REPORTS_DIR / "ENV_HEALTH.md"
UPSTREAM_REQUIREMENTS = [
    ROOT / ".upstream" / "Fixops" / "requirements.txt",
    ROOT / ".upstream" / "Fixops" / "requirements.dev.txt",
]


DEFAULT_MATRIX = ["3.10", "3.11", "3.12"]


@dataclass
class CommandResult:
    command: Sequence[str]
    returncode: int
    stdout: str
    stderr: str


def _run(command: Sequence[str], *, cwd: Path | None = None) -> CommandResult:
    process = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(command)} failed with code {process.returncode}\n{process.stderr}"
        )
    return CommandResult(command, process.returncode, process.stdout, process.stderr)


def _install_piptools() -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pip-tools>=7.3,<7.4"])


def _load_pyproject(path: Path) -> Dict[str, object]:
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _project_dependencies(pyproject: Dict[str, object]) -> List[str]:
    project = pyproject.get("project") if isinstance(pyproject, dict) else {}
    if not isinstance(project, dict):
        return []
    deps = project.get("dependencies", [])
    return [str(dep) for dep in deps]


def _dev_dependencies(pyproject: Dict[str, object]) -> List[str]:
    project = pyproject.get("project") if isinstance(pyproject, dict) else {}
    if not isinstance(project, dict):
        return []
    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, dict):
        return []
    dev = optional.get("dev", [])
    return [str(dep) for dep in dev]


def _requires_python(pyproject: Dict[str, object]) -> SpecifierSet | None:
    project = pyproject.get("project") if isinstance(pyproject, dict) else {}
    if isinstance(project, dict):
        requires = project.get("requires-python")
        if isinstance(requires, str):
            return SpecifierSet(requires)
    return None


def _parse_requirement_hints() -> List[str]:
    hints: List[str] = []
    for path in UPSTREAM_REQUIREMENTS:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if "python_version" in line:
                hints.append(line)
    return hints


def _matrix_from_spec(spec: SpecifierSet | None, hints: Iterable[str]) -> List[str]:
    matrix = list(DEFAULT_MATRIX)
    if spec is None and not hints:
        return matrix
    if spec is not None:
        matrix = [version for version in matrix if spec.contains(version)] or matrix
    for hint in hints:
        if ">=" in hint or ">" in hint or "<" in hint or "<=" in hint:
            expression = hint.split(";", 1)[-1].strip()
            for marker in [
                "python_version >=",
                "python_version >",
                "python_version <=",
                "python_version <",
            ]:
                if marker in expression:
                    value = expression.split(marker, 1)[-1].strip().strip("'\"")
                    spec_set = SpecifierSet(f"{marker.split()[-1]}{value}")
                    matrix = [version for version in matrix if spec_set.contains(version)] or matrix
    return sorted(set(matrix))


def _write_requirements(base: List[str], dev: List[str]) -> None:
    REQUIREMENTS_IN.write_text("\n".join(sorted(set(base))) + "\n", encoding="utf-8")
    dev_lines = ["-r requirements.in"] + sorted(set(dev))
    REQUIREMENTS_DEV_IN.write_text("\n".join(dev_lines) + "\n", encoding="utf-8")


def _pip_compile(input_path: Path, output_path: Path) -> CommandResult:
    command = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        str(input_path),
        "--output-file",
        str(output_path),
        "--resolver",
        "backtracking",
        "--upgrade",
    ]
    return _run(command)


def _pip_wheel(requirements_path: Path) -> CommandResult:
    WHEELS_DIR.mkdir(parents=True, exist_ok=True)
    for artifact in WHEELS_DIR.glob("*.whl"):
        artifact.unlink()
    command = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "-r",
        str(requirements_path),
        "-w",
        str(WHEELS_DIR),
    ]
    result = _run(command)
    readme_path = WHEELS_DIR / "README.md"
    if readme_path.exists():
        # Ensure the README survives the build cycle for source control context.
        readme_path.touch()
    return result


def _install_test(requirements_path: Path) -> CommandResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        pip_exe = venv_path / "bin" / "pip"
        command = [
            str(pip_exe),
            "install",
            "--no-index",
            "--find-links",
            str(WHEELS_DIR),
            "-r",
            str(requirements_path),
        ]
        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode != 0:
            raise RuntimeError(
                f"Install test failed with code {process.returncode}\n{process.stderr}"
            )
        return CommandResult(command, process.returncode, process.stdout, process.stderr)


PROGRESS_LINE = re.compile(r"^\s*[\u2500-\u259F]+\s+\S+/\S+\s+MB.*$")


def _normalize_log(text: str) -> str:
    if not text:
        return ""
    lines: List[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\b(?:Downloading|Using cached)\b", "Fetching", raw_line)
        if PROGRESS_LINE.match(line):
            indent = len(line) - len(line.lstrip())
            line = " " * indent + "<progress elided>"
        lines.append(line)
    return "\n".join(lines)


def _render_section(title: str, content: str) -> List[str]:
    lines = [f"## {title}", ""]
    lines.append("```text")
    lines.extend(content.strip().splitlines())
    lines.append("```")
    lines.append("")
    return lines


def build_wheelhouse(requirements_path: Path = REQUIREMENTS_TXT) -> Tuple[CommandResult, CommandResult]:
    if not requirements_path.is_file():
        raise FileNotFoundError(
            f"Cannot build wheelhouse; missing requirements file at {requirements_path}"
        )
    wheel_log = _pip_wheel(requirements_path)
    install_log = _install_test(requirements_path)
    return wheel_log, install_log


def generate() -> Dict[str, object]:
    _install_piptools()
    pyproject = _load_pyproject(ROOT / "pyproject.toml")
    base_deps = _project_dependencies(pyproject)
    dev_deps = _dev_dependencies(pyproject)
    spec = _requires_python(pyproject)
    hints = _parse_requirement_hints()
    matrix = _matrix_from_spec(spec, hints)

    _write_requirements(base_deps, dev_deps)

    CONSTRAINTS_DIR.mkdir(parents=True, exist_ok=True)
    for path in CONSTRAINTS_DIR.glob("py*.txt"):
        path.unlink()
    compile_logs: List[Tuple[str, CommandResult]] = []
    for version in matrix:
        constraints_path = CONSTRAINTS_DIR / f"py{version.replace('.', '')}.txt"
        compile_logs.append((version, _pip_compile(REQUIREMENTS_IN, constraints_path)))

    base_compile = _pip_compile(REQUIREMENTS_IN, REQUIREMENTS_TXT)
    dev_compile = _pip_compile(REQUIREMENTS_DEV_IN, REQUIREMENTS_DEV_TXT)

    wheel_log, install_log = build_wheelhouse(REQUIREMENTS_TXT)

    report_lines: List[str] = ["# Environment Health", ""]
    report_lines.append("Generated via tools/env/dependency_doctor.py.")
    report_lines.append("")
    report_lines.append("## Detected Python Versions")
    report_lines.append("")
    for version in matrix:
        report_lines.append(f"- Python {version}")
    if hints:
        report_lines.append("")
        report_lines.append("### Upstream Hints")
        report_lines.append("")
        for hint in hints:
            report_lines.append(f"- `{hint}`")
    report_lines.append("")
    report_lines.append(
        "> Constraints are compiled with the active interpreter because pip-tools no longer supports"
        " per-command python version overrides."
    )
    report_lines.append("")
    for version, entry in compile_logs:
        report_lines.extend(
            _render_section(
                f"Constraints for Python {version}",
                _normalize_log(entry.stdout or "(no output)"),
            )
        )
    report_lines.extend(
        _render_section(
            "requirements.txt", _normalize_log(base_compile.stdout or "(no output)")
        )
    )
    report_lines.extend(
        _render_section(
            "requirements-dev.txt",
            _normalize_log(dev_compile.stdout or "(no output)"),
        )
    )
    report_lines.extend(
        _render_section("Wheel Build", _normalize_log(wheel_log.stdout or "(no output)"))
    )
    report_lines.extend(
        _render_section(
            "Install Test", _normalize_log(install_log.stdout or "(no output)")
        )
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ENV_HEALTH_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    return {
        "matrix": matrix,
        "hints": hints,
        "constraints": [str(path) for path in CONSTRAINTS_DIR.glob("py*.txt")],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dependency Doctor")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run in verification mode (regenerates files and exits with diff status)",
    )
    parser.add_argument(
        "--wheelhouse-only",
        action="store_true",
        help="Rebuild wheels from the existing requirements lock without rewriting tracked files.",
    )
    args = parser.parse_args(argv)

    if args.check and args.wheelhouse_only:
        parser.error("--check and --wheelhouse-only cannot be combined")

    if args.wheelhouse_only:
        wheel_log, install_log = build_wheelhouse(REQUIREMENTS_TXT)
        print(
            json.dumps(
                {
                    "requirements": str(REQUIREMENTS_TXT),
                    "wheel_build": wheel_log.stdout or "",
                    "install_test": install_log.stdout or "",
                },
                indent=2,
            )
        )
        return 0

    result = generate()
    if args.check:
        diff = subprocess.run(["git", "diff", "--quiet"], check=False)
        return diff.returncode
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
