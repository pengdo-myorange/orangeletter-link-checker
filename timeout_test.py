#!/usr/bin/env python3
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Test URLs
test_urls = [
    'https://matching.impact.career/impactcareer/grantors/careers/epuOpL',
    'https://savethechildren.recruiter.co.kr/app/jobnotice/view?systemKindCode=MRS2&jobnoticeSn=220880',
    'https://gcs.or.kr/28/?idx=165644616&bmode=view'
]

def test_single_request(url, timeout):
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        end_time = time.time()
        
        return {
            'url': url,
            'timeout': timeout,
            'status': response.status_code,
            'time': end_time - start_time,
            'success': True,
            'size': len(response.content)
        }
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'timeout': timeout,
            'status': 'TIMEOUT',
            'time': timeout,
            'success': False,
            'size': 0
        }
    except Exception as e:
        return {
            'url': url,
            'timeout': timeout,
            'status': f'ERROR: {e}',
            'time': 0,
            'success': False,
            'size': 0
        }

def test_timeout_performance():
    print("=== Testing different timeout values ===")
    timeouts = [5, 10, 15, 30, 45]
    
    for timeout in timeouts:
        print(f"\n--- Testing with {timeout}s timeout ---")
        results = []
        
        for url in test_urls:
            result = test_single_request(url, timeout)
            results.append(result)
            print(f"URL: {url[:60]}...")
            print(f"  Status: {result['status']}, Time: {result['time']:.3f}s, Success: {result['success']}")
        
        successful_times = [r['time'] for r in results if r['success']]
        if successful_times:
            print(f"Summary - Timeout: {timeout}s, Success rate: {len(successful_times)}/{len(results)}")
            print(f"  Avg time: {statistics.mean(successful_times):.3f}s")
            print(f"  Max time: {max(successful_times):.3f}s")

def test_concurrent_requests():
    print("\n\n=== Testing concurrent requests (simulating high load) ===")
    
    def make_request(url_index):
        url = test_urls[url_index % len(test_urls)]
        return test_single_request(url, 45)
    
    # Test with different concurrency levels
    for concurrency in [1, 5, 10]:
        print(f"\n--- Testing with {concurrency} concurrent requests ---")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request, i) for i in range(concurrency * 3)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"Total time: {end_time - start_time:.3f}s")
        print(f"Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
        
        if successful:
            times = [r['time'] for r in successful]
            print(f"Avg response time: {statistics.mean(times):.3f}s")
            print(f"Max response time: {max(times):.3f}s")
        
        if failed:
            print(f"Failures: {[r['status'] for r in failed]}")

if __name__ == "__main__":
    test_timeout_performance()
    test_concurrent_requests()