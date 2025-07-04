#!/usr/bin/env python3
import requests
import time
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def test_url(url, test_num):
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=45, allow_redirects=True)
        end_time = time.time()
        
        print(f'Test {test_num}: Status {response.status_code}, Time {end_time - start_time:.3f}s')
        
        if response.status_code != 200:
            print(f'  Error response: {response.text[:200]}')
        else:
            # Quick check for common issues
            soup = BeautifulSoup(response.content, 'html.parser')
            body_text = soup.get_text()
            if '자동등록방지를 위해 보안절차를 거치고 있습니다' in body_text:
                print('  WARNING: Security verification page detected')
            if 'Access Denied' in body_text or 'Forbidden' in body_text:
                print('  WARNING: Access denied detected')
            if 'Too Many Requests' in body_text or 'Rate limit' in body_text:
                print('  WARNING: Rate limiting detected')
            
    except Exception as e:
        print(f'Test {test_num}: ERROR - {e}')

# Test rapid requests to the first URL
url = 'https://matching.impact.career/impactcareer/grantors/careers/epuOpL'
print('=== Testing rapid requests (simulating high load) ===')
print(f'URL: {url}')

# Send 10 rapid requests
for i in range(10):
    test_url(url, i+1)
    time.sleep(0.1)  # Small delay to avoid overwhelming

print('\n=== Testing with longer delays ===')
# Test with longer delays
for i in range(5):
    test_url(url, i+1)
    time.sleep(2)  # 2 second delay

print('\n=== Testing different URLs ===')
urls = [
    'https://matching.impact.career/impactcareer/grantors/careers/epuOpL',
    'https://savethechildren.recruiter.co.kr/app/jobnotice/view?systemKindCode=MRS2&jobnoticeSn=220880',
    'https://gcs.or.kr/28/?idx=165644616&bmode=view'
]

for i, url in enumerate(urls, 1):
    print(f'Testing URL {i}: {url}')
    test_url(url, 1)
    time.sleep(1)