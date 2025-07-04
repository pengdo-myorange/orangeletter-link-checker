#!/usr/bin/env python3
import http.server
import json
import os
import re
import socketserver
import webbrowser
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Bedrock Claude if available
try:
    from bedrock_claude import BedrockClaude

    bedrock_claude = BedrockClaude() if os.environ.get("AWS_ACCESS_KEY_ID") else None
except ImportError:
    bedrock_claude = None

PORT = 8080


class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)

        # Bedrock Claude batch analysis endpoint
        if parsed_path.path == "/api/analyze-batch":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode("utf-8"))
                links = data.get("links", [])

                if bedrock_claude and links:
                    # Use Bedrock Claude for batch analysis
                    analysis_results = bedrock_claude.analyze_links_batch(links)

                    response_data = json.dumps(analysis_results, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(response_data.encode("utf-8"))
                else:
                    error_response = json.dumps(
                        {"error": "Bedrock Claude not configured or no links provided"}
                    )
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(error_response.encode())
            except Exception as e:
                error_response = json.dumps({"error": str(e)})
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(error_response.encode())
            return

        # Default to parent implementation
        super().do_POST()

    def do_GET(self):
        parsed_path = urlparse(self.path)

        # API 엔드포인트 처리
        if parsed_path.path == "/api/fetch":
            query_params = parse_qs(parsed_path.query)
            url = query_params.get("url", [None])[0]

            if url:
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1"
                    }
                    response = requests.get(url, headers=headers, timeout=45, allow_redirects=True)  # 로컬: 30s -> 45s
                    response.raise_for_status()

                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(response.content)
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    error_response = json.dumps({"error": str(e)})
                    self.wfile.write(error_response.encode())
                    return
            else:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                error_response = json.dumps({"error": "URL parameter is required"})
                self.wfile.write(error_response.encode())
                return

        # API 엔드포인트 처리
        elif parsed_path.path == "/api/scrape":
            query_params = parse_qs(parsed_path.query)
            url = query_params.get("url", [None])[0]

            if url:
                try:
                    # 특정 사이트에 대한 특별 처리
                    if "forms.gle" in url or "docs.google.com/forms" in url:
                        # Google Forms는 JavaScript 렌더링 필요
                        page_info = {
                            "title": "Google Form",
                            "description": "구글 폼 신청서",
                            "organizer": "Google Forms",
                            "period": "확인 필요",
                            "location": "온라인",
                            "target": "확인 필요",
                            "keywords": ["신청", "폼"],
                            "error": False,
                            "note": "구글 폼은 직접 방문이 필요합니다"
                        }
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        response_data = json.dumps(page_info, ensure_ascii=False)
                        self.wfile.write(response_data.encode("utf-8"))
                        return
                    
                    # KOICA 사이트의 특별 처리 (로그인 필요)
                    if "job.koica.go.kr" in url:
                        page_info = {
                            "title": "KOICA 채용공고",
                            "description": "KOICA 채용공고 상세페이지",
                            "organizer": "KOICA",
                            "period": "확인 필요",
                            "location": "확인 필요",
                            "target": "확인 필요",
                            "keywords": ["채용", "KOICA"],
                            "error": False,
                            "note": "KOICA 사이트는 로그인이 필요합니다. 브라우저에서 직접 확인해주세요.",
                            "site_name": "job.koica.go.kr"
                        }
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        response_data = json.dumps(page_info, ensure_ascii=False)
                        self.wfile.write(response_data.encode("utf-8"))
                        return
                    
                    # thepromise.or.kr 사이트의 특별 처리
                    if "thepromise.or.kr" in url:
                        # 메타 정보에서 제목 추출 시도
                        try:
                            simple_headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            }
                            response = requests.get(url, headers=simple_headers, timeout=10)
                            content = response.text
                            
                            # 제목 추출
                            title_match = re.search(r'<title>([^<]+)</title>', content)
                            title = title_match.group(1) if title_match else "더프라미스 공지사항"
                            
                            # 더프라미스 관련 키워드로 판단
                            if "KOICA" in title or "YP" in title or "영프로패셔널" in title:
                                page_info = {
                                    "title": title.split('>')[0].strip(),
                                    "description": "KOICA 개발협력 사업 영프로패셔널(YP) 모집 공고",
                                    "organizer": "더프라미스",
                                    "period": "확인 필요",
                                    "location": "해외파견",
                                    "target": "청년",
                                    "keywords": ["채용", "KOICA", "YP"],
                                    "error": False,
                                    "note": "자세한 내용은 사이트에서 직접 확인하세요"
                                }
                            else:
                                page_info = {
                                    "title": title.split('>')[0].strip(),
                                    "description": "더프라미스 공지사항",
                                    "organizer": "더프라미스",
                                    "period": "확인 필요",
                                    "location": "확인 필요",
                                    "target": "확인 필요",
                                    "keywords": ["공지"],
                                    "error": False,
                                    "note": "보안 검증이 필요한 페이지입니다"
                                }
                            
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json; charset=utf-8")
                            self.end_headers()
                            response_data = json.dumps(page_info, ensure_ascii=False)
                            self.wfile.write(response_data.encode("utf-8"))
                            return
                        except:
                            # 실패 시 일반적인 처리로 진행
                            pass
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1"
                    }
                    response = requests.get(url, headers=headers, timeout=45, allow_redirects=True)  # 로컬: 30s -> 45s
                    
                    # 404 페이지인지 먼저 확인
                    if response.status_code == 404:
                        page_info = {
                            "title": "페이지를 찾을 수 없음",
                            "description": "요청한 페이지가 존재하지 않습니다",
                            "organizer": "Unknown",
                            "period": "Unknown",
                            "location": "Unknown",
                            "target": "Unknown",
                            "keywords": ["error"],
                            "error": True,
                            "errorType": "http",
                            "errorCode": 404,
                            "errorMessage": "HTTP 404 오류 (페이지를 찾을 수 없음)"
                        }
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.end_headers()
                        response_data = json.dumps(page_info, ensure_ascii=False)
                        self.wfile.write(response_data.encode("utf-8"))
                        return
                    
                    response.raise_for_status()

                    soup = BeautifulSoup(response.content, "html.parser")
                    
                    # 보안 검증 페이지 확인
                    body_text = soup.get_text()
                    if "자동등록방지를 위해 보안절차를 거치고 있습니다" in body_text:
                        # HTML 메타 정보에서 기본 정보 추출 시도
                        meta_title = soup.find("title")
                        if meta_title and meta_title.string:
                            extracted_title = meta_title.string.strip()
                            # 제목에서 핵심 정보 추출
                            main_title = extracted_title.split('>')[0].strip()
                            
                            page_info = {
                                "title": main_title,
                                "description": "보안 검증이 필요한 페이지입니다",
                                "organizer": "확인 필요",
                                "period": "확인 필요",
                                "location": "확인 필요",
                                "target": "확인 필요",
                                "keywords": ["보안검증"],
                                "error": False,
                                "note": "이 페이지는 보안 검증이 필요합니다. 브라우저에서 직접 확인해주세요.",
                                "site_name": urlparse(url).netloc
                            }
                            
                            # 도메인별 추가 정보
                            if "thepromise.or.kr" in url:
                                page_info["organizer"] = "더프라미스"
                                if "KOICA" in main_title or "YP" in main_title:
                                    page_info["keywords"] = ["채용", "KOICA"]
                                    page_info["target"] = "청년"
                                    page_info["location"] = "해외파견"
                            
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json; charset=utf-8")
                            self.end_headers()
                            response_data = json.dumps(page_info, ensure_ascii=False)
                            self.wfile.write(response_data.encode("utf-8"))
                            return

                    # 페이지 정보 추출 개선
                    title = ""
                    # 제목 추출 우선순위: og:title > title > h1 > h2
                    og_title = soup.find("meta", property="og:title")
                    if og_title:
                        title = og_title.get("content", "").strip()
                    elif soup.title:
                        title = soup.title.string.strip() if soup.title.string else ""
                    elif soup.find("h1"):
                        title = soup.find("h1").get_text().strip()
                    elif soup.find("h2"):
                        title = soup.find("h2").get_text().strip()

                    # 설명 추출
                    description = ""
                    og_desc = soup.find("meta", property="og:description")
                    meta_desc = soup.find("meta", attrs={"name": "description"})
                    if og_desc:
                        description = og_desc.get("content", "").strip()
                    elif meta_desc:
                        description = meta_desc.get("content", "").strip()

                    # 본문에서 추가 정보 추출
                    body_text = soup.get_text()

                    # 주최자 정보 추출 (맥락 고려 개선)
                    organizer = "Unknown Organizer"

                    # 1. 메타 데이터에서 추출
                    org_meta = soup.find("meta", attrs={"name": "author"})
                    if org_meta and org_meta.get("content"):
                        organizer = org_meta.get("content").strip()[:50]
                    else:
                        # 2. 패턴 매칭으로 추출
                        organizer_patterns = [
                            r"주최[:：]\s*([^\n\r\|]+)",
                            r"주관[:：]\s*([^\n\r\|]+)",
                            r"발행[:：]\s*([^\n\r\|]+)",
                            r"운영[:：]\s*([^\n\r\|]+)",
                            r"기관[:：]\s*([^\n\r\|]+)",
                            r"단체[:：]\s*([^\n\r\|]+)",
                            r"회사[:：]\s*([^\n\r\|]+)",
                            r"by\s+([^\n\r\|]+)",
                            r"©\s*([^\n\r\|]+)",
                            r"ⓒ\s*([^\n\r\|]+)",
                        ]
                        for pattern in organizer_patterns:
                            match = re.search(pattern, body_text, re.IGNORECASE)
                            if match:
                                candidate = match.group(1).strip()
                                # 의미있는 길이의 텍스트만 채택
                                if 2 <= len(candidate) <= 50 and not re.match(
                                    r"^\d+$", candidate
                                ):
                                    organizer = candidate
                                    break

                    # 3. URL에서 도메인 정보로 유추
                    if organizer == "Unknown Organizer":
                        domain_mapping = {
                            "habitat.careers.team": "해비타트",
                            "koica.go.kr": "KOICA",
                            "msf.or.kr": "국경없는의사회",
                            "concern.or.kr": "컨선월드와이드",
                            "globalcare.or.kr": "굿네이버스",
                            "asannanum.career.greetinghr.com": "아산나눔재단",
                            "saramin.co.kr": "사람인",
                            "happybean.naver.com": "네이버 해피빈",
                            "cherry.charity": "체리",
                            "socialfunch.org": "소셜펀치",
                        }
                        for domain, name in domain_mapping.items():
                            if domain in url:
                                organizer = name
                                break

                    # 기간 정보 추출 (맥락 고려 개선)
                    period = "Unknown Period"

                    # 1. 구조화된 데이터에서 추출 (JSON-LD, OpenGraph 등)
                    json_ld = soup.find("script", type="application/ld+json")
                    if json_ld:
                        try:
                            data = json.loads(json_ld.string)
                            if "startDate" in data and "endDate" in data:
                                period = f"{data['startDate']} ~ {data['endDate']}"
                            elif "validThrough" in data:
                                period = f"~{data['validThrough']}"
                        except:
                            pass

                    if period == "Unknown Period":
                        # 2. 메타 태그에서 추출
                        event_meta = soup.find("meta", property="event:start_time")
                        if event_meta:
                            period = event_meta.get("content", "")[:30]

                    if period == "Unknown Period":
                        # 3. 패턴 매칭으로 추출 (개선된 패턴)
                        date_patterns = [
                            # 기본 날짜 범위
                            r"(\d{4}[-./년]\s*\d{1,2}[-./월]\s*\d{1,2}[일]?)\s*[~-]\s*(\d{4}[-./년]\s*\d{1,2}[-./월]\s*\d{1,2}[일]?)",
                            r"(\d{1,2}[-./]\d{1,2})\s*[~-]\s*(\d{1,2}[-./]\d{1,2})",
                            # 특정 키워드와 함께
                            r"마감[:：]\s*(\d{4}[-./년]\s*\d{1,2}[-./월]\s*\d{1,2}[일]?)",
                            r"접수기간[:：]\s*([^\n\r]+?까지)",
                            r"신청기간[:：]\s*([^\n\r]+)",
                            r"모집기간[:：]\s*([^\n\r]+)",
                            r"기간[:：]\s*([^\n\r]+)",
                            r"일시[:：]\s*([^\n\r]+)",
                            r"날짜[:：]\s*([^\n\r]+)",
                            # 상대적 표현
                            r"(\d+[일월년]\s*[후뒤])\s*마감",
                            r"([^\n\r]*?까지)\s*접수",
                            r"([^\n\r]*?까지)\s*신청",
                            # 영어 패턴
                            r"until\s+([^\n\r]+)",
                            r"deadline[:：]\s*([^\n\r]+)",
                            r"due\s+([^\n\r]+)",
                        ]

                        for pattern in date_patterns:
                            match = re.search(pattern, body_text, re.IGNORECASE)
                            if match:
                                if len(match.groups()) > 1:
                                    period = f"{match.group(1).strip()} ~ {match.group(2).strip()}"
                                else:
                                    candidate = match.group(1).strip()[:50]
                                    # 의미있는 날짜 정보인지 검증
                                    if any(
                                        word in candidate
                                        for word in [
                                            "월",
                                            "일",
                                            "년",
                                            "까지",
                                            "until",
                                            "deadline",
                                            "/",
                                            "-",
                                            ".",
                                        ]
                                    ):
                                        period = candidate
                                break

                    # 장소 정보 추출 (맥락 고려 개선)
                    location = "Unknown Location"

                    # 1. 구조화된 데이터에서 추출
                    if json_ld:
                        try:
                            data = (
                                json.loads(json_ld.string)
                                if isinstance(json_ld, str)
                                else json.loads(json_ld.string)
                            )
                            if "location" in data:
                                if isinstance(data["location"], dict):
                                    location = data["location"].get(
                                        "name", data["location"].get("address", "")
                                    )
                                else:
                                    location = str(data["location"])
                        except:
                            pass

                    if location == "Unknown Location":
                        # 2. 메타 태그에서 추출
                        location_meta = soup.find("meta", property="event:location")
                        if location_meta:
                            location = location_meta.get("content", "")[:50]

                    if location == "Unknown Location":
                        # 3. 패턴 매칭으로 추출 (개선된 패턴)
                        # 우선 온라인 여부 확인
                        online_patterns = [
                            r"온라인|비대면|화상|웹|인터넷|virtual|online|zoom|webex|teams",
                            r"링크|URL|사이트에서",
                            r"Google\s+Meet|Zoom|Microsoft\s+Teams",
                        ]

                        for pattern in online_patterns:
                            if re.search(pattern, body_text, re.IGNORECASE):
                                location = "온라인"
                                break

                        if location == "Unknown Location":
                            # 물리적 장소 패턴
                            location_patterns = [
                                r"장소[:：]\s*([^\n\r]+)",
                                r"위치[:：]\s*([^\n\r]+)",
                                r"주소[:：]\s*([^\n\r]+)",
                                r"개최지[:：]\s*([^\n\r]+)",
                                r"회장[:：]\s*([^\n\r]+)",
                                r"venue[:：]\s*([^\n\r]+)",
                                r"location[:：]\s*([^\n\r]+)",
                                r"address[:：]\s*([^\n\r]+)",
                                # 지역명 패턴
                                r"([가-힣]+시\s+[가-힣]+구\s*[^\n\r]{0,30})",
                                r"([가-힣]+구\s+[가-힣]+동\s*[^\n\r]{0,30})",
                                r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[^\n\r]{0,50}",
                            ]

                            for pattern in location_patterns:
                                match = re.search(pattern, body_text, re.IGNORECASE)
                                if match:
                                    candidate = match.group(1).strip()[:50]
                                    # 의미있는 장소 정보인지 검증
                                    if len(candidate) >= 2 and not re.match(
                                        r"^\d+$", candidate
                                    ):
                                        location = candidate
                                        break

                    # 대상 정보 추출
                    target = "Unknown Target"
                    target_patterns = [
                        r"대상[:：]\s*([^\n\r]+)",
                        r"자격[:：]\s*([^\n\r]+)",
                        r"경력[:：]\s*([^\n\r]+)",
                        r"(신입|경력|인턴|신입/경력)",
                    ]
                    for pattern in target_patterns:
                        match = re.search(pattern, body_text)
                        if match:
                            target = match.group(1).strip()[:30]
                            break

                    # 키워드 추출 (제목과 설명에서)
                    keywords = ["general"]
                    all_text = f"{title} {description}".lower()
                    keyword_mapping = {
                        "채용": ["채용", "구인", "모집", "입사", "리크루팅"],
                        "펀딩": ["펀딩", "후원", "기부", "캠페인", "크라우드"],
                        "교육": ["교육", "강의", "세미나", "워크샵", "컨퍼런스"],
                        "공모": ["공모", "공모전", "지원", "신청", "모집"],
                        "행사": ["행사", "이벤트", "축제", "박람회", "전시"],
                    }

                    for category, words in keyword_mapping.items():
                        if any(word in all_text for word in words):
                            keywords = [category]
                            break

                    # 추가 컨텐츠 정보 추출
                    # 본문 주요 내용 추출 (첫 200자)
                    main_content = ""
                    content_selectors = [
                        "main",
                        "article",
                        ".content",
                        ".post",
                        ".entry",
                    ]
                    for selector in content_selectors:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            main_content = content_elem.get_text()[:200].strip()
                            break

                    if not main_content:
                        # 본문을 찾지 못한 경우 body에서 추출
                        body_paragraphs = soup.find_all("p")
                        if body_paragraphs:
                            main_content = " ".join(
                                [p.get_text().strip() for p in body_paragraphs[:3]]
                            )[:200]

                    # 이미지 정보
                    images = []
                    img_tags = soup.find_all("img", src=True)[:3]  # 최대 3개
                    for img in img_tags:
                        if img.get("src"):
                            images.append(
                                {
                                    "src": img.get("src"),
                                    "alt": img.get("alt", ""),
                                    "title": img.get("title", ""),
                                }
                            )

                    # 연락처 정보
                    contact_info = ""
                    contact_patterns = [
                        r"연락처[:：]\s*([^\n\r]+)",
                        r"문의[:：]\s*([^\n\r]+)",
                        r"이메일[:：]\s*([^\n\r]+)",
                        r"전화[:：]\s*([^\n\r]+)",
                    ]
                    for pattern in contact_patterns:
                        match = re.search(pattern, body_text)
                        if match:
                            contact_info = match.group(1).strip()[:50]
                            break

                    # 상세 내용 정보
                    details = ""
                    detail_patterns = [
                        r"내용[:：]\s*([^\n\r]+)",
                        r"상세[:：]\s*([^\n\r]+)",
                        r"설명[:：]\s*([^\n\r]+)",
                        r"소개[:：]\s*([^\n\r]+)",
                    ]
                    for pattern in detail_patterns:
                        match = re.search(pattern, body_text)
                        if match:
                            details = match.group(1).strip()[:100]
                            break

                    # URL에서 사이트 정보 추출
                    parsed_url = urlparse(url)
                    site_name = parsed_url.netloc

                    page_info = {
                        "title": title or "Unknown Title",
                        "description": description or "No description available",
                        "organizer": organizer,
                        "period": period,
                        "location": location,
                        "target": target,
                        "keywords": keywords,
                        "main_content": main_content or "No content available",
                        "images": images,
                        "contact_info": contact_info or "No contact info",
                        "details": details or "No details available",
                        "site_name": site_name,
                        "full_text": body_text[:500]
                        + ("..." if len(body_text) > 500 else ""),  # 전체 텍스트 일부
                    }

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    response_data = json.dumps(page_info, ensure_ascii=False)
                    self.wfile.write(response_data.encode("utf-8"))
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    error_response = json.dumps({"error": str(e)})
                    self.wfile.write(error_response.encode())
                    return

        # 일반 파일 서빙
        super().do_GET()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")

        # 자동으로 브라우저 열기
        webbrowser.open(f"http://localhost:{PORT}")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            httpd.shutdown()
