#!/usr/bin/env python3
import requests
import time

# Test different user agents to see if some sites block certain bots
user_agents = [
    # Current one used in scrape.py
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # More recent Chrome
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    # Windows Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    # Generic requests
    'python-requests/2.31.0',
    # Empty user agent
    '',
]

test_url = 'https://matching.impact.career/impactcareer/grantors/careers/epuOpL'

def test_user_agent(user_agent, url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    if user_agent:
        headers['User-Agent'] = user_agent
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        end_time = time.time()
        
        return {
            'user_agent': user_agent or 'None',
            'status': response.status_code,
            'time': end_time - start_time,
            'content_length': len(response.content),
            'success': True
        }
    except Exception as e:
        return {
            'user_agent': user_agent or 'None',
            'status': f'ERROR: {e}',
            'time': 0,
            'content_length': 0,
            'success': False
        }

print("=== Testing different User-Agent strings ===")
print(f"URL: {test_url}")
print()

for i, ua in enumerate(user_agents, 1):
    result = test_user_agent(ua, test_url)
    print(f"Test {i}:")
    print(f"  User-Agent: {ua[:60]}{'...' if len(ua) > 60 else ''}")
    print(f"  Status: {result['status']}")
    print(f"  Time: {result['time']:.3f}s")
    print(f"  Content Length: {result['content_length']}")
    print(f"  Success: {result['success']}")
    print()
    time.sleep(1)  # Small delay between tests