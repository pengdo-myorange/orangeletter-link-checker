// Vercel Edge Config를 사용한 글로벌 캐싱
// 이 기능을 사용하려면 Vercel 대시보드에서 Edge Config Store를 생성해야 합니다

export const edgeConfig = {
    // 자주 스크래핑되는 URL의 결과를 캐시
    cacheConfig: {
        // 캐시 유효 시간 (초)
        ttl: {
            scrapeResult: 3600,      // 1시간
            newsletterHtml: 1800,    // 30분
            analysisResult: 86400    // 24시간
        },
        
        // 최대 캐시 항목 수
        maxItems: 1000,
        
        // 캐시 키 프리픽스
        prefix: 'orangeletter_'
    },
    
    // 성능 설정
    performance: {
        // 동시 처리 배치 크기 (Vercel Pro)
        batchSize: 20,
        
        // API 타임아웃 (밀리초)
        apiTimeout: 30000,
        
        // 재시도 설정
        retry: {
            attempts: 2,
            delay: 1000
        }
    },
    
    // 허용된 도메인 목록 (보안)
    allowedDomains: [
        'stibee.com',
        'orangeletter.net',
        'habitat.careers.team',
        'saramin.co.kr',
        'wanted.co.kr',
        'jobkorea.co.kr',
        'happybean.naver.com',
        'tumblbug.com',
        'socialfunch.org',
        'cherry.charity'
    ]
};

// Edge Config 읽기
export async function getEdgeConfig(key) {
    if (process.env.EDGE_CONFIG) {
        try {
            const { get } = await import('@vercel/edge-config');
            return await get(key);
        } catch (error) {
            console.warn('Edge Config read failed:', error);
            return null;
        }
    }
    return null;
}

// Edge Config 캐시 조회
export async function getCachedResult(key) {
    const cachedKey = `${edgeConfig.cacheConfig.prefix}${key}`;
    const cached = await getEdgeConfig(cachedKey);
    
    if (cached && cached.timestamp) {
        const age = Date.now() - cached.timestamp;
        const ttl = edgeConfig.cacheConfig.ttl[cached.type] || 3600;
        
        if (age < ttl * 1000) {
            return cached.data;
        }
    }
    
    return null;
}