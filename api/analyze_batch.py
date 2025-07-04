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

모든 링크를 분석하여 URL을 키로 하는 JSON 객체로 응답해주세요.
각 링크에 대해 다음 정보를 포함해야 합니다:

{{
  "링크URL1": {{
    "suggested_text": "카테고리별 규칙에 맞는 이상적인 링크 텍스트",
    "accuracy": 0-100 사이의 정확도 점수,
    "issues": ["개선사항1", "개선사항2"],
    "key_info": {{
      "title": "제목",
      "organizer": "주최자/회사명",
      "period": "기간/마감일",
      "location": "장소",
      "target": "대상"
    }}
  }},
  "링크URL2": {{ ... }}
}}

카테고리별 링크 텍스트 규칙:
- job (채용): [회사명] 직군 채용 (경력구분, 마감일)
- funding (펀딩/캠페인): 프로젝트명 펀딩 (~마감일)
- education (교육/모임): [주최] 프로그램명 (장소, 날짜)
- contest (공모/지원): 공모전명 (~마감일)
- event (행사): [주최] 행사명 (장소, 기간)

중요: 반드시 모든 링크를 분석하고, URL을 키로 하는 단일 JSON 객체로 응답하세요."""

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
                
                # 응답이 이미 올바른 형식인지 확인
                if isinstance(result, dict) and not result.get('error'):
                    # URL이 키인 딕셔너리 형태로 되어 있는지 확인
                    formatted_result = result
                else:
                    # 에러가 있거나 형식이 잘못된 경우
                    formatted_result = {}
                    for link in links:
                        formatted_result[link['url']] = {
                            'suggested_text': link['text'],
                            'accuracy': 0,
                            'issues': ['AI 분석 실패'],
                            'key_info': {
                                'title': 'Unknown',
                                'organizer': 'Unknown',
                                'period': 'Unknown'
                            }
                        }
                
                # 응답 전송
                response_data = json.dumps(formatted_result, ensure_ascii=False)
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