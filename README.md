# LOC Graph Action

[![Tests](https://github.com/botforge-pro/loc-graph-action/actions/workflows/test.yml/badge.svg)](https://github.com/botforge-pro/loc-graph-action/actions/workflows/test.yml)

GitHub Action that analyzes your repository's commit history, counts lines of code (LOC) for each commit using `cloc`, and generates an SVG chart showing LOC changes over time.  
The SVG and a JSON cache are committed back to the repository automatically, so you can embed the chart directly in your README.

## Usage

In the repository where you want the LOC chart:

1. Create a workflow file `.github/workflows/loc-graph.yml`:

```yaml
name: LOC graph

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-loc-graph:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout full history
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate LOC graph
        uses: botforge-pro/loc-graph-action@main
```

### Trigger Options

You can trigger the graph generation in different ways:

- **On every push** (shown above) - Updates immediately after commits
- **Daily via cron** - Add `schedule` to run once per day to save Actions minutes
- **Manual only** - Keep only `workflow_dispatch` for on-demand generation

**Note:** Each graph update creates a new commit. For actively developed projects, using cron is recommended to avoid cluttering history with automated commits.

For less active repos, daily updates are recommended:
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:      # Allow manual triggers
```

2.	Commit and push the workflow file.
3.	After the workflow runs, the generated files will appear:
   * .github/loc-history-light.svg — SVG chart for light theme
   * .github/loc-history-dark.svg — SVG chart for dark theme
   * .github/loc-history.svg — Fallback SVG for backward compatibility
   * .github/loc_history.json — cached LOC data	
 4.	Embed the SVG in your README.md with automatic theme switching:
```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/loc-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/loc-history-light.svg">
  <img src=".github/loc-history-light.svg" alt="Lines of code over time">
</picture>
```

## Configuration Options

All inputs are optional:

| Input | Description | Default |
|-------|-------------|---------|
| `output_json` | Path to cached LOC history JSON | `.github/loc_history.json` |
| `fallback_theme` | Theme for fallback SVG: `light` or `dark` | `light` |
| `date_format` | Date format for multi-day projects (Python strftime) | `%d.%m.%Y` |
| `time_format` | Time format for same-day commits (Python strftime) | `%H:%M` |

### Example with all options:

```yaml
- name: Generate LOC graph
  uses: botforge-pro/loc-graph-action@main
  with:
    output_json: "docs/data/loc-cache.json"
    fallback_theme: dark  # Theme for .github/loc-history.svg
    date_format: "%Y-%m-%d"  # 2024-03-15
    time_format: "%I:%M %p"  # 03:45 PM
```

## Example

This repository uses its own action to track LOC over time:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/loc-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/loc-history-light.svg">
  <img src=".github/loc-history-light.svg" alt="Lines of code over time">
</picture>
