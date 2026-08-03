import base64
from pathlib import Path

def icon(name, size=20):
    path = Path("assets/icons") / f"{name}.svg"
    svg = path.read_text()
    b64 = base64.b64encode(svg.encode()).decode()
    return f"""
    <img
        src="data:image/svg+xml;base64,{b64}"
        width="{size}"
        height="{size}"
        style="vertical-align:middle;margin-right:8px;"
    />
    """