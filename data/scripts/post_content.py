#!/usr/bin/env python3
"""
GitHub Actions Auto-Posting Script
Ke Aupuni O Ke Akua Press
"""
import csv
import os
from datetime import datetime
import requests

def load_config():
    """Load configuration from GitHub Secrets"""
    return {
        'facebook': {
            'page_id': os.getenv('FB_PAGE_ID'),
            'access_token': os.getenv('FB_ACCESS_TOKEN')
        },
        'linkedin': {
            'person_id': os.getenv('LI_PERSON_ID'),
            'access_token': os.getenv('LI_ACCESS_TOKEN')
        }
    }

def load_calendar():
    """Load posts from CSV"""
    posts = []
    if os.path.exists('data/content_calendar.csv'):
        with open('data/content_calendar.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                posts.append(row)
    return posts

def save_calendar(posts):
    """Save updated CSV"""
    headers = ['scheduled_date', 'post_text', 'platforms', 'image_url', 
               'link_url', 'hashtags', 'book_title', 'status']
    
    with open('data/content_calendar.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(posts)

def post_to_facebook(config, text, image_url, link):
    """Post to Facebook"""
    try:
        page_id = config['facebook']['page_id']
        token = config['facebook']['access_token']
        
        if not page_id or not token:
            return False, "Missing credentials"
        
        if image_url:
            url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
            payload = {'url': image_url, 'message': text, 'access_token': token}
        elif link:
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            payload = {'message': text, 'link': link, 'access_token': token}
        else:
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            payload = {'message': text, 'access_token': token}
        
        response = requests.post(url, data=payload, timeout=30)
        
        if response.status_code == 200:
            return True, "Posted"
        else:
            return False, response.json().get('error', {}).get('message', 'Error')
    except Exception as e:
        return False, str(e)

def post_to_linkedin(config, text, link):
    """Post to LinkedIn"""
    try:
        person_id = config['linkedin']['person_id']
        token = config['linkedin']['access_token']
        
        if not person_id or not token:
            return False, "Missing credentials"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        post_data = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE" if link else "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        
        if link:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "originalUrl": link
            }]
        
        response = requests.post("https://api.linkedin.com/v2/ugcPosts", 
                                headers=headers, json=post_data, timeout=30)
        
        if response.status_code in [200, 201]:
            return True, "Posted"
        else:
            return False, response.json().get('message', 'Error')
    except Exception as e:
        return False, str(e)

def main():
    """Check for posts due today and post them"""
    print("\n" + "="*70)
    print(f"🌺 Ke Aupuni O Ke Akua Press - Auto-Post")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*70 + "\n")
    
    config = load_config()
    calendar = load_calendar()
    today = datetime.now().date()
    posted_count = 0
    
    for i, post in enumerate(calendar):
        if post.get('status', '').lower() == 'posted':
            continue
        
        scheduled_date = post.get('scheduled_date', '').strip()
        if not scheduled_date:
            continue
        
        try:
            post_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
            
            if post_date <= today:
                print(f"\n📤 {post.get('book_title', 'General')}")
                print(f"   {post['post_text'][:60]}...")
                
                platforms = [p.strip() for p in post.get('platforms', '').split(',')]
                text = post['post_text']
                hashtags = post.get('hashtags', '').strip()
                
                if hashtags:
                    text = f"{text}\n\n{hashtags}"
                
                image_url = post.get('image_url', '').strip()
                link = post.get('link_url', '').strip()
                success = False
                
                for platform in platforms:
                    if platform.lower() == 'facebook':
                        result, msg = post_to_facebook(config, text, image_url, link)
                        print(f"   {'✅' if result else '❌'} Facebook: {msg}")
                        if result:
                            success = True
                    
                    elif platform.lower() == 'linkedin':
                        result, msg = post_to_linkedin(config, text, link)
                        print(f"   {'✅' if result else '❌'} LinkedIn: {msg}")
                        if result:
                            success = True
                
                if success:
                    calendar[i]['status'] = 'posted'
                    posted_count += 1
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    if posted_count > 0:
        save_calendar(calendar)
        print(f"\n✅ Posted {posted_count} item(s)\n")
    else:
        print(f"\n💤 No posts due today\n")

if __name__ == '__main__':
    main()
