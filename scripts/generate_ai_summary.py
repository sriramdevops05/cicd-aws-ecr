#!/usr/bin/env python3
"""
generate_ai_summary.py
──────────────────────
Uses OpenAI GPT-4o to generate:
  1. A structured deployment summary (Markdown)
  2. Human-readable release notes

Reads pipeline context from environment variables set by GitHub Actions.
Outputs two Markdown files to reports/.
"""

import os
import sys
import json
import datetime
from pathlib import Path
from openai import OpenAI

# ── Output directory ────────────────────────────────────────────────────────
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# ── Collect pipeline context ────────────────────────────────────────────────
def collect_context() -> dict:
    """Gather all pipeline metadata from environment variables."""
    security_findings = ""
    security_path = REPORTS_DIR / "trivy-results.txt"
    if security_path.exists():
        content = security_path.read_text()
        # Limit to first 2000 chars to stay within token budget
        security_findings = content[:2000] + ("..." if len(content) > 2000 else "")

    return {
        "pipeline": {
            "repository":      os.getenv("REPO", "unknown/repo"),
            "branch":          os.getenv("BRANCH", "unknown"),
            "commit_sha":      os.getenv("COMMIT_SHA", "unknown")[:12],
            "triggered_by":    os.getenv("ACTOR", "unknown"),
            "run_url":         os.getenv("RUN_URL", "#"),
            "timestamp":       datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        },
        "job_results": {
            "build":           os.getenv("PIPELINE_STATUS_BUILD", "unknown"),
            "security_scan":   os.getenv("PIPELINE_STATUS_SECURITY", "unknown"),
            "ecr_push":        os.getenv("PIPELINE_STATUS_PUSH", "unknown"),
        },
        "image": {
            "tag":             os.getenv("IMAGE_TAG", "unknown"),
            "ecr_uri":         os.getenv("ECR_IMAGE_URI", "not-available"),
        },
        "changes": {
            "recent_commits":  os.getenv("COMMIT_MESSAGES", "No commit messages available"),
            "changed_files":   os.getenv("CHANGED_FILES", "No file changes available"),
        },
        "security_findings":   security_findings or "No security report available.",
    }

# ── Build the prompt ────────────────────────────────────────────────────────
def build_summary_prompt(ctx: dict) -> str:
    return f"""You are a senior DevOps engineer writing deployment documentation.
Analyze the following CI/CD pipeline execution and produce a structured deployment summary.

## Pipeline Execution Data
```json
{json.dumps(ctx, indent=2)}
```

## Instructions
Write a professional, concise deployment summary in Markdown. Include:

1. **Executive Summary** — 2-3 sentences on overall pipeline outcome.
2. **Pipeline Status Table** — a table with Job, Status (use), and Notes columns.
3. **Docker Image Details** — ECR URI, image tag, build timestamp.
4. **Security Assessment** — brief analysis of Trivy findings; flag CRITICAL/HIGH issues.
5. **Changes Deployed** — summarize recent commits and changed files in plain English.
6. **Recommendations** — 2-4 actionable suggestions for the team (e.g., dependency updates, test coverage, security fixes).
7. **Next Steps** — what automated checks or manual steps should follow.

Keep the tone professional but developer-friendly. Use emoji sparingly. Output only the Markdown, no preamble.
"""

def build_release_notes_prompt(ctx: dict) -> str:
    return f"""You are a technical writer generating release notes for an engineering team.

## Commit Messages (last 10)
{ctx['changes']['recent_commits']}

## Changed Files
{ctx['changes']['changed_files']}

## Image
{ctx['image']['ecr_uri']}

## Instructions
Generate clear, user-friendly release notes in Markdown. Structure:

### What's New
- Bullet list of new features or improvements inferred from commits.

### Bug Fixes
- Bullet list of bug fixes (if any, otherwise omit section).

### Internal / Infrastructure Changes
- Bullet list of infra, CI/CD, or dependency changes.

###Breaking Changes
- Any breaking changes (if none, say "None").

###Deployment
- Docker image: `{ctx['image']['ecr_uri']}`
- Deployed at: `{ctx['pipeline']['timestamp']}`
- Commit: `{ctx['pipeline']['commit_sha']}`

Keep it concise. Infer intent from commit messages. Output only the Markdown, no preamble.
"""

# ── Call OpenAI ──────────────────────────────────────────────────────────────
def call_openai(client: OpenAI, prompt: str, label: str) -> str:
    print(f"Generating {label}...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert DevOps engineer and technical writer. "
                        "You produce clear, accurate, and actionable documentation. "
                        "Always output valid Markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.3,  # Lower temperature → more deterministic/professional output
        )
        content = response.choices[0].message.content
        print(f" {label} generated ({len(content)} chars)")
        return content
    except Exception as e:
        print(f" Failed to generate {label}: {e}", file=sys.stderr)
        return f"## AI Summary Unavailable\n\nError: `{e}`\n"

# ── Write header ─────────────────────────────────────────────────────────────
def write_header(ctx: dict) -> str:
    status_emoji = {
        "success": "",
        "failure": "",
        "skipped": "",
        "unknown": "",
    }
    build_icon   = status_emoji.get(ctx["job_results"]["build"],         "")
    sec_icon     = status_emoji.get(ctx["job_results"]["security_scan"], "")
    push_icon    = status_emoji.get(ctx["job_results"]["ecr_push"],      "")
    overall = "SUCCESS" if all(
        v == "success" for v in ctx["job_results"].values()
    ) else "FAILED"

    return f"""#AI Deployment Summary — {overall}

> **Generated by GPT-4o** | {ctx['pipeline']['timestamp']}
> **Run:** [{ctx['pipeline']['repository']}]({ctx['pipeline']['run_url']}) · `{ctx['pipeline']['branch']}` · `{ctx['pipeline']['commit_sha']}`

| Job | Status |
|-----|--------|
| Docker Build | {build_icon} {ctx['job_results']['build'].upper()} |
| Security Scan | {sec_icon} {ctx['job_results']['security_scan'].upper()} |
| ECR Push | {push_icon} {ctx['job_results']['ecr_push'].upper()} |

---

"""

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set. Skipping AI summary generation.", file=sys.stderr)
        fallback = "## AI Summary Unavailable\n\nOPENAI_API_KEY secret is not configured.\n"
        (REPORTS_DIR / "ai-summary.md").write_text(fallback)
        (REPORTS_DIR / "release-notes.md").write_text(fallback)
        sys.exit(0)  # Don't fail the pipeline for missing AI key

    client = OpenAI(api_key=api_key)
    ctx = collect_context()

    print("📋 Pipeline context collected:")
    print(f"   Repo:   {ctx['pipeline']['repository']}")
    print(f"   Branch: {ctx['pipeline']['branch']}")
    print(f"   Commit: {ctx['pipeline']['commit_sha']}")
    print(f"   Jobs:   {ctx['job_results']}")

    # Generate both documents
    header       = write_header(ctx)
    summary_body = call_openai(client, build_summary_prompt(ctx),        "Deployment Summary")
    release_body = call_openai(client, build_release_notes_prompt(ctx),  "Release Notes")

    # Write outputs
    summary_path      = REPORTS_DIR / "ai-summary.md"
    release_path      = REPORTS_DIR / "release-notes.md"

    summary_path.write_text(header + summary_body)
    release_path.write_text(
        f"# Release Notes\n\n"
        f"> Commit `{ctx['pipeline']['commit_sha']}` · {ctx['pipeline']['timestamp']}\n\n"
        + release_body
    )

    print(f"\nReports written:")
    print(f"   {summary_path}")
    print(f"   {release_path}")

if __name__ == "__main__":
    main()
