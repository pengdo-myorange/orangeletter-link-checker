// 전역 변수
let analysisData = [];
let currentSortField = 'accuracy';
let currentSortOrder = 'desc';
let startTime;
let notificationsEnabled = false;

// 카테고리 정의
const CATEGORIES = {
    VERIFIED: {
        job: { name: '채용', icon: '🎯', color: '#2196F3' },
        funding: { name: '후원/캠페인/이벤트', icon: '📢', color: '#4CAF50' },
        education: { name: '교육/모임', icon: '📚', color: '#9C27B0' },
        contest: { name: '공모/지원', icon: '🏆', color: '#FF9800' },
        event: { name: '행사', icon: '🎉', color: '#F44336' }
    },
    EXCLUDED: {
        news: { name: '소식', icon: '📰', color: '#9E9E9E' },
        interview: { name: '인터뷰', icon: '🎤', color: '#9E9E9E' },
        thought: { name: '생각거리', icon: '💭', color: '#9E9E9E' },
        ad: { name: '광고', icon: '📣', color: '#9E9E9E' }
    }
};

// 섹션 제목 패턴 매칭 - 오렌지레터 실제 구조에 맞게 수정
const SECTION_PATTERNS = {
    '소식': /\(소식\)\s*세상을 바꾸는 크고 작은 움직임이 있었어요/i,
    '인터뷰': /\(인터뷰\)\s*어떤 사람들이, 무슨 변화를 꿈꿀까요\?/i,
    '생각거리': /\(생각거리\)\s*우리는 다양한 목소리와 이야기를 듣고 싶어요/i,
    '광고': /\(광고\)\s*오렌지레터 비즈니스 서포터 소식이에요/i,
    '채용': /\(채용\)\s*좋아하는 일이 직업이 될 수도 있어요/i,
    '후원/캠페인/이벤트': /\(후원\/캠페인\/이벤트\)\s*마음이 가는 일은 적극적으로 밀어줘요/i,
    '교육/모임': /\(교육\/모임\)\s*따로 또 같이, 사람들과 함께 성장해요/i,
    '공모/지원': /\(공모\/지원\)\s*언제나 새로운 기회는 있어요/i,
    '행사': /\(행사\)\s*여기서 만나요/i
};

// DOM 요소
const elements = {
    urlInput: document.getElementById('url-input'),
    analyzeBtn: document.getElementById('analyze-btn'),
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingText: document.getElementById('loading-text'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    resultsSection: document.getElementById('results-section'),
    newsletterUrl: document.getElementById('newsletter-url'),
    newsletterTitle: document.getElementById('newsletter-title'),
    verifiedCategories: document.getElementById('verified-categories'),
    categoryFilter: document.getElementById('category-filter'),
    resultsTable: document.getElementById('results-table'),
    resultsTbody: document.getElementById('results-tbody'),
    completionTime: document.getElementById('completion-time'),
    duration: document.getElementById('duration'),
    detailModal: document.getElementById('detail-modal'),
    modalClose: document.getElementById('modal-close'),
    modalCancel: document.getElementById('modal-cancel'),
    toastContainer: document.getElementById('toast-container'),
    aiToggleBtn: document.getElementById('ai-toggle-btn')
};

// 푸시 알림 관련 함수
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.log('이 브라우저는 알림을 지원하지 않습니다.');
        return false;
    }
    
    if (Notification.permission === 'granted') {
        notificationsEnabled = true;
        return true;
    }
    
    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            notificationsEnabled = true;
            showToast('알림이 활성화되었습니다! 분석 완료 시 알림을 받을 수 있어요.', 'success');
            return true;
        }
    }
    
    notificationsEnabled = false;
    return false;
}

function showNotification(title, options = {}) {
    if (!notificationsEnabled || Notification.permission !== 'granted') {
        return;
    }
    
    const defaultOptions = {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'orangeletter-analysis',
        renotify: true,
        requireInteraction: true
    };
    
    const notification = new Notification(title, {
        ...defaultOptions,
        ...options
    });
    
    // 클릭 시 창 포커스
    notification.onclick = function() {
        window.focus();
        notification.close();
    };
    
    // 5초 후 자동 닫기
    setTimeout(() => {
        notification.close();
    }, 5000);
    
    return notification;
}

function sendAnalysisCompleteNotification(analysisData) {
    if (!notificationsEnabled) {
        return;
    }
    
    const totalLinks = analysisData.length;
    const lowAccuracyLinks = analysisData.filter(item => item.accuracy < 70).length;
    const avgAccuracy = totalLinks > 0 ? Math.round(analysisData.reduce((sum, item) => sum + item.accuracy, 0) / totalLinks) : 0;
    
    let title = '🍊 오렌지레터 링크 분석 완료!';
    let body;
    let icon = '/favicon.ico';
    
    if (lowAccuracyLinks === 0) {
        body = `✅ ${totalLinks}개 링크 분석 완료\n평균 정확도: ${avgAccuracy}% - 모든 링크가 양호합니다!`;
        icon = '✅';
    } else {
        body = `⚠️ ${totalLinks}개 링크 분석 완료\n평균 정확도: ${avgAccuracy}%\n${lowAccuracyLinks}개 링크 수정 필요`;
        icon = '⚠️';
    }
    
    showNotification(title, {
        body: body,
        icon: icon,
        tag: 'analysis-complete'
    });
}

async function handleNotificationToggle() {
    if (Notification.permission === 'denied') {
        showToast('브라우저에서 알림이 차단되어 있습니다. 브라우저 설정에서 알림을 허용해주세요.', 'error');
        return;
    }
    
    if (!notificationsEnabled) {
        const granted = await requestNotificationPermission();
        if (granted) {
            showToast('알림이 활성화되었습니다!', 'success');
        } else {
            showToast('알림 권한이 거부되었습니다.', 'error');
        }
    } else {
        notificationsEnabled = false;
        showToast('알림이 비활성화되었습니다.', 'info');
    }
    
    updateNotificationButtonState();
}

function updateNotificationButtonState() {
    const notificationBtn = document.getElementById('notification-btn');
    if (!notificationBtn) return;
    
    if (notificationsEnabled) {
        notificationBtn.textContent = '🔔';
        notificationBtn.title = '알림 활성화됨 (클릭하여 비활성화)';
        notificationBtn.style.backgroundColor = '#4CAF50';
        notificationBtn.style.color = 'white';
    } else {
        notificationBtn.textContent = '🔕';
        notificationBtn.title = '알림 비활성화됨 (클릭하여 활성화)';
        notificationBtn.style.backgroundColor = '#f5f5f5';
        notificationBtn.style.color = '#666';
    }
}

// AI 분석 관련 함수
function handleAIToggle() {
    const useBedrockAPI = localStorage.getItem('useBedrockAPI') === 'true';
    
    if (!useBedrockAPI) {
        localStorage.setItem('useBedrockAPI', 'true');
        showToast('AI 분석이 활성화되었습니다! 다음 분석부터 적용됩니다.', 'success');
    } else {
        localStorage.setItem('useBedrockAPI', 'false');
        showToast('AI 분석이 비활성화되었습니다.', 'info');
    }
    
    updateAIButtonState();
}

function updateAIButtonState() {
    if (!elements.aiToggleBtn) return;
    
    const useBedrockAPI = localStorage.getItem('useBedrockAPI') === 'true';
    
    if (useBedrockAPI) {
        elements.aiToggleBtn.classList.add('active');
        elements.aiToggleBtn.title = 'AI 분석 활성화됨 (클릭하여 비활성화)';
    } else {
        elements.aiToggleBtn.classList.remove('active');
        elements.aiToggleBtn.title = 'AI 분석 비활성화됨 (클릭하여 활성화)';
    }
}

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    // 기본 title 설정
    document.title = '🍊 오렌지레터 링크 검증 도구';
    
    // 알림 권한 요청
    requestNotificationPermission();
    
    // 알림 버튼 이벤트 리스너
    const notificationBtn = document.getElementById('notification-btn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', handleNotificationToggle);
        updateNotificationButtonState();
    }
    
    // AI 분석 버튼 설정
    if (elements.aiToggleBtn) {
        elements.aiToggleBtn.addEventListener('click', handleAIToggle);
        updateAIButtonState();
    }
    
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') handleAnalyze();
    });
    
    // URL 입력 중 프리페칭
    let prefetchTimeout;
    elements.urlInput.addEventListener('input', function(e) {
        clearTimeout(prefetchTimeout);
        const url = e.target.value.trim();
        
        // URL이 유효하고 오렌지레터 도메인인 경우 프리페칭
        if (isValidUrl(url) && url.includes('orangeletter.net')) {
            prefetchTimeout = setTimeout(() => {
                // 백그라운드에서 HTML 미리 가져오기
                fetchNewsletterHtml(url).catch(() => {});
                console.log('프리페칭 시작:', url);
            }, 1000); // 1초 후에 프리페칭
        }
    });
    
    elements.categoryFilter.addEventListener('change', applyFilters);
    
    elements.modalClose.addEventListener('click', hideModal);
    elements.modalCancel.addEventListener('click', hideModal);
    
    document.getElementById('copy-all-btn').addEventListener('click', copyAllSuggestions);
    document.getElementById('reset-btn').addEventListener('click', resetAnalysis);
    
    // 모달 배경 클릭시 닫기
    elements.detailModal.addEventListener('click', function(e) {
        if (e.target === elements.detailModal) hideModal();
    });
});

// 메인 분석 함수
async function handleAnalyze() {
    if (!elements.urlInput || !elements.urlInput.value) {
        showToast('URL을 입력해주세요.', 'error');
        return;
    }
    
    const url = elements.urlInput.value.trim();
    if (!url) {
        showToast('URL을 입력해주세요.', 'error');
        return;
    }
    
    if (!isValidUrl(url)) {
        showToast('올바른 URL을 입력해주세요.', 'error');
        return;
    }
    
    startTime = Date.now();
    showLoading();
    
    try {
        // URL 표시
        elements.newsletterUrl.textContent = `분석 URL: ${url}`;
        
        // 1. 뉴스레터 HTML 가져오기
        updateLoadingText('뉴스레터 데이터를 가져오는 중...');
        const newsletterHtml = await fetchNewsletterHtml(url);
        
        // 2. 링크 추출 및 카테고리 분류
        updateLoadingText('링크를 추출하고 분류하는 중...');
        const links = extractAndCategorizeLinks(newsletterHtml);
        
        // 3. 검증 대상 링크만 필터링
        const verifiedLinks = links.filter(link => isVerifiedCategory(link.category));
        
        // 4. 각 링크 분석 - Bedrock Claude API 사용 시도
        updateLoadingText('링크를 분석하는 중...');
        analysisData = [];
        
        // Bedrock Claude API 사용 가능 여부 확인
        const useBedrockAPI = localStorage.getItem('useBedrockAPI') === 'true';
        
        if (useBedrockAPI) {
            try {
                // Bedrock Claude API로 일괄 분석
                updateLoadingText('AI로 링크를 일괄 분석하는 중...');
                const response = await fetch('/api/analyze-batch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ links: verifiedLinks })
                });
                
                if (response.ok) {
                    const results = await response.json();
                    // AI 분석 결과를 기존 포맷에 맞게 변환
                    for (let i = 0; i < verifiedLinks.length; i++) {
                        const link = verifiedLinks[i];
                        const aiResult = results[link.url] || {};
                        analysisData.push({
                            ...link,
                            pageInfo: aiResult.key_info || {},
                            suggestedText: aiResult.suggested_text || link.text,
                            accuracy: aiResult.accuracy || 0,
                            issues: aiResult.issues || [],
                            breakdown: calculateDetailedScore(link.text, aiResult.suggested_text || link.text, aiResult.key_info || {}, link.category)
                        });
                    }
                    showToast('AI 분석을 사용하여 빠르게 완료되었습니다!', 'success');
                } else {
                    throw new Error('Bedrock API 호출 실패');
                }
            } catch (error) {
                console.warn('Bedrock API 사용 실패, 기본 방식으로 전환:', error);
                showToast('AI 분석을 사용할 수 없어 기본 방식으로 진행합니다.', 'warning');
                await analyzeLinksInBatches(verifiedLinks);
            }
        } else {
            await analyzeLinksInBatches(verifiedLinks);
        }
        
        async function analyzeLinksInBatches(links) {
            const batchSize = 10;  // 5 -> 10으로 증가
            
            for (let i = 0; i < links.length; i += batchSize) {
                const batch = links.slice(i, i + batchSize);
                const currentBatchStart = i;
                
                // 배치 프로그레스 업데이트
                updateProgress(currentBatchStart, links.length, 
                    `링크 분석 중... (${Math.min(i + batchSize, links.length)}/${links.length})`);
                
                // 병렬로 배치 처리
                const batchPromises = batch.map(async (link) => {
                    try {
                        const pageInfo = await scrapePageInfo(link.url);
                        return analyzeLink(link, pageInfo);
                    } catch (error) {
                        console.error(`링크 분석 실패: ${link.url}`, error);
                        return {
                            ...link,
                            accuracy: 0,
                            issues: ['페이지 로드 실패'],
                            suggestedText: link.text,
                            pageInfo: null,
                            error: error.message
                        };
                    }
                });
                
                // 배치 결과 수집
                const batchResults = await Promise.all(batchPromises);
                analysisData.push(...batchResults);
                
                // 다음 배치 전 지연 제거 (필요시에만 추가)
                // 서버가 rate limit를 가지고 있다면 이 부분을 조정하세요
            }
        }
        
        hideLoading();
        displayResults(analysisData, links);
        
        // 분석 완료 알림 발송
        sendAnalysisCompleteNotification(analysisData);
        
    } catch (error) {
        console.error('분석 중 오류 발생:', error);
        hideLoading();
        showToast('분석 중 오류가 발생했습니다: ' + error.message, 'error');
    }
}

// 뉴스레터 HTML 가져오기 (캐싱 추가)
async function fetchNewsletterHtml(url) {
    // 캐시 확인
    const cacheKey = `newsletter_${url}`;
    const cached = sessionStorage.getItem(cacheKey);
    
    if (cached) {
        try {
            const cachedData = JSON.parse(cached);
            // 1시간 캐시 유효
            if (Date.now() - cachedData.timestamp < 60 * 60 * 1000) {
                console.log(`뉴스레터 캐시 사용: ${url}`);
                return cachedData.data;
            }
        } catch (e) {
            // 캐시 파싱 실패 시 무시
        }
    }
    
    try {
        // 로컬 서버의 API 엔드포인트 사용
        const response = await fetch(`/api/fetch?url=${encodeURIComponent(url)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const html = await response.text();
        
        // 캐시 저장
        try {
            sessionStorage.setItem(cacheKey, JSON.stringify({
                timestamp: Date.now(),
                data: html
            }));
        } catch (e) {
            // sessionStorage 용량 초과 시 무시
        }
        
        return html;
    } catch (error) {
        throw new Error(`뉴스레터 데이터 가져오기 실패: ${error.message}`);
    }
}

// 링크 추출 및 카테고리 분류
function extractAndCategorizeLinks(html) {
    console.log('링크 추출 시작');
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const links = [];
    const processedUrls = new Set(); // 중복 제거용
    
    // 뉴스레터 제목 추출 및 표시
    extractAndDisplayNewsletterTitle(doc);
    
    // 문서 전체에서 섹션 패턴 찾기
    const bodyText = doc.body ? doc.body.textContent : doc.textContent;
    const sectionMatches = [];
    
    // 각 섹션의 위치 찾기
    for (const [categoryName, pattern] of Object.entries(SECTION_PATTERNS)) {
        const match = pattern.exec(bodyText);
        if (match) {
            sectionMatches.push({
                category: getCategoryKeyFromName(categoryName),
                name: categoryName,
                position: match.index,
                text: match[0]
            });
        }
    }
    
    // 섹션을 위치 순으로 정렬
    sectionMatches.sort((a, b) => a.position - b.position);
    console.log('발견된 섹션들:', sectionMatches.map(s => s.name));
    
    // 모든 링크를 문서 순서대로 추출 (더 정확한 방법)
    const allElements = doc.querySelectorAll('*');
    const linkElementsInOrder = [];
    
    // DOM 순서대로 모든 요소를 순회하며 링크 찾기
    for (let i = 0; i < allElements.length; i++) {
        const element = allElements[i];
        if (element.tagName === 'A' && element.href) {
            const text = element.textContent ? element.textContent.trim() : '';
            const url = element.href;
            
            // 기본 필터링
            if (!text || 
                text.length < 3 || 
                url.startsWith('#') || 
                url.startsWith('mailto:') || 
                url.includes('stibee.com') ||
                url.includes('orangeletter.kr') ||
                processedUrls.has(url) ||
                text.includes('구독') ||
                text.includes('구독하기') ||
                text.includes('바로가기') ||
                text.length > 200) {
                continue;
            }
            
            // 푸터 관련 필터링 강화
            if (text.includes('오렌지랩') || 
                text.includes('수신거부') || 
                text.includes('unsubscribe') ||
                text.includes('오렌지레터와 메일함 바깥에서 만나기') ||
                text.includes('광고(유료)') ||
                text.includes('제보하기(무료)') ||
                text.includes('광고하기(유료)') ||
                text.includes('광고 문의') ||
                text.includes('제보 문의') ||
                url.includes('orangelab.kr')) {
                continue;
            }
            
            linkElementsInOrder.push({
                element: element,
                text: text,
                url: url,
                position: getLinkPosition(element, bodyText)
            });
        }
    }
    
    // 링크를 텍스트 위치 기준으로 정렬 (더 정확한 순서)
    linkElementsInOrder.sort((a, b) => a.position - b.position);
    
    // 링크를 순서대로 처리하여 카테고리 분류
    linkElementsInOrder.forEach((linkInfo, index) => {
        const { element, text, url, position } = linkInfo;
        
        // 현재 링크가 속한 섹션 찾기
        let currentCategory = 'news'; // 기본값
        let sectionContext = '';
        
        for (let i = sectionMatches.length - 1; i >= 0; i--) {
            if (position >= sectionMatches[i].position) {
                currentCategory = sectionMatches[i].category;
                sectionContext = sectionMatches[i].text;
                break;
            }
        }
        
        // 추가적인 텍스트 기반 분류
        const finalCategory = categorizeFromContext(sectionContext, text, url) || currentCategory;
        
        // 중복 체크
        processedUrls.add(url);
        
        links.push({
            id: `link-${index}`,
            url: url,
            text: text,
            category: finalCategory,
            section: sectionContext,
            order: index,
            position: position
        });
        
        console.log(`링크 #${index}: ${text.substring(0, 40)}... -> ${finalCategory} (pos: ${position})`);
    });
    
    // 카테고리별 링크 개수 로깅
    const categoryCounts = {};
    links.forEach(link => {
        categoryCounts[link.category] = (categoryCounts[link.category] || 0) + 1;
    });
    
    console.log('카테고리별 링크 개수:', categoryCounts);
    console.log(`총 ${links.length}개 링크 추출됨`);
    
    return links;
}

// 뉴스레터 제목 추출 및 표시
function extractAndDisplayNewsletterTitle(doc) {
    let title = '';
    
    // 1. title 태그에서 추출
    const titleTag = doc.querySelector('title');
    if (titleTag && titleTag.textContent) {
        title = titleTag.textContent.trim();
    }
    
    // 2. 본문에서 뉴스레터 제목 패턴 찾기
    if (!title || title.length < 5) {
        const bodyText = doc.body ? doc.body.textContent : doc.textContent;
        
        // 오렌지레터 특정 패턴들
        const titlePatterns = [
            /🍊\s*([^🍊\n\r]{10,100})/,  // 오렌지 이모지 뒤의 텍스트
            /오렌지레터\s*([^#\n\r]{10,100})/,
            /(\d{4}년\s*\d{1,2}월\s*\d{1,2}일[^#\n\r]{5,50})/,
            /([^#\n\r]{5,50})\s*#\d+/  // # 숫자 앞의 텍스트
        ];
        
        for (const pattern of titlePatterns) {
            const match = pattern.exec(bodyText);
            if (match) {
                title = match[1].trim();
                if (title.length >= 5) break;
            }
        }
    }
    
    // 3. 메타 태그에서 추출
    if (!title || title.length < 5) {
        const metaTitle = doc.querySelector('meta[property="og:title"]') || 
                         doc.querySelector('meta[name="title"]');
        if (metaTitle && metaTitle.content) {
            title = metaTitle.content.trim();
        }
    }
    
    // 4. h1 태그에서 추출
    if (!title || title.length < 5) {
        const h1 = doc.querySelector('h1');
        if (h1 && h1.textContent) {
            title = h1.textContent.trim();
        }
    }
    
    // 제목 정리
    if (title) {
        // 불필요한 텍스트 제거
        title = title.replace(/^\s*-\s*/, '')  // 시작 부분의 대시 제거
                    .replace(/\s*-\s*$/, '')  // 끝 부분의 대시 제거
                    .replace(/^\s*\|\s*/, '') // 시작 부분의 파이프 제거
                    .replace(/\s*\|\s*$/, '') // 끝 부분의 파이프 제거
                    .replace(/^\s*:\s*/, '')  // 시작 부분의 콜론 제거
                    .replace(/\s*:\s*$/, '')  // 끝 부분의 콜론 제거
                    .substring(0, 100);       // 최대 100자 제한
    }
    
    // UI에 표시
    if (title && title.length >= 3) {
        elements.newsletterTitle.textContent = title;
        console.log('뉴스레터 제목:', title);
    } else {
        elements.newsletterTitle.textContent = '제목을 찾을 수 없습니다';
    }
}

// 링크의 문서 내 위치 계산
function getLinkPosition(linkElement, bodyText) {
    const linkText = linkElement.textContent.trim();
    if (!linkText) return 0;
    
    // 링크 텍스트의 첫 번째 출현 위치 찾기
    const position = bodyText.indexOf(linkText);
    return position >= 0 ? position : 0;
}

// 링크 주변 컨텍스트 가져오기
function getLinkContext(linkElement, bodyText) {
    // 링크가 포함된 부모 요소들의 텍스트를 순회하여 섹션 찾기
    let current = linkElement;
    
    while (current && current.parentElement) {
        current = current.parentElement;
        const text = current.textContent || '';
        
        // 섹션 패턴 찾기
        for (const [categoryName, pattern] of Object.entries(SECTION_PATTERNS)) {
            if (pattern.test(text)) {
                return text.substring(0, 100);
            }
        }
    }
    
    return '';
}

// 컨텍스트를 기반으로 카테고리 분류
function categorizeFromContext(context, linkText, url) {
    // 1. 컨텍스트 기반 분류 (우선순위 1)
    for (const [categoryName, pattern] of Object.entries(SECTION_PATTERNS)) {
        if (pattern.test(context)) {
            return getCategoryKeyFromName(categoryName);
        }
    }
    
    // 2. 링크 텍스트 기반 상세 분류 (우선순위 2)
    const text = linkText.toLowerCase();
    
    // 채용 관련 키워드 (더 상세하게)
    if (text.includes('채용') || text.includes('모집') || text.includes('구인') || 
        text.includes('입사') || text.includes('리크루팅') || text.includes('신입') || 
        text.includes('경력') || text.includes('인턴') || text.includes('정규직') ||
        text.includes('계약직') || text.includes('파트타임')) {
        return 'job';
    }
    
    // 펀딩/후원 관련 키워드
    if (text.includes('펀딩') || text.includes('후원') || text.includes('캠페인') || 
        text.includes('기부') || text.includes('크라우드') || text.includes('모금') ||
        text.includes('도움') || text.includes('지원해') || text.includes('함께해')) {
        return 'funding';
    }
    
    // 교육/모임 관련 키워드
    if (text.includes('교육') || text.includes('강의') || text.includes('세미나') || 
        text.includes('워크샵') || text.includes('컨퍼런스') || text.includes('토론') ||
        text.includes('모임') || text.includes('스터디') || text.includes('네트워킹') ||
        text.includes('아카데미') || text.includes('학습') || text.includes('프로그램')) {
        return 'education';
    }
    
    // 공모/지원 관련 키워드
    if (text.includes('공모') || text.includes('지원') || text.includes('신청') || 
        text.includes('모집') || text.includes('선발') || text.includes('접수') ||
        text.includes('마감') || text.includes('응모')) {
        return 'contest';
    }
    
    // 행사 관련 키워드
    if (text.includes('행사') || text.includes('이벤트') || text.includes('축제') || 
        text.includes('박람회') || text.includes('전시') || text.includes('페어') ||
        text.includes('개최') || text.includes('참가')) {
        return 'event';
    }
    
    // 3. URL 기반 추론 (우선순위 3)
    const urlLower = url.toLowerCase();
    
    // 채용 관련 URL
    if (urlLower.includes('career') || urlLower.includes('job') || urlLower.includes('recruit') ||
        urlLower.includes('hiring') || urlLower.includes('employment') || urlLower.includes('saramin') ||
        urlLower.includes('jobkorea') || urlLower.includes('wanted')) {
        return 'job';
    }
    
    // 펀딩 관련 URL
    if (urlLower.includes('funding') || urlLower.includes('campaign') || urlLower.includes('donation') ||
        urlLower.includes('happybean') || urlLower.includes('tumblbug') || urlLower.includes('kickstarter') ||
        urlLower.includes('indiegogo') || urlLower.includes('cherry.charity') || urlLower.includes('socialfunch')) {
        return 'funding';
    }
    
    // 교육 관련 URL
    if (urlLower.includes('education') || urlLower.includes('seminar') || urlLower.includes('academy') ||
        urlLower.includes('course') || urlLower.includes('workshop') || urlLower.includes('conference') ||
        urlLower.includes('onoffmix') || urlLower.includes('festa')) {
        return 'education';
    }
    
    // 공모 관련 URL
    if (urlLower.includes('contest') || urlLower.includes('competition') || urlLower.includes('apply') ||
        urlLower.includes('application') || urlLower.includes('startup')) {
        return 'contest';
    }
    
    // 행사 관련 URL
    if (urlLower.includes('event') || urlLower.includes('festival') || urlLower.includes('fair') ||
        urlLower.includes('exhibition')) {
        return 'event';
    }
    
    // 4. 도메인별 특성 분류 (우선순위 4)
    if (urlLower.includes('naver.com') || urlLower.includes('kakao.com')) {
        // 네이버, 카카오는 주로 펀딩/캠페인
        return 'funding';
    }
    
    if (urlLower.includes('forms.gle') || urlLower.includes('tally.so') || urlLower.includes('typeform')) {
        // 구글폼 등은 주로 신청/지원
        return 'contest';
    }
    
    // 기본값: 소식 (분류되지 않은 경우)
    return 'news';
}


// 카테고리 이름을 키로 변환
function getCategoryKeyFromName(name) {
    const mapping = {
        '소식': 'news',
        '인터뷰': 'interview', 
        '생각거리': 'thought',
        '광고': 'ad',
        '채용': 'job',
        '후원/캠페인/이벤트': 'funding',
        '교육/모임': 'education',
        '공모/지원': 'contest',
        '행사': 'event'
    };
    return mapping[name] || 'news';
}

// 검증 대상 카테고리 확인
function isVerifiedCategory(category) {
    return Object.keys(CATEGORIES.VERIFIED).includes(category);
}

// 페이지 정보 스크래핑 (캐싱 추가)
async function scrapePageInfo(url) {
    // 캐시 확인
    const cacheKey = `scrape_${url}`;
    const cached = localStorage.getItem(cacheKey);
    
    if (cached) {
        try {
            const cachedData = JSON.parse(cached);
            // 24시간 캐시 유효
            if (Date.now() - cachedData.timestamp < 24 * 60 * 60 * 1000) {
                console.log(`캐시 사용: ${url}`);
                return cachedData.data;
            }
        } catch (e) {
            // 캐시 파싱 실패 시 무시
        }
    }
    
    try {
        // 로컬 서버의 스크래핑 API 사용
        const response = await fetch(`/api/scrape?url=${encodeURIComponent(url)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const pageInfo = await response.json();
        
        // 캐시 저장
        try {
            localStorage.setItem(cacheKey, JSON.stringify({
                timestamp: Date.now(),
                data: pageInfo
            }));
        } catch (e) {
            // localStorage 용량 초과 시 오래된 캐시 삭제
            clearOldCache();
        }
        
        return pageInfo;
    } catch (error) {
        console.warn(`페이지 스크래핑 실패 (${url}):`, error.message);
        // 실패시 에러 정보와 함께 기본 정보 반환
        return {
            title: "페이지 로드 실패",
            description: error.message || "페이지를 불러올 수 없습니다",
            organizer: "Unknown",
            period: "Unknown",
            location: "Unknown",
            target: "Unknown",
            keywords: ["error"],
            error: true,
            errorMessage: error.message
        };
    }
}

// 오래된 캐시 삭제 함수
function clearOldCache() {
    const keys = Object.keys(localStorage);
    const scrapeKeys = keys.filter(k => k.startsWith('scrape_'));
    const now = Date.now();
    
    // 가장 오래된 항목부터 삭제
    scrapeKeys.sort((a, b) => {
        try {
            const aData = JSON.parse(localStorage.getItem(a));
            const bData = JSON.parse(localStorage.getItem(b));
            return (aData.timestamp || 0) - (bData.timestamp || 0);
        } catch (e) {
            return 0;
        }
    });
    
    // 절반 삭제
    const toRemove = Math.floor(scrapeKeys.length / 2);
    for (let i = 0; i < toRemove; i++) {
        localStorage.removeItem(scrapeKeys[i]);
    }
}

// 시뮬레이션된 페이지 정보 생성
function generateSimulatedPageInfo(url) {
    const samples = [
        {
            title: '2024 청년 창업 지원 프로그램',
            description: '서울시에서 진행하는 청년 창업자 지원 사업입니다.',
            organizer: '서울특별시',
            period: '2024.11.01 ~ 2024.12.31',
            location: '서울시 전체',
            target: '만 19~39세 청년 창업자',
            keywords: ['창업', '지원', '청년', '서울시']
        },
        {
            title: 'AI 개발자 채용 공고',
            description: '혁신적인 AI 스타트업에서 시니어 개발자를 모집합니다.',
            organizer: '테크스타트업',
            period: '채용시 마감',
            location: '강남구 역삼동',
            target: '경력 3년 이상',
            keywords: ['AI', '개발자', '채용', '스타트업']
        },
        {
            title: '환경보호 캠페인 후원',
            description: '지구를 지키는 환경보호 캠페인에 함께해주세요.',
            organizer: '환경보호단체',
            period: '2024.12.01 ~ 2024.12.31',
            location: '온라인',
            target: '일반인',
            keywords: ['환경', '캠페인', '후원', '펀딩']
        }
    ];
    
    // URL 해시 기반으로 일관된 샘플 데이터 선택
    const hash = url.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
    }, 0);
    
    return samples[Math.abs(hash) % samples.length];
}

// 링크 분석
function analyzeLink(link, pageInfo) {
    const currentText = link.text;
    const suggestedText = generateIdealLinkText(link.category, pageInfo);
    const accuracy = calculateAccuracy(currentText, suggestedText, pageInfo, link.category);
    const issues = identifyIssues(currentText, pageInfo, link.category);
    
    return {
        ...link,
        pageInfo: pageInfo,
        suggestedText: suggestedText,
        accuracy: accuracy,
        issues: issues,
        breakdown: calculateDetailedScore(currentText, suggestedText, pageInfo, link.category)
    };
}

// 이상적인 링크 텍스트 생성
function generateIdealLinkText(category, pageInfo) {
    if (!pageInfo) return '';
    
    const rules = getCategoryRules(category);
    let text = '';
    
    switch (category) {
        case 'job':
            // [회사명] 직군 채용 (경력구분, 마감일)
            text = `[${pageInfo.organizer}] ${pageInfo.title}`;
            if (pageInfo.target) text += ` (${pageInfo.target})`;
            if (pageInfo.period && pageInfo.period !== '채용시 마감') {
                text += ` (~${formatPeriod(pageInfo.period)})`;
            }
            break;
            
        case 'funding':
            // 프로젝트명 펀딩 (~마감일)
            text = pageInfo.title;
            if (pageInfo.keywords.some(k => ['펀딩', '캠페인'].includes(k))) {
                text += ' 펀딩';
            }
            if (pageInfo.period) text += ` (~${formatPeriod(pageInfo.period)})`;
            break;
            
        case 'education':
            // [주최] 프로그램명 (장소, 날짜)
            text = `[${pageInfo.organizer}] ${pageInfo.title}`;
            if (pageInfo.location && pageInfo.location !== '온라인') {
                text += ` (${pageInfo.location})`;
            }
            break;
            
        case 'contest':
            // 공모전명 (~마감일)
            text = pageInfo.title;
            if (pageInfo.period) text += ` (~${formatPeriod(pageInfo.period)})`;
            break;
            
        case 'event':
            // [주최] 행사명 (장소, 기간)
            text = `[${pageInfo.organizer}] ${pageInfo.title}`;
            if (pageInfo.location) {
                text += ` (${pageInfo.location}`;
                if (pageInfo.period) text += `, ${formatPeriod(pageInfo.period)}`;
                text += ')';
            }
            break;
            
        default:
            text = pageInfo.title;
    }
    
    return text;
}

// 기간 포맷팅
function formatPeriod(period) {
    if (!period) return '';
    
    // "YYYY.MM.DD ~ YYYY.MM.DD" 형태를 "MM/DD" 형태로 변환
    const match = period.match(/(\d{4})\.(\d{2})\.(\d{2})\s*~\s*(\d{4})\.(\d{2})\.(\d{2})/);
    if (match) {
        const [, , , , endYear, endMonth, endDay] = match;
        return `${parseInt(endMonth)}/${parseInt(endDay)}`;
    }
    
    return period;
}

// 카테고리별 규칙 가져오기
function getCategoryRules(category) {
    const rules = {
        job: {
            requiredFields: ['organizer', 'title', 'target'],
            formatPattern: '[회사명] 직군 (경력구분)',
            commonIssues: ['날짜누락', '경력구분누락', '회사명누락']
        },
        funding: {
            requiredFields: ['title', 'period'],
            formatPattern: '프로젝트명 펀딩 (~마감일)',
            commonIssues: ['마감일누락', '성격불명']
        },
        education: {
            requiredFields: ['organizer', 'title', 'location'],
            formatPattern: '[주최] 프로그램명 (장소)',
            commonIssues: ['주최불명', '장소누락']
        },
        contest: {
            requiredFields: ['title', 'period'],
            formatPattern: '공모전명 (~마감일)',
            commonIssues: ['마감일누락', '상금누락']
        },
        event: {
            requiredFields: ['organizer', 'title', 'location', 'period'],
            formatPattern: '[주최] 행사명 (장소, 기간)',
            commonIssues: ['장소누락', '기간누락', '주최불명']
        }
    };
    
    return rules[category] || rules.job;
}

// 정확도 계산
function calculateAccuracy(currentText, suggestedText, pageInfo, category) {
    const scores = calculateDetailedScore(currentText, suggestedText, pageInfo, category);
    return Math.round(
        (scores.coreInfo.score / scores.coreInfo.max) * 40 +
        (scores.accuracy.score / scores.accuracy.max) * 30 +
        (scores.readability.score / scores.readability.max) * 20 +
        (scores.consistency.score / scores.consistency.max) * 10
    );
}

// 상세 점수 계산
function calculateDetailedScore(currentText, suggestedText, pageInfo, category) {
    const rules = getCategoryRules(category);
    
    // 핵심 정보 포함 여부 (40%)
    let coreInfoScore = 0;
    const coreInfoMax = rules.requiredFields.length * 10;
    
    rules.requiredFields.forEach(field => {
        if (pageInfo[field] && currentText.includes(pageInfo[field])) {
            coreInfoScore += 10;
        }
    });
    
    // 정보의 정확성 (30%)
    let accuracyScore = 30;
    const accuracyMax = 30;
    
    // 잘못된 정보가 있는지 체크 (간단한 휴리스틱)
    if (currentText.length < 10) accuracyScore -= 10;
    if (!pageInfo.title || !currentText.toLowerCase().includes(pageInfo.title.toLowerCase().substring(0, 5))) {
        accuracyScore -= 10;
    }
    
    // 가독성과 명확성 (20%)
    let readabilityScore = 20;
    const readabilityMax = 20;
    
    if (currentText.length > 100) readabilityScore -= 5;
    if (currentText.length < 10) readabilityScore -= 10;
    if (!/[가-힣]/.test(currentText)) readabilityScore -= 5; // 한글 포함 여부
    
    // 형식 일관성 (10%)
    let consistencyScore = 10;
    const consistencyMax = 10;
    
    if (!currentText.includes('[') && rules.formatPattern.includes('[')) {
        consistencyScore -= 3;
    }
    if (!currentText.includes('(') && rules.formatPattern.includes('(')) {
        consistencyScore -= 3;
    }
    
    return {
        coreInfo: { score: Math.max(0, coreInfoScore), max: coreInfoMax },
        accuracy: { score: Math.max(0, accuracyScore), max: accuracyMax },
        readability: { score: Math.max(0, readabilityScore), max: readabilityMax },
        consistency: { score: Math.max(0, consistencyScore), max: consistencyMax }
    };
}

// 이슈 식별
function identifyIssues(currentText, pageInfo, category) {
    const issues = [];
    const rules = getCategoryRules(category);
    
    rules.requiredFields.forEach(field => {
        if (!pageInfo[field] || !currentText.includes(pageInfo[field])) {
            if (field === 'period') issues.push('날짜누락');
            else if (field === 'organizer') issues.push('주최불명');
            else if (field === 'location') issues.push('장소누락');
            else if (field === 'target') issues.push('대상불명');
        }
    });
    
    if (currentText.length < 10) issues.push('텍스트부족');
    if (currentText.length > 100) issues.push('텍스트과다');
    
    if (issues.length === 0) issues.push('양호');
    
    return issues;
}

// 결과 표시
function displayResults(analysisData, allLinks) {
    showResultsSection();
    updateCategoryOverview(analysisData, allLinks);
    updateFilters();
    
    // 모든 링크 표시 (검증 대상 + 제외 대상)
    const combinedData = allLinks.map(link => {
        const analysisResult = analysisData.find(item => item.id === link.id);
        if (analysisResult) {
            return analysisResult;
        } else {
            // 검증 제외 대상 링크
            return {
                ...link,
                accuracy: 0,
                issues: ['검증 제외'],
                suggestedText: link.text,
                pageInfo: null,
                breakdown: null
            };
        }
    });
    
    updateResultsTable(combinedData);
    updateFooter();
}

// 결과 섹션 표시
function showResultsSection() {
    elements.resultsSection.classList.remove('hidden');
}


// 카테고리 개요 업데이트
function updateCategoryOverview(analysisData, allLinks) {
    // 검증 대상 카테고리만 표시 (정확도 수치 제거)
    const verifiedHtml = Object.entries(CATEGORIES.VERIFIED).map(([key, category]) => {
        const categoryLinks = analysisData.filter(item => item.category === key);
        
        return `
            <div class="category-card ${key}">
                <span class="category-icon">${category.icon}</span>
                <div class="category-name">${category.name}</div>
                <div class="category-stats">${categoryLinks.length}개</div>
            </div>
        `;
    }).join('');
    
    elements.verifiedCategories.innerHTML = verifiedHtml;
}

// 필터 업데이트
function updateFilters() {
    // 카테고리 필터 옵션 추가
    const categoryOptions = Object.entries(CATEGORIES.VERIFIED).map(([key, category]) => 
        `<option value="${key}">${category.name}</option>`
    ).join('');
    
    elements.categoryFilter.innerHTML = `
        <option value="">모든 카테고리</option>
        ${categoryOptions}
    `;
}

// 결과 테이블 업데이트
function updateResultsTable(data) {
    let filteredData = [...data];
    
    // 카테고리 필터만 적용
    const categoryFilter = elements.categoryFilter.value;
    
    if (categoryFilter) {
        filteredData = filteredData.filter(item => item.category === categoryFilter);
    }
    
    // 기본 정렬: 원본 순서 유지 (order 필드 기준)
    filteredData.sort((a, b) => a.order - b.order);
    
    // 테이블 HTML 생성 - 새로운 인라인 상세 정보 형식
    const tableHtml = filteredData.map((item, index) => {
        const category = CATEGORIES.VERIFIED[item.category] || CATEGORIES.EXCLUDED[item.category];
        const accuracyClass = getAccuracyClass(item.accuracy);
        const isVerified = isVerifiedCategory(item.category);
        
        // 상세 분석 정보 생성
        const detailsHtml = generateInlineDetails(item);
        
        return `
            <tr data-link-id="${item.id}" class="link-row ${isVerified ? 'verified' : 'excluded'}">
                <td data-label="#" class="order-cell">
                    ${item.order + 1}
                </td>
                <td data-label="카테고리">
                    <div class="category-badge ${item.category}">
                        ${category.icon} ${category.name}
                    </div>
                </td>
                <td class="text-cell" data-label="링크 텍스트" title="${escapeHtml(item.text)}">
                    <div class="link-text">${escapeHtml(item.text)}</div>
                    <div class="link-url">
                        <a href="${item.url}" target="_blank" class="url-link">${item.url}</a>
                    </div>
                </td>
                <td class="accuracy-cell" data-label="정확도">
                    ${isVerified ? `
                        <div class="accuracy-bar">
                            <div class="accuracy-fill ${accuracyClass}" style="width: ${item.accuracy}%"></div>
                        </div>
                        <span class="accuracy-text">${item.accuracy}%</span>
                    ` : `
                        <span class="excluded-text">검증 제외</span>
                    `}
                </td>
                <td class="details-cell" data-label="상세 분석">
                    ${isVerified ? detailsHtml : '<span class="excluded-text">-</span>'}
                </td>
                <td data-label="액션">
                    <div class="action-buttons">
                        ${isVerified && item.suggestedText ? `<button class="btn-action" onclick="copyText('${escapeHtml(item.suggestedText)}')" title="개선안 복사">📋</button>` : ''}
                        <button class="btn-action" onclick="copyText('${escapeHtml(item.url)}')" title="URL 복사">🔗</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    elements.resultsTbody.innerHTML = tableHtml;
}

// 인라인 상세 정보 생성
function generateInlineDetails(item) {
    if (!item.pageInfo || !item.breakdown) {
        return '<span class="no-data">분석 데이터 없음</span>';
    }
    
    const breakdown = item.breakdown;
    const pageInfo = item.pageInfo;
    
    return `
        <div class="inline-details">
            <div class="detail-row">
                <span class="detail-label">페이지:</span>
                <span class="page-title">${escapeHtml(pageInfo.title)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">설명:</span>
                <span class="page-description">${escapeHtml(pageInfo.description)}</span>
            </div>
            ${pageInfo.main_content && pageInfo.main_content !== 'No content available' ? `
            <div class="detail-row">
                <span class="detail-label">내용:</span>
                <span class="main-content">${escapeHtml(pageInfo.main_content)}</span>
            </div>
            ` : ''}
            <div class="detail-row">
                <span class="detail-label">주최:</span>
                <span class="organizer">${escapeHtml(pageInfo.organizer)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">기간:</span>
                <span class="period">${escapeHtml(pageInfo.period)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">장소:</span>
                <span class="location">${escapeHtml(pageInfo.location)}</span>
            </div>
            ${pageInfo.target && pageInfo.target !== 'Unknown Target' ? `
            <div class="detail-row">
                <span class="detail-label">대상:</span>
                <span class="target">${escapeHtml(pageInfo.target)}</span>
            </div>
            ` : ''}
            ${pageInfo.contact_info && pageInfo.contact_info !== 'No contact info' ? `
            <div class="detail-row">
                <span class="detail-label">연락처:</span>
                <span class="contact">${escapeHtml(pageInfo.contact_info)}</span>
            </div>
            ` : ''}
            ${pageInfo.details && pageInfo.details !== 'No details available' ? `
            <div class="detail-row">
                <span class="detail-label">상세:</span>
                <span class="details">${escapeHtml(pageInfo.details)}</span>
            </div>
            ` : ''}
            <div class="detail-row">
                <span class="detail-label">사이트:</span>
                <span class="site-name">${escapeHtml(pageInfo.site_name || 'Unknown Site')}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">이슈:</span>
                <span class="issues-text">${item.issues.join(', ')}</span>
            </div>
            <div class="score-breakdown">
                <span class="score-item">핵심정보 ${breakdown.coreInfo.score}/${breakdown.coreInfo.max}</span>
                <span class="score-item">정확성 ${breakdown.accuracy.score}/${breakdown.accuracy.max}</span>
                <span class="score-item">가독성 ${breakdown.readability.score}/${breakdown.readability.max}</span>
                <span class="score-item">일관성 ${breakdown.consistency.score}/${breakdown.consistency.max}</span>
            </div>
        </div>
    `;
}

// 정확도 클래스 반환
function getAccuracyClass(accuracy) {
    if (accuracy >= 90) return 'excellent';
    if (accuracy >= 70) return 'good';
    if (accuracy >= 50) return 'fair';
    return 'poor';
}

// HTML 이스케이프
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 푸터 업데이트
function updateFooter() {
    const endTime = Date.now();
    const duration = Math.round((endTime - startTime) / 1000);
    const completionTime = new Date().toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    elements.completionTime.textContent = completionTime;
    elements.duration.textContent = `${duration}초`;
}

// 필터 적용
function applyFilters() {
    if (analysisData.length > 0) {
        // 전체 데이터에서 필터링된 결과 표시
        const allData = [...analysisData];
        updateResultsTable(allData);
    }
}

// 텍스트 복사
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('텍스트가 복사되었습니다.', 'success');
    }).catch(err => {
        showToast('복사에 실패했습니다.', 'error');
    });
}

// 전체 제안 텍스트 복사
function copyAllSuggestions() {
    const suggestions = analysisData.map(item => 
        `${CATEGORIES.VERIFIED[item.category].name}: ${item.suggestedText}`
    ).join('\n');
    
    copyText(suggestions);
}

// 상세 모달 표시
function showDetailModal(linkId) {
    const item = analysisData.find(data => data.id === linkId);
    if (!item) return;
    
    const category = CATEGORIES.VERIFIED[item.category];
    
    // 기본 정보
    document.getElementById('basic-info').innerHTML = `
        <div class="info-grid">
            <span class="info-label">카테고리:</span>
            <span>${category.icon} ${category.name}</span>
            <span class="info-label">URL:</span>
            <span><a href="${item.url}" target="_blank">${item.url}</a></span>
            <span class="info-label">섹션:</span>
            <span>${item.section || '분류되지 않음'}</span>
        </div>
    `;
    
    // 텍스트 비교
    document.getElementById('text-comparison').innerHTML = `
        <div class="comparison-box">
            <div class="comparison-current">
                <strong>현재:</strong> "${item.text}"
            </div>
            <div class="comparison-suggested">
                <strong>제안:</strong> "${item.suggestedText}"
            </div>
        </div>
    `;
    
    // 정확도 상세 분석
    const breakdown = item.breakdown;
    document.getElementById('accuracy-breakdown').innerHTML = `
        <div class="score-item">
            <span>핵심 정보 (40%): ${breakdown.coreInfo.score}/${breakdown.coreInfo.max}점</span>
            <div class="score-details">
                ${item.issues.filter(issue => ['날짜누락', '주최불명', '장소누락', '대상불명'].includes(issue))
                    .map(issue => `<div class="error">⚠️ ${getIssueDescription(issue)}</div>`).join('')}
                ${breakdown.coreInfo.score === breakdown.coreInfo.max ? '<div class="success">✓ 모든 핵심 정보 포함</div>' : ''}
            </div>
        </div>
        <div class="score-item">
            <span>정보 정확성 (30%): ${breakdown.accuracy.score}/${breakdown.accuracy.max}점</span>
            <div class="score-details">
                ${breakdown.accuracy.score === breakdown.accuracy.max ? 
                    '<div class="success">✓ 모든 정보가 정확함</div>' : 
                    '<div class="warning">⚠️ 일부 정보 확인 필요</div>'}
            </div>
        </div>
        <div class="score-item">
            <span>가독성 (20%): ${breakdown.readability.score}/${breakdown.readability.max}점</span>
            <div class="score-details">
                ${breakdown.readability.score < breakdown.readability.max ? 
                    '<div class="warning">⚠️ 텍스트 길이 또는 구조 개선 필요</div>' : 
                    '<div class="success">✓ 가독성 양호</div>'}
            </div>
        </div>
        <div class="score-item">
            <span>형식 일관성 (10%): ${breakdown.consistency.score}/${breakdown.consistency.max}점</span>
            <div class="score-details">
                ${breakdown.consistency.score < breakdown.consistency.max ? 
                    '<div class="warning">⚠️ 오렌지레터 형식 규칙 미준수</div>' : 
                    '<div class="success">✓ 형식 규칙 준수</div>'}
            </div>
        </div>
    `;
    
    // 추출된 페이지 정보
    if (item.pageInfo) {
        document.getElementById('extracted-info').innerHTML = `
            <div class="info-grid">
                <span class="info-label">제목:</span>
                <span>${item.pageInfo.title}</span>
                <span class="info-label">설명:</span>
                <span>${item.pageInfo.description}</span>
                <span class="info-label">기간:</span>
                <span>${item.pageInfo.period}</span>
                <span class="info-label">주최:</span>
                <span>${item.pageInfo.organizer}</span>
                <span class="info-label">대상:</span>
                <span>${item.pageInfo.target}</span>
                <span class="info-label">키워드:</span>
                <span>${item.pageInfo.keywords.join(', ')}</span>
            </div>
        `;
    }
    
    // 모달 표시
    elements.detailModal.classList.remove('hidden');
    
    // 버튼 이벤트 리스너
    document.getElementById('copy-suggested-btn').onclick = () => copyText(item.suggestedText);
    document.getElementById('copy-url-btn').onclick = () => copyText(item.url);
}

// 이슈 설명 반환
function getIssueDescription(issue) {
    const descriptions = {
        '날짜누락': '마감일 정보 누락',
        '주최불명': '주최 기관 표기 개선 필요',
        '장소누락': '장소 정보 누락',
        '대상불명': '대상 정보 불명확',
        '텍스트부족': '링크 텍스트가 너무 짧음',
        '텍스트과다': '링크 텍스트가 너무 김'
    };
    return descriptions[issue] || issue;
}

// 모달 숨기기
function hideModal() {
    elements.detailModal.classList.add('hidden');
}

// 분석 초기화
function resetAnalysis() {
    analysisData = [];
    elements.resultsSection.classList.add('hidden');
    elements.urlInput.value = '';
    showToast('분석이 초기화되었습니다.', 'success');
}

// 로딩 표시
function showLoading() {
    elements.loadingOverlay.classList.remove('hidden');
    elements.analyzeBtn.disabled = true;
    document.title = '🍊 오렌지레터 링크 검증 도구 (분석 중...)';
}

// 로딩 숨기기
function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
    elements.analyzeBtn.disabled = false;
    document.title = '🍊 오렌지레터 링크 검증 도구 (분석 완료)';
}

// 로딩 텍스트 업데이트
function updateLoadingText(text) {
    elements.loadingText.textContent = text;
}

// 진행률 업데이트
function updateProgress(current, total, text) {
    const percentage = total > 0 ? (current / total) * 100 : 0;
    elements.progressFill.style.width = `${percentage}%`;
    elements.progressText.textContent = `${current}/${total}`;
    if (text) elements.loadingText.textContent = text;
    
    // 브라우저 title에도 진행률 표시
    const progressPercent = Math.round(percentage);
    document.title = `🍊 오렌지레터 링크 검증 도구 (${progressPercent}% - ${current}/${total})`;
}

// 토스트 메시지 표시
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// URL 유효성 검사
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}