#!/bin/bash
# Update Instagram data for Sync2 Content Hub

INSTAGRAM_USER_ID="25854064164252098"
ACCESS_TOKEN="IGAAbSDMre2ttBZAGJ6cFhYUkVKVU5NWlhRWFRiWVo2bmVNNjhsdEs0MDJ6RUxiNVV4WlJteVF3bE9Ba3ZAwTXhLMUloXzFfdXlaWkdGVTZA2VlJ3ejZAVN2xFUTdCbXh5MnFnM29UdVYxNG9HYVJjRmVWRWhTMG84am5pTHBqNmo0QQZDZD"
OUTPUT_FILE="/root/clawd/projects/sync2-content-hub/api/instagram.json"
TEMP_DIR="/tmp/instagram-sync"

mkdir -p "$TEMP_DIR"

# Fetch data from Instagram API
curl -s "https://graph.instagram.com/v18.0/${INSTAGRAM_USER_ID}/media?fields=id,caption,media_type,like_count,comments_count,timestamp,permalink&limit=20&access_token=${ACCESS_TOKEN}" > "$TEMP_DIR/data.json"

# Get account info
curl -s "https://graph.instagram.com/v18.0/${INSTAGRAM_USER_ID}?fields=id,username,account_type,media_count&access_token=${ACCESS_TOKEN}" > "$TEMP_DIR/account.json"

# Parse and create JSON
python3 << 'EOF'
import json
from datetime import datetime
import os

temp_dir = "/tmp/instagram-sync"

with open(f"{temp_dir}/data.json") as f:
    data = json.load(f)

with open(f"{temp_dir}/account.json") as f:
    account = json.load(f)

# Check for API errors
if 'error' in data:
    print(f"API Error: {data['error'].get('message', 'Unknown error')}")
    exit(1)

posts = []
total_likes = 0
total_comments = 0
top_post = None

for item in data.get('data', []):
    caption = item.get('caption', '')
    post = {
        'id': item.get('id'),
        'caption': (caption[:60] + '...') if len(caption) > 60 else caption,
        'type': item.get('media_type'),
        'likes': item.get('like_count', 0),
        'comments': item.get('comments_count', 0),
        'timestamp': item.get('timestamp'),
        'url': item.get('permalink')
    }
    posts.append(post)
    total_likes += post['likes']
    total_comments += post['comments']
    
    if top_post is None or post['likes'] > top_post['likes']:
        top_post = post

output = {
    'lastUpdated': datetime.utcnow().isoformat() + 'Z',
    'account': {
        'username': account.get('username'),
        'id': account.get('id'),
        'accountType': account.get('account_type'),
        'mediaCount': account.get('media_count')
    },
    'posts': posts,
    'stats': {
        'totalLikes': total_likes,
        'totalComments': total_comments,
        'avgLikes': round(total_likes / len(posts), 1) if posts else 0,
        'avgComments': round(total_comments / len(posts), 1) if posts else 0,
        'topPost': top_post
    }
}

output_file = os.environ.get('OUTPUT_FILE', '/root/clawd/projects/sync2-content-hub/api/instagram.json')
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Updated {len(posts)} posts. Total likes: {total_likes}")
EOF

# Commit and push if there are changes
cd /root/clawd/projects/sync2-content-hub
git add api/instagram.json
git diff --cached --quiet || (git commit -m "Update Instagram data $(date +%Y-%m-%d)" && git push origin master)
