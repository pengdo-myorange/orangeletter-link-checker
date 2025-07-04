#!/usr/bin/env python3
import requests
import time
import urllib.parse

# Test both local and production APIs
apis = {
    'local': 'http://localhost:8080/api/scrape',
    # Note: Add your Vercel production URL here if available
    # 'production': 'https://your-app.vercel.app/api/scrape'
}

test_urls = [
    'https://matching.impact.career/impactcareer/grantors/careers/epuOpL',
    'https://savethechildren.recruiter.co.kr/app/jobnotice/view?systemKindCode=MRS2&jobnoticeSn=220880',
    'https://gcs.or.kr/28/?idx=165644616&bmode=view'
]

def test_api_endpoint(api_name, api_url, test_url):
    try:
        encoded_url = urllib.parse.quote_plus(test_url)
        full_url = f"{api_url}?url={encoded_url}"
        
        start_time = time.time()
        response = requests.get(full_url, timeout=60)  # Longer timeout for API calls
        end_time = time.time()
        
        result = {
            'api': api_name,
            'test_url': test_url,
            'status': response.status_code,
            'time': end_time - start_time,
            'success': response.status_code == 200,
            'response_size': len(response.content) if response.content else 0
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                result['has_title'] = bool(data.get('title'))
                result['has_error'] = data.get('error', False)
                result['error_type'] = data.get('errorType', None)
            except:
                result['has_title'] = False
                result['has_error'] = True
                result['error_type'] = 'json_parse_error'
        else:
            result['has_title'] = False
            result['has_error'] = True
            result['error_type'] = f'http_{response.status_code}'
            
        return result
        
    except requests.exceptions.Timeout:
        return {
            'api': api_name,
            'test_url': test_url,
            'status': 'TIMEOUT',
            'time': 60,
            'success': False,
            'response_size': 0,
            'has_title': False,
            'has_error': True,
            'error_type': 'timeout'
        }
    except Exception as e:
        return {
            'api': api_name,
            'test_url': test_url,
            'status': f'ERROR: {e}',
            'time': 0,
            'success': False,
            'response_size': 0,
            'has_title': False,
            'has_error': True,
            'error_type': 'connection_error'
        }

def run_comparison_tests():
    print("=== API Comparison Testing ===")
    
    for api_name, api_url in apis.items():
        print(f"\n--- Testing {api_name.upper()} API: {api_url} ---")
        
        for i, test_url in enumerate(test_urls, 1):
            print(f"\nTest {i}: {test_url[:80]}...")
            result = test_api_endpoint(api_name, api_url, test_url)
            
            print(f"  Status: {result['status']}")
            print(f"  Time: {result['time']:.3f}s")
            print(f"  Success: {result['success']}")
            print(f"  Has Title: {result['has_title']}")
            print(f"  Has Error: {result['has_error']}")
            if result['error_type']:
                print(f"  Error Type: {result['error_type']}")
            print(f"  Response Size: {result['response_size']} bytes")
            
            time.sleep(1)  # Small delay between requests

def test_edge_cases():
    print("\n\n=== Testing Edge Cases ===")
    
    edge_case_urls = [
        # Non-existent URL
        'https://this-domain-does-not-exist-12345.com',
        # 404 page
        'https://httpbin.org/status/404',
        # Slow response (should be fast with httpbin)
        'https://httpbin.org/delay/2',
        # Large response
        'https://httpbin.org/html',
    ]
    
    for api_name, api_url in apis.items():
        print(f"\n--- Testing {api_name.upper()} API Edge Cases ---")
        
        for i, test_url in enumerate(edge_case_urls, 1):
            print(f"\nEdge Case {i}: {test_url}")
            result = test_api_endpoint(api_name, api_url, test_url)
            
            print(f"  Status: {result['status']}")
            print(f"  Time: {result['time']:.3f}s")
            print(f"  Success: {result['success']}")
            print(f"  Error Type: {result['error_type']}")
            
            time.sleep(1)

if __name__ == "__main__":
    run_comparison_tests()
    test_edge_cases()