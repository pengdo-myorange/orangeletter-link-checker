from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

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
            
            # Bedrock Claude 사용 시도
            try:
                import boto3
                
                # Bedrock 클라이언트 생성
                client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name='us-east-1',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
                
                # 프롬프트 생성
                prompt = f"""오렌지레터 뉴스레터의 링크들을 분석해주세요.

링크 목록:
{json.dumps(links, ensure_ascii=False, indent=2)}

각 링크에 대해 다음 정보를 JSON 형식으로 제공해주세요:
1. suggested_text: 카테고리별 규칙에 맞는 이상적인 링크 텍스트
2. accuracy: 현재 텍스트의 정확도 점수 (0-100)
3. issues: 개선이 필요한 사항들 (배열)
4. key_info: 링크에서 추출한 핵심 정보 (제목, 주최자, 기간, 장소 등)

카테고리별 링크 텍스트 규칙:
- job (채용): [회사명] 직군 채용 (경력구분, 마감일)
- funding (펀딩/캠페인): 프로젝트명 펀딩 (~마감일)
- education (교육/모임): [주최] 프로그램명 (장소, 날짜)
- contest (공모/지원): 공모전명 (~마감일)
- event (행사): [주최] 행사명 (장소, 기간)

JSON 형식으로만 응답해주세요."""

                # Bedrock API 호출
                request_body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "top_p": 0.9
                })
                
                bedrock_response = client.invoke_model(
                    modelId="anthropic.claude-3-haiku-20240307-v1:0",
                    body=request_body,
                    contentType='application/json'
                )
                
                response_body = json.loads(bedrock_response['body'].read())
                content = response_body.get('content', [{}])[0].get('text', '{}')
                
                # JSON 파싱 시도
                result = None
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 텍스트에서 JSON 부분 추출
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        result = {"error": "Failed to parse AI response", "raw": content}
                
                # 응답 전송
                response_data = json.dumps(result, ensure_ascii=False)
                self.send_header('Content-Length', str(len(response_data.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(response_data.encode('utf-8'))
                
            except Exception as e:
                error_response = json.dumps({
                    "error": f"Bedrock API error: {str(e)}"
                }, ensure_ascii=False)
                self.send_header('Content-Length', str(len(error_response.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(error_response.encode('utf-8'))
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            error_response = json.dumps({"error": str(e)})
            self.send_header('Content-Length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())