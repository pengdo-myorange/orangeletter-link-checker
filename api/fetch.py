#!/usr/bin/env python3
import json
import requests
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        path_parts = self.path.split('?')
        if len(path_parts) > 1:
            query_params = parse_qs(path_parts[1])
            url = query_params.get('url', [None])[0]
            
            if url:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
                    }
                    response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)  # Vercel Pro: 10s -> 30s
                    response.raise_for_status()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    self.wfile.write(response.content)
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    error_response = json.dumps({'error': str(e)})
                    self.wfile.write(error_response.encode())
                    return
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = json.dumps({'error': 'URL parameter is required'})
                self.wfile.write(error_response.encode())
                return
        
        self.send_response(400)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()