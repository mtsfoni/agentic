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
   document for the default `build` agent to implement.
3. The default `build` agent implements the plan. I may add an orchestration
   agent here later.
4. When using GPT-5.6, `build` can call `review-normal` itself after an
   implementation. I have not yet seen it call `review-deep`.

## Why Documents

The written handoffs should preserve the important context between stages so
compaction is ideally unnecessary. Compaction is expensive and often loses
information.
