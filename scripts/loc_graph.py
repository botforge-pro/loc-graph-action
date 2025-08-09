#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Generates an SVG chart of LOC over time using cloc per commit.
# Caches results in .github/loc_history.json to avoid recomputation.

import json, os, subprocess
from datetime import datetime

# Fixed paths to match action.yml defaults
OUTPUT_SVG = ".github/loc-history.svg"
OUTPUT_JSON = ".github/loc_history.json"

# Directories commonly excluded from LOC counts
EXCLUDE_DIRS = [".git", ".github"]

def sh(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def run(cmd):
    subprocess.check_call(cmd)

def cloc_code_lines():
    """Return SUM.code from cloc JSON output."""
    # Build --exclude-dir list
    exclude = "--exclude-dir=" + ",".join(EXCLUDE_DIRS)
    out = sh(["cloc", "--json", "--quiet", exclude, "."])
    data = json.loads(out)
    return int(data.get("SUM", {}).get("code", 0))

def get_commits():
    """Return list of (sha, iso8601) oldest -> newest."""
    lines = sh(["git", "log", "--format=%H %cI", "--reverse"]).splitlines()
    return [tuple(line.split(" ", 1)) for line in lines]

def load_history():
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(hist):
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)

def generate_svg(points, w=900, h=260, pad=40, title="Lines of code over time"):
    """Write simple static SVG line chart to OUTPUT_SVG."""
    os.makedirs(os.path.dirname(OUTPUT_SVG), exist_ok=True)
    if not points:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><text x="12" y="24">No data</text></svg>'
        open(OUTPUT_SVG, "w", encoding="utf-8").write(svg)
        return

    xs = list(range(len(points)))
    ys = [p["loc"] for p in points]
    ymin, ymax = 0, max(ys) or 1

    def sx(i): return pad + i * (w - 2*pad) / max(1, len(xs)-1)
    def sy(v): return h - pad - (v - ymin) * (h - 2*pad) / (ymax - ymin)

    path = "M " + " L ".join(f"{sx(i):.2f} {sy(ys[i]):.2f}" for i in range(len(xs)))

    # Y grid (6 ticks)
    grid = []
    for t in range(6):
        val = int(ymin + t*(ymax - ymin)/5)
        y = sy(val)
        grid.append(f'<line x1="{pad}" y1="{y:.2f}" x2="{w-pad}" y2="{y:.2f}" stroke="#e5e7eb"/>')
        grid.append(f'<text x="{pad-8}" y="{y+4:.2f}" font-size="10" text-anchor="end">{val}</text>')

    last = points[-1]
    last_label = f'{last["date"][:10]} · {last["loc"]} LOC'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="white"/>
  <g>
    <line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#9ca3af"/>
    <line x1="{pad}" y1="{pad}"   x2="{pad}"   y2="{h-pad}" stroke="#9ca3af"/>
    {''.join(grid)}
    <path d="{path}" fill="none" stroke="#111827" stroke-width="2"/>
    <circle cx="{sx(len(xs)-1):.2f}" cy="{sy(ys[-1]):.2f}" r="3" fill="#111827"/>
  </g>
</svg>'''
    open(OUTPUT_SVG, "w", encoding="utf-8").write(svg)

def main():
    current_ref = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    commits = get_commits()
    hist = load_history()
    done = {e["sha"] for e in hist}
    updated = False

    try:
        for sha, date in commits:
            if sha in done:
                continue
            # Checkout each commit, run cloc, then append
            run(["git", "checkout", "--quiet", sha])
            loc = cloc_code_lines()
            hist.append({"sha": sha, "date": date, "loc": loc})
            updated = True
    finally:
        run(["git", "checkout", "--quiet", current_ref])

    hist.sort(key=lambda e: datetime.fromisoformat(e["date"]))
    if updated or not os.path.exists(OUTPUT_SVG):
        save_history(hist)
        generate_svg(hist)

if __name__ == "__main__":
    main()
