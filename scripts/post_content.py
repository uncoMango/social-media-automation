#!/usr/bin/env python3
import csv
import os
from datetime import datetime
import requests

def load_config():
    return {
        'facebook': {
            'page_id': os.getenv('FB_PAGE_ID'),
            'access_token': os.getenv('FB_ACCESS_TOKEN')
        }
    }

def load_calendar():
    posts = []
    if os.path.exists('data/content_calendar.csv'):
        with open('data/content_calendar.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                posts.append(row)
    return posts

def save_calendar(posts):
    headers = ['scheduled_date', 'post_text', 'platforms', 'image_url', 
               'link_url', 'hashtags', 'book_title', 'status']
    with open('data/content_calendar.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(posts)

def post_to_facebook(config, text, image_url, link):
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

def main():
    print("\n" + "="*70)
    print(f"🌺 The Kingdom Revealed - Auto-Post")
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
