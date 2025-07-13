# InsightMate Agents

| Agent | Responsibility |
|-------|---------------|
| Planner | Map user requests to a list of tool actions. Outputs a JSON array describing those actions. |
| Executor | Run the planned actions using Gmail, Calendar and other integrations. Collects the results for the final reply. |
| Summarizer | Shortens long email or calendar data using the currently selected language model. |

**One line contract for the planner:** Output a JSON array of actions. Each object **must** use the key `type` to specify the tool (never `tool` or `action`). No commentary or `<think>` tags.
