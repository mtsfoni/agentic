# Agentic Workflows

These are the OpenCode workflow components I currently use. They are not
perfect, but I keep refining them and share them in case they are useful to
someone else.

## Workflow

1. Optionally, `incident-analyst` examines logs and bug reports to reconstruct
   what happened. It records the investigation in an incident report that can
   be handed to `planner`.
2. `planner` plans a fix or a new feature. It asks questions and shares
   relevant implementation insights, then records the completed plan in a
   document for `builder` or `orchestrator` to implement.
3. `builder` implements work directly or as a subagent. `orchestrator` accepts
   a direct request or a written plan and hands each phase sequentially to a fresh builder,
   with a refactor checkpoint after every five implementation phases and for
   any remaining phases at the end. Final verification follows refactoring.
   It stops if a phase or checkpoint fails its checks.
4. When using GPT-5.6, `builder` can call `review-normal` itself after an
   implementation. I have not yet seen it call `review-deep`.

## Agents

From the parent checkout, deploy agents with an explicit model profile:

```sh
./agentic/install-agents.sh --profile personal
```

From this repository itself, use `./install-agents.sh --profile personal`.
Use `--profile work` on work machines. The installer writes model pins into the
installed Markdown frontmatter from `models-personal.jsonc` or `models-work.jsonc`;
source agents and global configuration are not modified. Launch OpenCode normally
after deployment; no `OPENCODE_CONFIG` variable is needed to select these models.

The destination is `${XDG_CONFIG_HOME:-$HOME/.config}/opencode/agents/`.
Set `OPENCODE_AGENT_DIR` to choose a different target. Profile deployment requires
Python 3 (standard library only). Profiles support JSONC comments and trailing
commas and must supply a provider/model ID for every source agent. Invalid profiles
fail before installing any agents. Authentication and model availability remain
machine-specific and are not checked by the installer.

Repeating the command overwrites the same source agent filenames; switching
profiles replaces their pins. Unrelated installed files are left alone. Run
`./install-agents.sh` without a profile to copy the unpinned source agents,
removing any previously installed profile pins. This retains the original
installation behavior and does not require Python. Restart OpenCode after
installing or updating agents.

Builder uses mode `all` (primary and subagent), with a focused implementation,
verification, and escalation prompt. `builder-fast` is subagent-only and handles
small, well-specified changes with limited autonomy. It returns blockers to its
parent and cannot delegate work or enter planning mode. `refactor` is subagent-only
and performs classical behavior-preserving cleanup of completed work, using
GPT-6.1 Sol in both model profiles. Orchestrator is primary-only and can delegate
only to builder and refactor.

A written plan is optional for orchestrator. For a direct request, it inspects
repository context and creates a small working outline in the conversation.
It asks questions only when requirements or consequential decisions are unclear;
it does not require a plan file before starting.

Refactor checkpoints improve naming, duplication, readability, and structure
within the completed work's scope; they do not add features or redesign the
architecture. A verified no-op is valid when no useful refactoring is needed.
For three implementation phases, refactor runs once at the end; for five, once
after phase five; for six, after phase five and again after phase six. Only
successful implementation phases count, and a checkpoint at the end is not
duplicated. All handoffs use fresh children and run sequentially, with final
verification performed by builder after refactoring.

To make builder the default and disable built-in build, merge these fields into
your OpenCode configuration after installing the agents:

```json
{
  "default_agent": "builder",
  "agent": {
    "build": { "disable": true }
  }
}
```

Preserve your other agents, permissions, MCP, plugin, and skill settings when
merging configuration. Agent installation alone does not change these fields.

## Deployment model profiles

Agent Markdown files define behavior, modes, and permissions without model pins.
Model choices live in tracked configuration profiles so forks can customize them:

| Profile | Implementation and coordination | Small review | Normal / deep review |
| --- | --- | --- | --- |
| [`models-work.jsonc`](models-work.jsonc) | OpenAI GPT-6.1 Sol; GPT-6 Luna for builder-fast | OpenAI GPT-6 Luna | Direct Anthropic Claude Sonnet 5.5 / Opus 5.5 |
| [`models-personal.jsonc`](models-personal.jsonc) | OpenAI GPT-6.1 Sol; GPT-6 Luna for builder-fast | OpenAI GPT-6 Luna | GitHub Copilot Claude Sonnet 5.5 / Opus 5.5 |

Both profiles explicitly map every public agent, including refactor, planner, and incident
analyst. Work models are starting defaults; edit the provider/model IDs to match
your deployment's access. Check available IDs with `opencode models` and configure
provider authentication separately on each machine.

For deployment, use the installer command above. Alternatively, install without
a profile and select one from the checkout at launch:

```sh
OPENCODE_CONFIG="/path/to/agentic/models-personal.jsonc" opencode --agent builder
```

Use `models-work.jsonc` at work. This launch-time profile merges with existing global
settings; it does not supply credentials or replace MCP, plugins, permissions, or
default-agent settings. Installation without `--profile` does not select models.
An agent omitted from a profile uses normal OpenCode model selection/inheritance.

To preview a profile and the repository agents without global installation, run
from this repository's root:

```sh
OPENCODE_CONFIG="$PWD/models-personal.jsonc" \
  OPENCODE_CONFIG_DIR="$PWD" opencode debug agent builder-fast
OPENCODE_CONFIG="$PWD/models-personal.jsonc" \
  OPENCODE_CONFIG_DIR="$PWD" opencode --agent builder
```

Model mappings can also be merged into each machine's global config instead of
using `OPENCODE_CONFIG`. When switching to either configuration-based approach,
reinstall without `--profile` first to remove installed model pins and avoid
competing model settings. Restart OpenCode after changing the selected profile
or agent definitions.

Installer checks run entirely in temporary directories:

```sh
python3 -B -m unittest discover -s tests -v
```

## Why Documents

The written handoffs should preserve the important context between stages so
compaction is ideally unnecessary. Compaction is expensive and often loses
information.
