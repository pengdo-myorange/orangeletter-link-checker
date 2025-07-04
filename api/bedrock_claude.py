import json
import boto3
import os
from typing import List, Dict, Any

class BedrockClaude:
    def __init__(self):
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def analyze_links_batch(self, links: List[Dict[str, Any]]) -> Dict[str, Any]:
        """여러 링크를 한 번에 분석"""
        
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

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
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
                }),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [{}])[0].get('text', '{}')
            
            # JSON 파싱 시도
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트에서 JSON 부분 추출
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"error": "Failed to parse response", "raw": content}
                    
        except Exception as e:
            print(f"Bedrock API error: {str(e)}")
            return {"error": str(e)}
    
    def extract_page_info(self, url: str, html_content: str) -> Dict[str, Any]:
        """단일 페이지의 정보를 추출"""
        
        prompt = f"""다음 웹페이지의 HTML에서 정보를 추출해주세요.

URL: {url}

HTML (첫 5000자):
{html_content[:5000]}

다음 정보를 JSON 형식으로 추출해주세요:
- title: 페이지 제목
- organizer: 주최자/회사명
- period: 기간/마감일
- location: 장소 (온라인/오프라인)
- target: 대상
- description: 간단한 설명
- keywords: 관련 키워드 배열

JSON 형식으로만 응답해주세요."""

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1
                }),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [{}])[0].get('text', '{}')
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "title": "",
                    "organizer": "",
                    "period": "",
                    "location": "",
                    "target": "",
                    "description": "",
                    "keywords": []
                }
                
        except Exception as e:
            print(f"Bedrock API error: {str(e)}")
            return None