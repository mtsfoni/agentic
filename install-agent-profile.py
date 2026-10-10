"""Render a model profile into staged Markdown; called by install-agents.sh."""

import json
from pathlib import Path
import re
import sys


STRING = r'"(?:[^"\\]|\\.)*"'


def load_profile(path):
    # Keep strings intact while removing JSONC comments and trailing commas.
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        STRING + r'|//[^\r\n]*|/\*.*?\*/',
        lambda match: match[0] if match[0].startswith('"') else " ",
        text, flags=re.DOTALL)
    text = re.sub(
        STRING + r'|,\s*(?=[}\]])',
        lambda match: match[0] if match[0].startswith('"') else "",
        text)
    profile = json.loads(text)
    if not isinstance(profile, dict) or not isinstance(profile.get("agent"), dict):
        raise ValueError("profile must contain an agent object")
    return profile["agent"]


def render(source, model):
    text = source.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[3:]:
        raise ValueError(f"{source.name}: expected Markdown YAML frontmatter")
    header, body = text[4:].split("\n---\n", 1)
    # Source agents are unpinned. Refuse accidental pins rather than producing
    # duplicate YAML keys or silently overriding a fork's multiline model value.
    if re.search(r"^model\s*:", header, flags=re.MULTILINE):
        raise ValueError(f"{source.name}: remove the source model pin; use the profile")
    return f"---\nmodel: {json.dumps(model)}\n{header}\n---\n{body}"


def main():
    profile_path, source_dir, staging_dir = map(Path, sys.argv[1:])
    agents = load_profile(profile_path)
    sources = sorted(source_dir.glob("*.md"))
    if not sources:
        raise ValueError(f"no agent Markdown files in {source_dir}")
    rendered = {}
    for source in sources:
        entry = agents.get(source.stem)
        model = entry.get("model") if isinstance(entry, dict) else None
        if (not isinstance(model, str) or
                not re.fullmatch(r"[^/\s]+/[^\s]+", model)):
            raise ValueError(f"{source.stem}: profile requires a provider/model ID")
        rendered[source.name] = render(source, model)
    # Validate every agent before writing anything, even to staging.
    for name, text in rendered.items():
        (staging_dir / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Error: cannot prepare agent profile: {error}", file=sys.stderr)
        sys.exit(1)
