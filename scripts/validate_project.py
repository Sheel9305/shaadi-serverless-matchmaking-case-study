"""Static checks for the whole repository. Uses only the standard library plus PyYAML.

Checks:
  1. Required files exist (expected repository structure)
  2. Every Python file compiles
  3. Backend modules import (app, lambda_handler, ...)
  4. Every JSON file parses; the dataset is flagged synthetic
  5. YAML (SAM template, with CloudFormation tags) and TOML parse
  6. Mermaid sources are non-empty and start with a diagram type
  7. Relative links in Markdown files point to files that exist
  8. Secret / credential scan (AWS keys, private keys, tokens, passwords)

Usage:  python scripts/validate_project.py
Exit code 0 = all checks passed.
"""

from __future__ import annotations

import json
import py_compile
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    ".aws-sam",
}

REQUIRED = """
README.md LICENSE .gitignore requirements.txt START_HERE.md TEAM_TASKS.md CONTRIBUTION_MATRIX.md GITHUB_WORKFLOW.md
research/week1_summary.md research/sources.md research/salient_points.md
docs/01_project_overview.md docs/02_case_study_analysis.md docs/03_real_world_architecture.md
docs/04_student_architecture.md docs/05_exercise_plan.md docs/06_deployment_guide.md
docs/07_testing_and_experiments.md docs/08_cost_analysis.md docs/09_team_contributions.md docs/10_viva_questions.md
docs/diagrams/case_study_overview.mmd docs/diagrams/student_architecture.mmd docs/diagrams/request_flow.mmd
docs/diagrams/recommendation_flow.mmd docs/diagrams/deployment_architecture.mmd docs/diagrams/testing_workflow.mmd
docs/diagrams/github_workflow.mmd docs/diagrams/project_timeline.mmd
backend/src/app.py backend/src/lambda_handler.py backend/src/models.py backend/src/validation.py
backend/src/recommendation_service.py backend/src/repository.py backend/src/logging_utils.py
backend/src/requirements.txt backend/src/data/sample_profiles.json
backend/tests/test_models.py backend/tests/test_validation.py backend/tests/test_recommendation.py
backend/tests/test_handler.py backend/tests/test_api.py backend/tests/test_edge_cases.py
infrastructure/template.yaml infrastructure/samconfig.toml infrastructure/README.md
frontend/index.html frontend/style.css frontend/script.js frontend/config.js
experiments/k6/load_test.js experiments/k6/scenarios.js experiments/configs/scenarios.json
experiments/configs/cost_inputs.json experiments/results/README.md experiments/results/cloud_results_template.csv
experiments/analysis/analyze_results.py experiments/analysis/generate_charts.py experiments/analysis/collect_results.py
experiments/analysis/cost_model.py experiments/run_local_benchmark.py
reports/README.md reports/report_outline.md presentation/presentation_outline.md
test_reports/validation_summary.md
scripts/run_tests.sh scripts/run_tests.ps1 scripts/validate_project.py scripts/generate_diagrams.sh
""".split()

# Patterns are assembled from pieces so this file does not flag itself.
SECRET_PATTERNS = {
    "AWS access key ID": re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    "AWS secret key assignment": re.compile(r"aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}", re.I),
    "Private key block": re.compile("-----BEGIN " + r"(RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Generic password assignment": re.compile(
        r"\b(password|passwd|secret|api_key)\s*[=:]\s*['\"][^'\"\s]{8,}['\"]", re.I
    ),
}
TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".json",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".html",
    ".css",
    ".sh",
    ".ps1",
    ".mmd",
    ".csv",
    ".ini",
    ".cfg",
    ".env",
}
MERMAID_STARTS = ("flowchart", "graph", "sequenceDiagram", "gantt", "gitGraph", "classDiagram", "stateDiagram")


class CfnLoader(yaml.SafeLoader):
    """SafeLoader that accepts CloudFormation short-form tags like !Ref and !Sub."""


def _cfn_tag(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return {tag_suffix: loader.construct_scalar(node)}
    if isinstance(node, yaml.SequenceNode):
        return {tag_suffix: loader.construct_sequence(node)}
    return {tag_suffix: loader.construct_mapping(node)}


CfnLoader.add_multi_constructor("!", _cfn_tag)


def iter_files(suffixes: set[str] | None = None):
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.is_file() and (suffixes is None or path.suffix in suffixes or path.name in suffixes):
            yield path


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, name: str, problems: list[str], detail: str = "") -> None:
        if problems:
            self.failures.extend(f"[{name}] {p}" for p in problems)
            print(f"FAIL  {name}: {len(problems)} problem(s)")
            for p in problems[:20]:
                print(f"        - {p}")
        else:
            print(f"PASS  {name}{' - ' + detail if detail else ''}")


def check_required() -> list[str]:
    return [f"missing {p}" for p in REQUIRED if not (ROOT / p).exists()]


def check_compile() -> tuple[list[str], int]:
    problems, count = [], 0
    for path in iter_files({".py"}):
        count += 1
        try:
            py_compile.compile(str(path), doraise=True, cfile=None)
        except py_compile.PyCompileError as exc:
            problems.append(f"{path.relative_to(ROOT)}: {exc.msg}")
    return problems, count


def check_imports() -> list[str]:
    code = (
        "import sys; sys.path.insert(0, 'backend/src');"
        "import app, lambda_handler, models, validation, recommendation_service, repository, logging_utils;"
        "print('ok')"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    return [] if result.returncode == 0 else [result.stderr.strip().splitlines()[-1]]


def check_json() -> tuple[list[str], int]:
    problems, count = [], 0
    for path in iter_files({".json"}):
        count += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if path.name == "sample_profiles.json" and data.get("synthetic") is not True:
            problems.append("sample_profiles.json must be flagged synthetic: true")
    return problems, count


def check_yaml_toml() -> tuple[list[str], int]:
    problems, count = [], 0
    for path in iter_files({".yaml", ".yml"}):
        count += 1
        try:
            doc = yaml.load(path.read_text(encoding="utf-8"), Loader=CfnLoader)  # noqa: S506 - SafeLoader subclass
        except yaml.YAMLError as exc:
            problems.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if path.name == "template.yaml":
            fn = doc["Resources"]["RecommendationFunction"]["Properties"]
            if fn["Handler"] != "lambda_handler.handler":
                problems.append("template.yaml Handler must be lambda_handler.handler")
            if not (path.parent / fn["CodeUri"] / "lambda_handler.py").exists():
                problems.append(f"template.yaml CodeUri {fn['CodeUri']} does not contain lambda_handler.py")
            routes = {(e["Properties"]["Method"], e["Properties"]["Path"]) for e in fn["Events"].values()}
            if routes != {("GET", "/health"), ("POST", "/recommendations")}:
                problems.append(f"template.yaml routes mismatch: {routes}")
    for path in iter_files({".toml"}):
        count += 1
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            problems.append(f"{path.relative_to(ROOT)}: {exc}")
    return problems, count


def check_mermaid() -> tuple[list[str], int]:
    problems, count = [], 0
    for path in sorted((ROOT / "docs" / "diagrams").glob("*.mmd")):
        count += 1
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
        body = [ln for ln in lines if ln and not ln.startswith("%%")]
        if not body or not body[0].startswith(MERMAID_STARTS):
            problems.append(f"{path.name}: does not start with a Mermaid diagram type")
    return problems, count


LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")


def check_links() -> tuple[list[str], int]:
    problems, count = [], 0
    for path in iter_files({".md"}):
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        for match in LINK_RE.finditer(text):
            target = match.group(1) or match.group(2)
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            count += 1
            file_part = target.split("#")[0]
            if file_part and not (path.parent / file_part).resolve().exists():
                problems.append(f"{path.relative_to(ROOT)} -> {target}")
    return problems, count


def check_secrets() -> tuple[list[str], int]:
    problems, count = [], 0
    for path in iter_files(TEXT_SUFFIXES):
        if path.name == "validate_project.py":
            continue
        count += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{path.relative_to(ROOT)}: possible {name}")
    for bad in (".env", "credentials", ".aws/credentials"):
        if (ROOT / bad).exists():
            problems.append(f"credential file present in repo: {bad}")
    return problems, count


def main() -> int:
    report = Report()
    report.check("required files", check_required(), f"{len(REQUIRED)} present")
    probs, n = check_compile()
    report.check("python compile", probs, f"{n} files")
    report.check("backend imports", check_imports(), "7 modules")
    probs, n = check_json()
    report.check("json parse", probs, f"{n} files")
    probs, n = check_yaml_toml()
    report.check("yaml/toml parse + SAM consistency", probs, f"{n} files")
    probs, n = check_mermaid()
    report.check("mermaid sources", probs, f"{n} diagrams")
    probs, n = check_links()
    report.check("markdown relative links", probs, f"{n} links")
    probs, n = check_secrets()
    report.check("secret scan", probs, f"{n} files scanned")
    print()
    if report.failures:
        print(f"{len(report.failures)} problem(s) found.")
        return 1
    print("All project validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
