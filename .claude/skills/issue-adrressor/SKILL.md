---
name: issue-addressor
description: Analyze GitHub issues and create PRs to address them. Takes a list of issue numbers and handles analysis, branching, commits, and PR creation.
arguments: [issues]
disable-model-invocation: true
allowed-tools: Bash Grep
---

## Address GitHub Issues

Process the following issues: $issues

For each issue:

- Analyze the issue summary and determine the best approach
- Create a new branch (issue-{number})
- Make commits addressing the changes
- Push and create a PR linked to the issue
- Merge and close the issue

See [template.md](template.md) for PR output format.
