# 🍊 오렌지레터 링크 검증 웹앱

오렌지레터의 링크 텍스트가 실제 랜딩 페이지 내용을 정확히 반영하는지 검증하고 개선안을 제시하는 웹 애플리케이션입니다.

## 📋 주요 기능

### 🔍 뉴스레터 분석
- URL 입력을 통한 오렌지레터 분석
- HTML 파싱으로 모든 하이퍼링크 추출
- 섹션별 카테고리 자동 분류

### 📊 카테고리별 분류
**검증 대상 카테고리 (5개):**
- 🎯 채용
- 📢 후원/캠페인/이벤트
- 📚 교육/모임
- 🏆 공모/지원
- 🎉 행사

**검증 제외 카테고리 (4개):**
- 📰 소식
- 🎤 인터뷰
- 💭 생각거리
- 📣 광고

### ⚡ 링크 검증 프로세스
1. **랜딩 페이지 크롤링**
2. **페이지 정보 추출** (제목, 설명, 날짜, 주최자 등)
3. **이상적인 링크 텍스트 생성**
4. **정확도 점수 계산** (0-100%)
5. **개선안 제시**

## 🎯 정확도 평가 기준

- **핵심 정보 포함 여부 (40%)**: 행사명, 주최자, 날짜 등
- **정보의 정확성 (30%)**: 잘못된 정보가 없는지
- **가독성과 명확성 (20%)**: 간결하고 이해하기 쉬운지
- **형식 일관성 (10%)**: 오렌지레터의 기존 형식 준수

## 🚀 실행 방법

### 필요 라이브러리 설치
```bash
pip install requests beautifulsoup4
```

### 서버 실행
```bash
python3 server.py
```

서버가 시작되면 자동으로 브라우저에서 http://localhost:8000 이 열립니다.

### 사용법
1. 오렌지레터 URL 입력 (예: https://stibee.com/api/v1.0/emails/share/6hkmBPCA0PoOL3J6VWi9P1HmYE-1_34)
2. "분석 시작" 버튼 클릭
3. 결과 확인 및 개선안 복사

## 🎨 주요 UI 구성

### 📱 반응형 디자인
- **데스크톱**: 전체 테이블 표시
- **태블릿**: 일부 컬럼 숨김
- **모바일**: 카드 형태로 전환

### 🎯 메인 기능
- **요약 대시보드**: 전체 정확도, 검증 대상 링크 수, 수정 필요 개수
- **카테고리 개요**: 카테고리별 정확도 및 링크 수 표시
- **필터링**: 카테고리별, 정확도별 필터링
- **정렬**: 정확도, 카테고리별 정렬
- **상세 모달**: 각 링크별 상세 분석 정보
- **복사 기능**: 개선된 링크 텍스트 쉬운 복사

## 📝 카테고리별 포맷팅 규칙

### 채용
- 형식: `[회사명] 직군 채용 (경력구분, 마감일)`
- 예시: `[스타트업] AI 개발자 채용 (경력 3년+, ~12/31)`

### 후원/캠페인/이벤트
- 형식: `프로젝트명 펀딩 (~마감일)`
- 예시: `환경보호 캠페인 펀딩 (~12/31)`

### 교육/모임
- 형식: `[주최] 프로그램명 (장소)`
- 예시: `[서울시] AI 워크샵 (강남구)`

### 공모/지원
- 형식: `공모전명 (~마감일)`
- 예시: `2024 창업 공모전 (~12/31)`

### 행사
- 형식: `[주최] 행사명 (장소, 기간)`
- 예시: `[문화재단] 음악 축제 (종로구, ~12/25)`

## 🔧 기술 스택

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python HTTP Server
- **Libraries**: 
  - requests (HTTP 요청)
  - BeautifulSoup4 (HTML 파싱)
- **Features**:
  - CORS 처리
  - 반응형 웹 디자인
  - 모바일 최적화

## 🚀 배포 가이드

### Vercel 배포 (권장)

1. **Vercel 계정 생성**
   - https://vercel.com 에서 GitHub 계정으로 로그인

2. **프로젝트 Import**
   ```bash
   # 1. GitHub에 프로젝트 푸시
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/orangeletter-link-checker.git
   git push -u origin main
   
   # 2. Vercel 대시보드에서
   - "New Project" 클릭
   - GitHub 저장소 선택
   - Framework Preset: "Other" 선택
   ```

3. **환경 변수 설정**
   - Settings > Environment Variables
   - 필요한 환경 변수 추가:
     ```
     PORT=8080
     HOST=0.0.0.0
     ```

4. **배포**
   - "Deploy" 버튼 클릭
   - 자동 빌드 및 배포 진행

### 로컬 개발 환경 설정

1. **저장소 클론**
   ```bash
   git clone https://github.com/your-username/orangeletter-link-checker.git
   cd orangeletter-link-checker
   ```

2. **Python 가상환경 설정**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일 수정
   ```

5. **로컬 서버 실행**
   ```bash
   python server.py
   ```

### 수동 서버 배포

1. **서버 준비**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

2. **프로젝트 배포**
   ```bash
   # 코드 업로드
   scp -r * user@server:/var/www/orangeletter-checker
   
   # 의존성 설치
   ssh user@server
   cd /var/www/orangeletter-checker
   pip3 install -r requirements.txt
   ```

3. **Systemd 서비스 설정**
   ```bash
   # /etc/systemd/system/orangeletter-checker.service
   [Unit]
   Description=Orange Letter Link Checker
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/var/www/orangeletter-checker
   ExecStart=/usr/bin/python3 /var/www/orangeletter-checker/server.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **서비스 시작**
   ```bash
   sudo systemctl enable orangeletter-checker
   sudo systemctl start orangeletter-checker
   ```

## 📊 테스트 URL

다음 URL로 테스트 가능:
```
https://stibee.com/api/v1.0/emails/share/6hkmBPCA0PoOL3J6VWi9P1HmYE-1_34
```

## 🎯 주요 특징

1. **정확한 분류**: 섹션 제목 패턴 인식을 통한 자동 카테고리 분류
2. **실시간 분석**: 실제 랜딩 페이지 크롤링으로 정확한 정보 추출
3. **사용자 친화적**: 직관적인 UI와 상세한 분석 결과 제공
4. **효율적인 작업흐름**: 복사 기능으로 빠른 텍스트 수정 가능
5. **모바일 지원**: 반응형 디자인으로 다양한 기기에서 사용 가능

## 🚨 주의사항

- CORS 정책으로 인해 일부 사이트의 크롤링이 제한될 수 있습니다
- 크롤링 실패 시 시뮬레이션된 데이터로 대체됩니다
- 과도한 요청은 서버 부하를 줄 수 있으니 적절한 간격을 두고 사용하세요

## 📞 문의

기능 개선이나 버그 신고는 이슈로 등록해주세요.