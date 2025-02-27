# 🌐 LLM 기반 HTTP 미들웨어 자동화 시스템
## 📖 1. 시스템 개요

## 🛠️ 1.1 프로젝트 배경

최근 웹 애플리케이션과 API의 확산으로 HTTP 요청 처리와 관련된 요구사항이 점점 복잡해지고 있습니다.  
**IP 필터링, 요청 검증, 로깅, 콘텐츠 변환** 등 HTTP 요청을 처리하는 미들웨어는 개발자가 직접 코드를 작성해야 했으나, 이는 시간이 많이 소요되고 오류 가능성이 높습니다.

본 프로젝트는 **AI 기반 HTTP 미들웨어 자동화 시스템**으로, 자연어 요청을 기반으로 미들웨어 코드를 생성하고, 이를 검증 및 개선하여 **개발 효율성과 코드 품질**을 극대화합니다.

## 🔑 2. 핵심 컴포넌트

## 🧠 2.1 자연어 처리기 (ParsingAgent)

- **기능**: 사용자의 자연어 입력을 분석하여 JSON 형식의 요구사항을 생성.
    
- **예시 입력**:  
    `"러시아에서 오는 요청을 차단해줘"`
    
- **출력 예시**:
```json
{   
	"intent": "block_request",  
	"entities": ["Russia"],  
	"requirements": ["Block requests from Russia"],  
	"constraints": [],  
	"parameters": {
		"country": "Russia"
	} 
}
```
    

## 🔍 2.2 HTTP 요청 분석기 (Request Analyzer)

- **기능**: 샘플 HTTP 요청 데이터를 분석하여 주요 특성을 추출.
    
- **분석 대상**:
    
    - HTTP Method (GET, POST 등)
        
    - Headers (Content-Type, Authorization 등)
        
    - Body 및 Query Parameters
        
    - 요청의 Path 및 IP 주소
        
- **활용 사례**:
    
    - CORS 정책 검증
        
    - JWT 토큰 유효성 검사
        
    - URL 파라미터 정제
        

## 💻 2.3 함수 생성기 (MiddlewareAgent)

- **기능**: JSON 요구사항을 기반으로 Python 코드를 자동 생성.
    
- **지원 기능**:
    
    - IP 기반 필터링
        
    - 콘텐츠 필터링
        
    - 요청 변환 및 헤더 수정
        
    - 로깅 및 캐싱
        
- **출력 예시 코드**:
```python
def middleware(request):     
	if request.headers.get("X-Country") == "Russia":        
		return Response("Blocked", status=403)    
	return next(request)
```
    

## ✅ 2.4 테스트 엔진 (ValidationAgent)

- **기능**: 생성된 코드가 요구사항을 충족하는지 검증하고 피드백 제공.
    
- **검증 프로세스**:
    
    - 구조 검증: 문법 오류 확인.
        
    - 기능 검증: 요구사항 충족 여부 확인.
        
    - 보안 검증: OWASP Top 10 기준으로 보안 문제 식별.
        
- **출력 예시**:
```text
검증 결과: 
	- 보안 문제: JWT 토큰 유효성 검사 누락 
	- 성능 문제: 캐싱 로직 없음 개선 필요 사항: 
	- 헤더 검사 강화
```
    

## 📚 2.5 문서화 에이전트 (DocumentationAgent)

- **기능**: 생성된 코드에 대한 주석 및 API 문서를 자동 작성.
    
- **출력 예시**:
```text
# 이 미들웨어는 러시아에서 오는 모든 요청을 차단합니다. 
# 사용 예시: 
# request.headers["X-Country"] = "Russia"
```

## 🗂️ 2.6 데이터베이스 관리 (MiddlewareDatabase)

- SQLite를 이용해 작업 히스토리를 저장하고 관리.
    
- **테이블 스키마**:
```SQL
    CREATE TABLE middleware_history 
    (     
	    id INTEGER PRIMARY KEY AUTOINCREMENT, 
	    timestamp TEXT,    
	    input_text TEXT,    
	    requirements TEXT,    
	    initial_code TEXT,    
	    initial_documentation TEXT,    
	    validation TEXT,    
	    improved_code TEXT,    
	    improved_documentation TEXT 
	)
```
    

## 🔄 3. 작동 프로세스

1. 사용자가 자연어로 요청 입력 (예: `"러시아에서 오는 요청을 차단해줘"`).
    
2. ParsingAgent가 입력 내용을 분석하여 JSON 형태의 요구사항 도출.
    
3. MiddlewareAgent가 요구사항에 맞는 Python 코드를 자동 생성.
    
4. SampleRequestAgent가 샘플 HTTP 요청 시나리오를 생성.
    
5. ValidationAgent가 생성된 코드를 검증하고 피드백 제공.
    
6. DocumentationAgent가 코드에 대한 문서를 작성.
    
7. 필요 시 개선된 코드와 문서를 추가적으로 생성.
    

## 📋 4. 주요 기능 요약

| 기능                | 설명                                                          |
| ------------------- | ------------------------------------------------------------- |
| 📋 **요구사항 분석** | 사용자의 자연어 입력을 구조화된 JSON 객체로 변환.             |
| 💻 **코드 생성**     | Python 기반의 미들웨어 함수 자동 생성.                        |
| ✅ **코드 검증**     | ValidationAgent를 통해 보안, 성능, 요구사항 충족 여부를 검증. |
| 🚀 **개선 프로세스** | 검증 피드백을 바탕으로 개선된 코드와 문서를 생성.             |
| 📚 **문서화 지원**   | DocumentationAgent를 활용한 자동화된 코드 주석 및 설명 작성.  |

## 🗄️ 5. 데이터 저장 및 관리

## SQLite 데이터베이스 구조 (`middleware_history`)

| Column Name              | Type    | Description                 |
| ------------------------ | ------- | --------------------------- |
| `id`                     | INTEGER | 고유 식별자                 |
| `timestamp`              | TEXT    | 작업 시간                   |
| `input_text`             | TEXT    | 사용자가 입력한 자연어 요청 |
| `requirements`           | TEXT    | 분석된 요구사항(JSON)       |
| `initial_code`           | TEXT    | 최초로 생성된 미들웨어 코드 |
| `initial_documentation`  | TEXT    | 최초로 작성된 문서          |
| `validation`             | TEXT    | 검증 결과                   |
| `improved_code`          | TEXT    | 개선된 코드                 |
| `improved_documentation` | TEXT    | 개선된 문서                 |

## 🌟 6. 기대 효과

| 구분                 | 기존 방식                  | AI 기반 솔루션     |
| -------------------- | -------------------------- | ------------------ |
| ⏱️ **코드 작성 시간** | 수 시간 소요               | 실시간 생성 가능   |
| 🎯 **검증 정확도**    | 사람 의존 (오류 발생 가능) | AI가 정확히 검증   |
| 📝 **문서 작성 시간** | 수동 작업 필요             | 실시간 문서화      |
| 💰 **유지보수 비용**  | 높음                       | 낮음 (자동 최적화) |

## 🚀 7. 결론 및 차별점

본 솔루션은 AI 기술을 활용하여 HTTP 미들웨어 개발 과정을 개선합니다.

✔ 자연어 입력만으로 요구사항 분석부터 코드 생성까지 자동화  
✔ 검증 및 피드백 과정을 통해 고품질 코드를 보장  
✔ 지속적인 데이터 학습으로 점진적 성능 향상  