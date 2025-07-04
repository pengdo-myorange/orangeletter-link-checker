from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# 상위 디렉토리의 모듈을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bedrock_claude import BedrockClaude
    bedrock_available = True
except ImportError:
    bedrock_available = False

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # CORS 헤더 설정
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            # POST 데이터 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            links = data.get('links', [])
            
            # Vercel 환경변수 확인
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            
            if not bedrock_available:
                error_response = json.dumps({
                    "error": "Bedrock Claude module not available"
                }, ensure_ascii=False)
                self.send_header('Content-Length', str(len(error_response.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(error_response.encode('utf-8'))
                return
            
            if not aws_access_key or not aws_secret_key:
                error_response = json.dumps({
                    "error": "AWS credentials not configured in environment variables"
                }, ensure_ascii=False)
                self.send_header('Content-Length', str(len(error_response.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(error_response.encode('utf-8'))
                return
            
            if not links:
                error_response = json.dumps({
                    "error": "No links provided"
                }, ensure_ascii=False)
                self.send_header('Content-Length', str(len(error_response.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(error_response.encode('utf-8'))
                return
            
            # Bedrock Claude 인스턴스 생성
            bedrock_claude = BedrockClaude()
            
            # 링크 분석 수행
            analysis_results = bedrock_claude.analyze_links_batch(links)
            
            # 응답 전송
            response_data = json.dumps(analysis_results, ensure_ascii=False)
            self.send_header('Content-Length', str(len(response_data.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(response_data.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            error_response = json.dumps({"error": str(e)})
            self.send_header('Content-Length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()