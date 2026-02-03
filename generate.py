import os
from datetime import datetime

# Ensure posts folder exists
os.makedirs("posts", exist_ok=True)

trend_name = "npc-livestream-test"
title = "NPC livestreams are still pulling insane numbers"

content = f"""
<html>
<head>
  <title>{title}</title>
</head>
<body>
  <h1>{title}</h1>
  <p><strong>Why this is trending:</strong></p>
  <p>People know it's repetitive, people know it's dumb, but somehow
  NPC livestreams keep pulling millions of views across platforms.</p>

  <p><strong>AI take:</strong></p>
  <pre>
everyone said they'd stop watching
nobody actually did
the internet wins again
  </pre>

  <p><em>Auto-posted at {datetime.utcnow()} UTC</em></p>
</body>
</html>
"""

filename = f"posts/{trend_name}-{int(datetime.utcnow().timestamp())}.html"

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Created post: {filename}")
