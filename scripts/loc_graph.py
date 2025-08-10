#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Generates an SVG chart of LOC over time using cloc per commit.
# Caches results in .github/loc_history.json to avoid recomputation.

import json
import os
import subprocess
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

    # Theme colors
    theme = os.environ.get("THEME", "light").lower()
    if theme == "dark":
        bg_color = "#0d1117"  # GitHub dark background
        grid_color = "#30363d"
        axis_color = "#30363d"  # Same as grid for consistency
        line_color = "#3fb950"  # Green
        text_color = "#c9d1d9"
        point_color = "#3fb950"
    else:
        bg_color = "white"
        grid_color = "#e5e7eb"
        axis_color = "#9ca3af"
        line_color = "#111827"
        text_color = "#111827"
        point_color = "#111827"

    xs = list(range(len(points)))
    ys = [p["loc"] for p in points]
    ymin = 0
    
    # Calculate nice round ymax first, before defining sy function
    def nice_round(n):
        """Round to nice numbers like 10, 25, 50, 100, 250, 500, 1000, etc."""
        if n <= 10:
            return 10
        magnitude = 10 ** (len(str(int(n))) - 1)
        normalized = n / magnitude
        if normalized <= 1:
            return magnitude
        elif normalized <= 2.5:
            return int(2.5 * magnitude)
        elif normalized <= 5:
            return 5 * magnitude
        else:
            return 10 * magnitude
    
    ymax = nice_round(max(ys) * 1.2) if max(ys) > 0 else 100

    def sx(i): return pad + i * (w - 2*pad) / max(1, len(xs)-1)
    def sy(v): return h - pad - (v - ymin) * (h - 2*pad) / (ymax - ymin)

    path = "M " + " L ".join(f"{sx(i):.2f} {sy(ys[i]):.2f}" for i in range(len(xs)))

    # X grid with dates
    x_grid = []
    date_labels = []
    
    # Determine date format based on whether dates repeat
    dates_only = [p["date"][:10] for p in points]
    use_time = len(dates_only) != len(set(dates_only))  # Show time if dates repeat
    
    # Add vertical lines and date labels for each point
    for i, point in enumerate(points):
        x = sx(i)
        # Vertical grid line
        x_grid.append(f'<line x1="{x:.2f}" y1="{pad}" x2="{x:.2f}" y2="{h-pad}" stroke="{grid_color}" opacity="0.5"/>')
        
        # Date label (rotate for better fit)
        if use_time:
            label = point["date"][11:16]  # Show HH:MM if dates repeat
        else:
            label = point["date"][5:10]  # Show MM-DD
        
        # Only show every Nth label if too crowded (more than 10 points)
        if len(points) <= 10 or i % max(1, len(points) // 10) == 0:
            date_labels.append(f'<text x="{x:.2f}" y="{h-pad+15:.2f}" font-size="9" fill="{text_color}" text-anchor="middle" transform="rotate(-45 {x:.2f} {h-pad+15:.2f})">{label}</text>')

    # Y grid - Generate grid with nice tick values
    def format_number(n):
        """Format numbers: 1000 -> 1k, 1000000 -> 1M"""
        if n >= 1000000:
            return f"{n/1000000:.0f}M" if n % 1000000 == 0 else f"{n/1000000:.1f}M"
        elif n >= 1000:
            return f"{n/1000:.0f}k" if n % 1000 == 0 else f"{n/1000:.1f}k"
        else:
            return str(n)
    
    grid = []
    for i in range(6):
        val = int(ymax * i / 5)
        y = sy(val)
        grid.append(f'<line x1="{pad}" y1="{y:.2f}" x2="{w-pad}" y2="{y:.2f}" stroke="{grid_color}"/>')
        grid.append(f'<text x="{pad-8}" y="{y+4:.2f}" font-size="10" fill="{text_color}" text-anchor="end">{format_number(val)}</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h+30}" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;">
  <rect width="100%" height="100%" fill="{bg_color}"/>
  <g>
    {''.join(x_grid)}
    {''.join(grid)}
    <line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="{axis_color}"/>
    <line x1="{pad}" y1="{pad}"   x2="{pad}"   y2="{h-pad}" stroke="{axis_color}"/>
    <path d="{path}" fill="none" stroke="{line_color}" stroke-width="2"/>
    <circle cx="{sx(len(xs)-1):.2f}" cy="{sy(ys[-1]):.2f}" r="3" fill="{point_color}"/>
    {''.join(date_labels)}
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
