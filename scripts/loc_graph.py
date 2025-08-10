#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Generates an SVG chart of LOC over time using cloc per commit.
# Caches results in .github/loc_history.json to avoid recomputation.

import json
import os
import shutil
import subprocess
from datetime import datetime

# Fixed paths to match action.yml defaults
OUTPUT_SVG_FALLBACK = ".github/loc-history.svg"
OUTPUT_SVG_LIGHT = ".github/loc-history-light.svg"
OUTPUT_SVG_DARK = ".github/loc-history-dark.svg"
OUTPUT_JSON = ".github/loc_history.json"

# Directories commonly excluded from LOC counts
DEFAULT_EXCLUDE = [".git", ".github"]

def get_exclude_dirs():
    """Get exclude directories from environment or use defaults."""
    exclude_env = os.environ.get("EXCLUDE", "")
    if not exclude_env:
        return DEFAULT_EXCLUDE

    # Split by comma and strip whitespace
    custom_excludes = [dir.strip() for dir in exclude_env.split(",") if dir.strip()]
    return DEFAULT_EXCLUDE + custom_excludes

def sh(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def run(cmd):
    subprocess.check_call(cmd)

def cloc_code_lines():
    """Return SUM.code from cloc JSON output."""
    # Build --exclude-dir list
    exclude_dirs = get_exclude_dirs()
    exclude = "--exclude-dir=" + ",".join(exclude_dirs)
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

def nice_round(n):
    """Round up to nice numbers like 10, 20, 50, 100, 200, 300, 500, 1000, etc."""
    if n <= 0:
        return 10
    
    # Nice round numbers sequence
    steps = [1, 2, 3, 5, 10]
    
    # Find magnitude (10, 100, 1000, etc)
    magnitude = 10 ** (len(str(int(n))) - 1)
    
    # Find the nice number
    for step in steps:
        nice = step * magnitude
        if n <= nice:
            return nice
    
    # If nothing fits, go to next magnitude
    return 10 * magnitude

def format_number(n):
    """Format numbers: 1000 -> 1k, 1000000 -> 1M"""
    if n >= 1000000:
        return f"{n/1000000:.0f}M" if n % 1000000 == 0 else f"{n/1000000:.1f}M"
    elif n >= 1000:
        return f"{n/1000:.0f}k" if n % 1000 == 0 else f"{n/1000:.1f}k"
    else:
        return str(n)

def generate_svg(points, output_path, theme="light", w=900, h=260, pad=40, title="Lines of code over time"):
    """Write simple static SVG line chart to output_path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not points:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><text x="12" y="24">No data</text></svg>'
        open(output_path, "w", encoding="utf-8").write(svg)
        return

    # Theme colors
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
    # Round up the max value to next nice number, ensuring some padding
    max_val = max(ys) if max(ys) > 0 else 100
    
    # First, get the nice round number at or above max_val
    ymax = nice_round(max_val)
    
    # If max_val equals ymax (exact match), we need the next level
    # Otherwise check if we're using more than 80%
    if max_val == ymax or max_val > ymax * 0.8:
        # Find the next nice number in the sequence
        # Add a small increment to ensure we get the next level
        ymax = nice_round(ymax * 1.1 + 1)

    def sx(i): return pad + i * (w - 2*pad) / max(1, len(xs)-1)
    def sy(v): return h - pad - (v - ymin) * (h - 2*pad) / (ymax - ymin)

    path = "M " + " L ".join(f"{sx(i):.2f} {sy(ys[i]):.2f}" for i in range(len(xs)))

    # X grid with dates
    x_grid = []
    date_labels = []
    
    # Get date/time formats from environment
    date_format = os.environ.get("DATE_FORMAT", "%d.%m.%Y")
    time_format = os.environ.get("TIME_FORMAT", "%H:%M")
    
    # Determine if project spans multiple days
    first_date = datetime.fromisoformat(points[0]["date"]).date()
    last_date = datetime.fromisoformat(points[-1]["date"]).date()
    use_time = (last_date - first_date).days <= 2  # Use time for projects ≤2 days
    
    # Add vertical lines and date labels for selected points
    for i, point in enumerate(points):
        # Only show every Nth line and label if too crowded (more than 10 points)
        if len(points) <= 10 or i % max(1, len(points) // 10) == 0:
            x = sx(i)
            # Vertical grid line
            x_grid.append(f'<line x1="{x:.2f}" y1="{pad}" x2="{x:.2f}" y2="{h-pad}" stroke="{grid_color}" opacity="0.5"/>')
            
            # Format date label
            dt = datetime.fromisoformat(point["date"])
            label = dt.strftime(time_format if use_time else date_format)
            
            date_labels.append(f'<text x="{x:.2f}" y="{h-pad+15:.2f}" font-size="9" fill="{text_color}" text-anchor="middle" transform="rotate(-45 {x:.2f} {h-pad+15:.2f})">{label}</text>')

    # Y grid - Generate grid with nice tick values
    grid = []
    for i in range(6):
        val = int(ymax * i / 5)
        y = sy(val)
        grid.append(f'<line x1="{pad}" y1="{y:.2f}" x2="{w-pad}" y2="{y:.2f}" stroke="{grid_color}"/>')
        grid.append(f'<text x="{pad-8}" y="{y+4:.2f}" font-size="10" fill="{text_color}" text-anchor="end">{format_number(val)}</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h+30}" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;">
  <rect width="100%" height="100%" fill="{bg_color}"/>
  <g>
    {''.join(grid)}
    {''.join(x_grid)}
    <line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="{axis_color}"/>
    <line x1="{pad}" y1="{pad}"   x2="{pad}"   y2="{h-pad}" stroke="{axis_color}"/>
    <path d="{path}" fill="none" stroke="{line_color}" stroke-width="2"/>
    <circle cx="{sx(len(xs)-1):.2f}" cy="{sy(ys[-1]):.2f}" r="3" fill="{point_color}"/>
    {''.join(date_labels)}
  </g>
</svg>'''
    open(output_path, "w", encoding="utf-8").write(svg)

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
    if updated or not os.path.exists(OUTPUT_SVG_LIGHT) or not os.path.exists(OUTPUT_SVG_DARK):
        save_history(hist)
        generate_svg(hist, OUTPUT_SVG_LIGHT, theme="light")
        generate_svg(hist, OUTPUT_SVG_DARK, theme="dark")
        
        # Copy appropriate theme to fallback for backward compatibility
        fallback_theme = os.environ.get("FALLBACK_THEME", "light").lower()
        source_svg = OUTPUT_SVG_DARK if fallback_theme == "dark" else OUTPUT_SVG_LIGHT
        shutil.copy(source_svg, OUTPUT_SVG_FALLBACK)

if __name__ == "__main__":
    main()
