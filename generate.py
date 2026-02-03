import os
from datetime import datetime

POSTS_DIR = "posts"
os.makedirs(POSTS_DIR, exist_ok=True)

# Create a test post
slug = f"npc-livestream-{int(datetime.utcnow().timestamp())}"
post_filename = f"{slug}.html"
post_path = os.path.join(POSTS_DIR, post_filename)

post_html = f"""
<html>
<head>
  <title>NPC livestreams are still pulling insane numbers</title>
</head>
<body>
  <h1>NPC livestreams are still pulling insane numbers</h1>

  <p><strong>Why it’s trending:</strong></p>
  <p>
    People know it’s repetitive, people know it’s dumb,
    but NPC livestreams keep pulling millions of views.
  </p>

  <pre>
everyone said they'd stop watching
nobody actually did
the internet wins again
  </pre>

  <p><em>Auto-posted at {datetime.utcnow()} UTC</em></p>

  <p><a href="./index.html">← Back to all posts</a></p>
</body>
</html>
"""

with open(post_path, "w", encoding="utf-8") as f:
    f.write(post_html)

# Build posts index
links = []
for file in sorted(os.listdir(POSTS_DIR), reverse=True):
    if file.endswith(".html") and file != "index.html":
        links.append(f'<li><a href="{file}">{file}</a></li>')

index_html = f"""
<html>
<head>
  <title>Trend Bot – Posts</title>
</head>
<body>
  <h1>🔥 Trend Bot – Auto Posts</h1>
  <ul>
    {''.join(links)}
  </ul>

  <p><a href="../index.html">← Home</a></p>
</body>
</html>
"""

with open(os.path.join(POSTS_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

print("Post and index generated successfully")
