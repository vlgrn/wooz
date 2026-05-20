### 1. Plan mode by default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- If something goes sideways, STOP and re-plan immediately — don't keep pushing.
- Use plan mode for verification, not just building.
- Write detailed specs upfront to reduce ambiguity.

### 2. Subagents liberally
- Offload research, exploration, parallel analysis to subagents — keep the main context clean.
- One task per subagent for focused execution.
- For complex problems, throw more compute via parallel subagents.

### 3. Self-improvement loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern.
- Write rules for yourself that prevent the same mistake.
- Iterate ruthlessly until mistake rate drops.
- Review `tasks/lessons.md` at the start of each session.

### 4. Verification before "done"
- Never mark a task complete without proving it works.
- Run tests, check logs, demonstrate correctness.
- Diff behavior between main and your changes when relevant.
- Ask: "Would a staff engineer approve this?"

### 5. Demand elegance (balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: redo it knowing what you now know.
- Skip this for simple, obvious fixes — don't over-engineer.
- Challenge your own work before presenting it.

### 6. Autonomous bug fixing
- Given a bug report: just fix it. Don't ask for hand-holding.
- Point at logs, errors, failing tests → resolve them.
- Zero context switching required from the user.

## Task management

- Use the harness's built-in `TodoWrite` tool for in-conversation task tracking — do **not** write planning to a `tasks/todo.md` file.
- Use plan mode (or a written spec in the conversation) for non-trivial work; verify the plan with the user before implementing.
- Mark TodoWrite items complete as you go; give a short high-level summary at each step.
- After corrections from the user, update `tasks/lessons.md` so the same mistake isn't repeated.

## Core principles

- **Simplicity first.** Every change as simple as possible. Touch minimal code.
- **No laziness.** Find root causes. No temporary fixes. Senior-developer standard.
- **Minimal impact.** Changes only touch what's necessary. Don't introduce bugs in unrelated areas.
