#!/usr/bin/env python3
"""
Scrape Instagram profile stats for @keshavsuki
Uses Playwright to fetch public data without API
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/root/clawd/projects/sync2-content-hub/data")
OUTPUT_DIR.mkdir(exist_ok=True)

INSTAGRAM_HANDLE = "keshavsuki"

def scrape_instagram():
    """Scrape Instagram profile using playwright"""
    
    # Create a temporary JS file for playwright
    js_script = f'''
    const {{ chromium }} = require('playwright');
    
    (async () => {{
        const browser = await chromium.launch({{ headless: true }});
        const context = await browser.newContext({{
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }});
        const page = await context.newPage();
        
        try {{
            await page.goto('https://www.instagram.com/{INSTAGRAM_HANDLE}/', {{ 
                waitUntil: 'networkidle',
                timeout: 30000 
            }});
            
            // Wait for content to load
            await page.waitForTimeout(3000);
            
            // Get page content
            const content = await page.content();
            
            // Extract data from meta tags and page content
            const data = await page.evaluate(() => {{
                const result = {{}};
                
                // Get follower count from meta description
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc) {{
                    const desc = metaDesc.content;
                    const followerMatch = desc.match(/([\d,.]+[KMB]?)\s*Followers/i);
                    if (followerMatch) {{
                        result.followers = followerMatch[1];
                    }}
                    const followingMatch = desc.match(/([\d,.]+[KMB]?)\s*Following/i);
                    if (followingMatch) {{
                        result.following = followingMatch[1];
                    }}
                    const postsMatch = desc.match(/([\d,.]+[KMB]?)\s*Posts/i);
                    if (postsMatch) {{
                        result.posts = postsMatch[1];
                    }}
                }}
                
                // Try to get from page header stats
                const statElements = document.querySelectorAll('header section ul li');
                statElements.forEach(el => {{
                    const text = el.textContent || '';
                    if (text.includes('posts')) {{
                        const match = text.match(/([\d,.]+)/);
                        if (match) result.posts = match[1];
                    }}
                    if (text.includes('followers')) {{
                        const match = text.match(/([\d,.]+[KMB]?)/i);
                        if (match) result.followers = match[1];
                    }}
                    if (text.includes('following')) {{
                        const match = text.match(/([\d,.]+)/);
                        if (match) result.following = match[1];
                    }}
                }});
                
                // Get bio
                const bioEl = document.querySelector('header section > div.-vDIg span');
                if (bioEl) {{
                    result.bio = bioEl.textContent;
                }}
                
                // Get recent posts/reels
                const posts = [];
                const postLinks = document.querySelectorAll('article a[href*="/p/"], article a[href*="/reel/"]');
                postLinks.forEach((link, idx) => {{
                    if (idx < 12) {{
                        const href = link.getAttribute('href');
                        const img = link.querySelector('img');
                        const viewsEl = link.querySelector('span');
                        posts.push({{
                            url: 'https://instagram.com' + href,
                            type: href.includes('/reel/') ? 'reel' : 'post',
                            thumbnail: img ? img.src : null
                        }});
                    }}
                }});
                result.recentPosts = posts;
                
                return result;
            }});
            
            console.log(JSON.stringify(data, null, 2));
            
        }} catch (error) {{
            console.error(JSON.stringify({{ error: error.message }}));
        }} finally {{
            await browser.close();
        }}
    }})();
    '''
    
    # Write and execute
    script_path = OUTPUT_DIR / "temp_scrape.js"
    script_path.write_text(js_script)
    
    result = subprocess.run(
        ["node", str(script_path)],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    script_path.unlink()  # Clean up
    
    if result.returncode == 0 and result.stdout:
        try:
            data = json.loads(result.stdout)
            data['handle'] = INSTAGRAM_HANDLE
            data['scraped_at'] = datetime.utcnow().isoformat() + 'Z'
            return data
        except json.JSONDecodeError:
            print(f"Failed to parse: {result.stdout}")
            return None
    else:
        print(f"Error: {result.stderr}")
        return None


def save_data(data):
    """Save scraped data to JSON file"""
    if not data:
        return
    
    # Save latest
    latest_path = OUTPUT_DIR / "instagram_latest.json"
    latest_path.write_text(json.dumps(data, indent=2))
    
    # Append to history
    history_path = OUTPUT_DIR / "instagram_history.json"
    history = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text())
        except:
            history = []
    
    history.append(data)
    # Keep last 100 entries
    history = history[-100:]
    history_path.write_text(json.dumps(history, indent=2))
    
    print(f"Saved Instagram data: {data.get('followers', 'N/A')} followers")


if __name__ == "__main__":
    print(f"Scraping @{INSTAGRAM_HANDLE}...")
    data = scrape_instagram()
    if data:
        save_data(data)
        print(json.dumps(data, indent=2))
    else:
        print("Failed to scrape Instagram")
