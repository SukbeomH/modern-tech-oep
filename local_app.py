import os
import json
from typing import Dict, List
from dotenv import load_dotenv
import streamlit as st
from anthropic import Anthropic
import sqlite3
from datetime import datetime
from typing import Dict

# 환경 변수 로드
load_dotenv()

# Anthropic 클라이언트 초기화
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL ="claude-3-5-sonnet-20241022"

class MiddlewareDatabase:
    def __init__(self, db_name: str = 'middleware_history.db'):
        self.db_name = db_name
        self.create_schema()

    def create_schema(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS middleware_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            input_text TEXT,
            requirements TEXT,
            initial_code TEXT,
            initial_documentation TEXT,
            validation TEXT,
            improved_code TEXT,
            improved_documentation TEXT
        )''')
        conn.commit()
        conn.close()

    def save_results(self, initial_result, improved_result=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO middleware_history 
            (timestamp, input_text, requirements, initial_code, 
             initial_documentation, validation, improved_code, improved_documentation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            initial_result.get('input_text', ''),
            json.dumps(initial_result.get('requirements', {})),
            initial_result.get('code', ''),
            initial_result.get('documentation', ''),
            initial_result.get('validation', ''),
            improved_result.get('improved_code', '') if improved_result else '',
            improved_result.get('improved_documentation', '') if improved_result else ''
        ))
        
        conn.commit()
        conn.close()

    def get_all_history(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM middleware_history
            ORDER BY timestamp DESC
        ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results

class ParsingAgent:
    def __init__(self):
        self.client = anthropic
        
    def parse_natural_language(self, text: str) -> Dict:
        prompt = f"""
        다음 자연어 요청을 분석하여 JSON 형태로 구조화해주세요.

        요청: {text}

        다음 항목들을 반드시 포함해주세요:
        1. "intent": 요청의 주요 의도
        2. "entities": 필요한 주요 개체들의 배열
        3. "requirements": 구체적인 요구사항들의 배열
        4. "constraints": 제약사항이나 고려사항들의 배열
        5. "parameters": 필요한 설정값들을 키-값 쌍으로

        규칙:
        1. 응답은 반드시 유효한 JSON 형식이어야 합니다.
        2. JSON 외의 다른 텍스트는 포함하지 마세요.
        3. 모든 키는 영문 소문자로 작성하세요.
        4. 값은 한글 또는 영문으로 작성할 수 있습니다.
        """
        
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        
        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {str(e)}")
            st.write("원본 응답:", response.content[0].text)
            return {}

class SampleRequestAgent:
    def __init__(self):
        self.client = anthropic
        
    def generate_sample_requests(self, n: int = 5) -> List[str]:
        prompt = f"""
        HTTP Request 처리를 위한 미들웨어 요청 {n}개를 JSON 배열로 생성해주세요.
        
        고려해야 할 HTTP Request 관련 카테고리:
        1. 요청 헤더 검증/수정 (예: Content-Type, Authorization 등)
        2. 요청 본문 검증/변환 (예: JSON 유효성 검사, 크기 제한 등)
        3. 요청 파라미터 처리 (예: URL 파라미터 검증, 쿼리 파라미터 정제 등)
        4. 요청 보안 관련 (예: CORS, XSS 방지, JWT 검증 등)
        5. 요청 최적화 (예: 압축, 캐싱, 요청 횟수 제한 등)

        응답 예시:
        [
            "들어오는 모든 HTTP 요청의 Content-Type이 application/json인지 검증하는 미들웨어",
            "요청 헤더에 유효한 JWT 토큰이 있는지 확인하는 미들웨어",
            "POST 요청의 본문 크기를 5MB로 제한하는 미들웨어"
        ]

        규칙:
        1. 각 요청은 구체적인 HTTP Request 처리와 관련되어야 합니다.
        2. 실제 웹 애플리케이션에서 활용 가능한 현실적인 시나리오여야 합니다.
        3. 보안, 성능, 데이터 무결성 등 다양한 측면을 고려해야 합니다.
        4. 응답은 반드시 JSON 배열 형식이어야 합니다.
        5. 각 요청은 명확하고 구체적이어야 합니다.
        6. 최소한 3개 이상의 요청을 만들어야 합니다.

        최대한 실용적이고 일반적으로 필요한 HTTP Request 미들웨어 요청을 생성해주세요.
        """
        
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        
        try:
            samples = json.loads(response.content[0].text)
            # 추가 검증: 각 샘플이 HTTP Request 관련 키워드를 포함하는지 확인
            http_keywords = ['http', 'request', 'header', 'body', 'payload', 'content-type', 
                           'authorization', 'token', 'jwt', 'cors', 'method', 'get', 'post', 
                           'put', 'delete', 'url', 'query', 'parameter']
            
            validated_samples = []
            for sample in samples:
                sample_lower = sample.lower()
                if any(keyword in sample_lower for keyword in http_keywords):
                    validated_samples.append(sample)
            
            return validated_samples if validated_samples else []
            
        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {str(e)}")
            st.write("원본 응답:", response.content[0].text)
            return []

class DocumentationAgent:
    def __init__(self):
        self.client = anthropic
        
    def generate_documentation(self, code: str) -> str:
        prompt = f"""
        다음 Python 코드에 대한 문서를 생성해주세요:
        코드: {code}
        응답은 적절한 주석과 설명을 포함해야 합니다.
        """
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            
            # content가 리스트인 경우 첫 번째 요소의 text 속성 사용
            if isinstance(response.content, list):
                if len(response.content) > 0:
                    return response.content[0].text
                else:
                    return "문서 생성에 실패했습니다."
            # content가 단일 객체인 경우 직접 text 속성 사용
            else:
                return response.content.text
                
        except Exception as e:
            return f"문서 생성 중 오류 발생: {str(e)}"

class ValidationAgent:
    def __init__(self):
        self.client = anthropic
        
    def validate_middleware(self, code: str, requirements: Dict) -> str:
        prompt = f"""
        다음 Python 코드가 주어진 요구사항을 충족하는지 검증해주세요:

        코드: {code}

        요구사항: {json.dumps(requirements, ensure_ascii=False, indent=2)}

        검증 결과와 개선 사항을 알려주세요.
        """
        
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        
        return response.content[0].text

class MiddlewareAgent:
    def __init__(self):
        self.client = anthropic

    def generate_middleware(self, requirements: Dict) -> str:
        prompt = f"""
        다음 요구사항에 맞는 HTTP 미들웨어 코드를 생성해주세요:
        {json.dumps(requirements, ensure_ascii=False, indent=2)}

        규칙:
        1. 코드는 Python으로 작성해주세요.
        2. 필요한 주석을 포함해주세요.
        3. 코드외에 다른 설명은 포함하지 마세요.
        4. 함수는 "HTTP Request" 형태를 입력받습니다.
        """
        
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.content[0].text

    def generate_improved_code(self, original_code: str, validation_feedback: str) -> str:
        """검증 결과를 바탕으로 개선된 코드를 생성합니다."""
        improvement_analysis = self._analyze_feedback(validation_feedback)
        
        prompt = f"""
        주어진 코드를 다음 검증 결과와 분석을 바탕으로 개선해주세요:

        원본 코드:
        {original_code}

        검증 결과:
        {validation_feedback}

        개선 필요 영역:
        {json.dumps(improvement_analysis, ensure_ascii=False, indent=2)}

        개선 규칙:
        1. 검증 결과에서 지적된 모든 문제를 해결해야 합니다.
        2. 에러 처리와 예외 상황 대응을 강화해야 합니다.
        3. 코드 성능과 보안을 개선해야 합니다.
        4. 기존 기능은 모두 유지하면서 개선해야 합니다.
        5. 모든 변경사항에 대해 주석으로 설명을 추가해야 합니다.
        6. HTTP 미들웨어의 표준 패턴을 따라야 합니다.

        응답 형식:
        1. Python 코드만 제공해주세요.
        2. 추가 설명이나 마크다운은 포함하지 마세요.
        """

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.content[0].text

    def _analyze_feedback(self, validation_feedback: str) -> Dict[str, List[str]]:
        """검증 피드백을 분석하여 개선이 필요한 영역을 식별합니다."""
        prompt = f"""
        다음 검증 피드백을 분석하여 개선이 필요한 영역을 JSON 형식으로 분류해주세요:

        피드백:
        {validation_feedback}

        다음 카테고리로 분류해주세요:
        1. "security_issues": 보안 관련 문제점
        2. "performance_issues": 성능 관련 문제점
        3. "error_handling": 에러 처리 관련 문제점
        4. "code_structure": 코드 구조 관련 문제점
        5. "functionality_issues": 기능 관련 문제점

        각 카테고리는 구체적인 문제점들의 배열이어야 합니다.
        """

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {
                "security_issues": [],
                "performance_issues": [],
                "error_handling": [],
                "code_structure": [],
                "functionality_issues": []
            }

    def verify_improvements(self, original_code: str, improved_code: str, requirements: Dict) -> bool:
        """개선된 코드가 원래 요구사항을 충족하면서 실제로 개선되었는지 확인합니다."""
        prompt = f"""
        개선된 코드가 원래 요구사항을 충족하면서 실제로 개선되었는지 검증해주세요.

        원본 코드:
        {original_code}

        개선된 코드:
        {improved_code}

        요구사항:
        {json.dumps(requirements, ensure_ascii=False, indent=2)}

        True 또는 False로만 응답해주세요.
        """

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        return "true" in response.content[0].text.lower()
    
class DocumentationAgent:
    def __init__(self):
        self.client = anthropic
    def generate_documentation(self, code: str, is_improved: bool = False, original_code: str = None) -> str:
        """코드에 대한 문서를 생성합니다."""
        prompt = f"""
        다음 Python 코드에 대한 문서를 생성해주세요:
        
        코드: {code}
        """
        
        if is_improved and original_code:
            prompt += f"""
            이 코드는 다음 원본 코드의 개선 버전입니다:
            {original_code}
            
            문서에 다음 내용을 포함해주세요:
            1. 개선된 부분 설명
            2. 성능/보안 개선사항
            3. 변경된 로직 설명
            """
        
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        return response.content[0].text
    
    def generate_changes_summary(self, original_code: str, improved_code: str, validation_feedback: str) -> str:
        """코드 변경사항을 요약합니다."""
        prompt = f"""
            다음 두 버전의 코드 차이점을 분석하여 요약해주세요:
            
            원본 코드:
            {original_code}
            
            개선된 코드:
            {improved_code}
            
            검증 피드백:
            {validation_feedback}
            
            요약 포함 사항:
            1. 주요 변경사항 목록
            2. 개선된 기능/성능
            3. 보안 강화 사항
            4. 코드 구조 변경
            5. 새로운 예외 처리
            
            응답 형식:
            1. Markdown 형식
            2. 명확한 섹션 구분
            3. 중요 변경사항 강조
            """

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        return response.content.text

    def generate_api_documentation(self, code: str, requirements: Dict) -> str:
        """API 문서를 생성합니다."""
        prompt = f"""
            다음 미들웨어 코드에 대한 API 문서를 생성해주세요:
            
            코드:
            {code}
            
            요구사항:
            {json.dumps(requirements, ensure_ascii=False, indent=2)}
            
            문서 포함 사항:
            1. API 엔드포인트 설명
            2. 요청/응답 형식
            3. 미들웨어 동작 방식
            4. 에러 처리 방법
            5. 설정 옵션
            6. 사용 예시
            
            응답 형식:
            1. Markdown 형식
            2. OpenAPI 스펙 호환
            3. 명확한 예시 포함
            """

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.content.text

class NLPMiddlewareGenerator:
    def __init__(self):
        self.parsing_agent = ParsingAgent()
        self.sample_request_agent = SampleRequestAgent()
        self.middleware_agent = MiddlewareAgent()
        self.documentation_agent = DocumentationAgent()
        self.validation_agent = ValidationAgent()
        self.db = MiddlewareDatabase()
        self.search_manager = SearchManager(self.db)
    

    def generate_with_rag(self, user_input: str) -> Dict:
        # 유사한 이전 사례 검색
        similar_cases = self.search_manager.semantic_search(user_input)
        
        # 컨텍스트 구성
        context = self._prepare_context(similar_cases)
        
        # RAG 기반 생성
        return self._generate_with_context(user_input, context)

class EmbeddingManager:
    def __init__(self):
        self.client = anthropic
    
    def create_embeddings(self, text: str, chunk_size: int = 1000) -> List[Dict]:
        chunks = self._create_chunks(text, chunk_size)
        embeddings = []
        
        for chunk in chunks:
            embedding = self._get_embedding(chunk)
            embeddings.append({
                'text': chunk,
                'embedding': embedding
            })
        
        return embeddings
    
    def _create_chunks(self, text: str, chunk_size: int) -> List[str]:
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

class SearchManager:
    def __init__(self, db: MiddlewareDatabase):
        self.db = db
        self.embedding_manager = EmbeddingManager()
    
    def semantic_search(self, query: str, top_k: int = 3) -> List[Dict]:
        query_embedding = self.embedding_manager.create_embeddings(query)[0]
        
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        
        # 벡터 유사도 검색
        cursor.execute('''
            SELECT h.*, vector_distance(e.embedding, ?) as distance
            FROM middleware_history h
            JOIN embeddings e ON h.id = e.history_id
            ORDER BY distance ASC
            LIMIT ?
        ''', (query_embedding['embedding'], top_k))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

class RetrievalManager:
    def __init__(self, db: MiddlewareDatabase):
        self.db = db
        self.client = anthropic
        
    def retrieve_similar_cases(self, query: str, top_k: int = 3) -> List[Dict]:
        """유사한 이전 사례를 검색합니다."""
        history = self.db.get_all_history()
        similar_cases = []
        
        for case in history:
            if any(keyword in case['input_text'].lower() 
                  for keyword in query.lower().split()):
                similar_cases.append(case)
                if len(similar_cases) >= top_k:
                    break
        
        return similar_cases

    def generate_enhanced_requirements(self, query: str, similar_cases: List[Dict]) -> Dict:
        """유사 사례를 바탕으로 향상된 요구사항을 생성합니다."""
        prompt = f"""
            다음 요청과 유사한 이전 사례들을 바탕으로 향상된 요구사항을 생성해주세요:
            
            새로운 요청: {query}
            
            유사 사례들:
            {json.dumps([case['requirements'] for case in similar_cases], indent=2)}
            
            응답 규칙:
            1. 반드시 유효한 JSON 형식으로 응답해야 합니다
            2. 모든 키는 영문 소문자로 작성하세요
            3. JSON 외의 다른 텍스트는 포함하지 마세요
            4. 빈 응답은 허용되지 않습니다
            """
        
        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # 응답 검증
            if not response.content or not response.content[0].text.strip():
                return {"error": "Empty response received"}
                
            # JSON 파싱 시도
            try:
                return json.loads(response.content[0].text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값 반환
                return {
                    "intent": "unknown",
                    "entities": [],
                    "requirements": [],
                    "constraints": [],
                    "parameters": {}
                }
                
        except Exception as e:
            return {"error": f"Failed to generate requirements: {str(e)}"}

    
    def generate_enhanced_code(self, requirements: Dict, similar_cases: List[Dict]) -> str:
        """유사 사례를 바탕으로 향상된 코드를 생성합니다."""
        prompt = f"""
        다음 요구사항과 유사한 이전 사례들을 참고하여 향상된 코드를 생성해주세요:
        
        요구사항: {json.dumps(requirements, indent=2)}

        규칙:
        1. 코드는 Python으로 작성해주세요.
        2. 필요한 주석을 포함해주세요.
        3. 코드외에 다른 설명은 포함하지 마세요.
        4. 함수는 "HTTP Request" 형태를 입력받습니다.
        
        참고할 이전 코드들:
        {json.dumps([case['initial_code'] for case in similar_cases], indent=2)}
        """
        
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        return response.content[0].text

def rag_middleware_tab():
    st.header("RAG 기반 미들웨어 생성")
    
    db = MiddlewareDatabase()
    retrieval_manager = RetrievalManager(db)
    
    user_input = st.text_area("미들웨어 요구사항을 입력하세요:", height=100)
    
    if st.button("RAG 기반 미들웨어 생성"):
        if not user_input:
            st.error("요구사항을 입력해주세요.")
            return
            
        history = db.get_all_history()
        if not history:
            st.warning("학습할 이전 데이터가 없습니다. 기본 생성으로 진행합니다.")
            return
        
        # 1. 유사 사례 검색
        with st.spinner("유사한 사례 검색 중..."):
            similar_cases = retrieval_manager.retrieve_similar_cases(user_input)
            
            if similar_cases:
                st.subheader("📚 유사한 이전 사례")
                for idx, case in enumerate(similar_cases, 1):
                    with st.expander(f"사례 {idx}: {case['input_text'][:50]}..."):
                        st.json(json.loads(case['requirements']))
                        st.code(case['initial_code'], language="python")
        
        # 2. 향상된 요구사항 생성
        with st.spinner("RAG 기반 요구사항 분석 중..."):
            enhanced_requirements = retrieval_manager.generate_enhanced_requirements(
                user_input, similar_cases
            )
            st.subheader("📋 향상된 요구사항")
            st.json(enhanced_requirements)
        
        # 3. 향상된 코드 생성
        with st.spinner("향상된 코드 생성 중..."):
            enhanced_code = retrieval_manager.generate_enhanced_code(
                enhanced_requirements, similar_cases
            )
            st.subheader("💻 생성된 코드")
            st.code(enhanced_code, language="python")

def show_history_tab():
    st.header("저장된 미들웨어 히스토리")

     # 데이터베이스 관리 버튼들
    if st.button("🔄 데이터베이스 포맷"):
        try:
            db = MiddlewareDatabase()
            conn = sqlite3.connect(db.db_name)
            cursor = conn.cursor()
            
            # 테이블 재생성
            cursor.execute("DROP TABLE IF EXISTS middleware_history")
            db.create_schema()
            
            st.success("데이터베이스가 포맷되었습니다.")
            conn.close()
        except Exception as e:
            st.error(f"포맷 중 오류가 발생했습니다: {str(e)}")
    
    # 구분선 추가
    st.divider()

    db = MiddlewareDatabase()
    history = db.get_all_history()
    
    if not history:
        st.info("저장된 미들웨어 정보가 없습니다.")
        return
    
    # 날짜별 필터링
    dates = [datetime.fromisoformat(h['timestamp']).date() for h in history]
    unique_dates = sorted(set(dates), reverse=True)
    selected_date = st.selectbox("날짜 선택", unique_dates)
    
    # 선택된 날짜의 기록만 표시
    filtered_history = [
        h for h in history 
        if datetime.fromisoformat(h['timestamp']).date() == selected_date
    ]
    
    for entry in filtered_history:
        with st.expander(f"📝 {entry['timestamp']} - {entry['input_text'][:50]}..."):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("초기 버전")
                st.json(json.loads(entry['requirements']))
                st.code(entry['initial_code'], language="python")
                st.markdown(entry['initial_documentation'])
                st.markdown(entry['validation'])
            
            with col2:
                st.subheader("개선된 버전")
                if entry['improved_code']:
                    st.code(entry['improved_code'], language="python")
                    st.markdown(entry['improved_documentation'])
                else:
                    st.info("개선된 버전이 없습니다.")

def generate_middleware_tab():
    # 세션 상태 초기화를 가장 먼저 수행
    if 'initial_result' not in st.session_state:
        st.session_state['initial_result'] = {
            'input_text': '',
            'requirements': None,
            'code': None,
            'documentation': None,
            'validation': None
        }
    
    if 'improved_result' not in st.session_state:
        st.session_state['improved_result'] = {
            'improved_code': None,
            'improved_documentation': None
        }
        
    # 데이터베이스 초기화
    db = MiddlewareDatabase()

    # 좌우 컬럼 생성
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.header("초기 미들웨어 생성")
    
        # 샘플 요청 생성 버튼
        if st.button("샘플 요청 생성"):

            generator = NLPMiddlewareGenerator()
            
            with st.spinner("샘플 요청 생성 중..."):
                samples = generator.sample_request_agent.generate_sample_requests()
                if samples:
                    st.write("샘플 요청:")
                    for i, sample in enumerate(samples, 1):
                        st.write(f"{i}. {sample}")
                else:
                    st.error("샘플 요청을 생성하지 못했습니다.")
        
        # 사용자 입력
        user_input = st.text_area("미들웨어 요구사항을 자연어로 입력하세요:", height=100)
        
        if st.button("미들웨어 생성"):
            if not user_input:
                st.error("요구사항을 입력해주세요.")
                return
                
            generator = NLPMiddlewareGenerator()
            
            # 진행 상황을 보여줄 컨테이너
            progress_container = st.empty()
            
            # 1. 요구사항 분석
            with st.spinner("요구사항 분석 중..."):
                requirements = generator.parsing_agent.parse_natural_language(user_input)
                st.session_state['initial_result']['requirements'] = requirements
                
                st.subheader("📋 요구사항 분석")
                st.json(requirements)
            
            # 2. 코드 생성
            with st.spinner("미들웨어 코드 생성 중..."):
                code = generator.middleware_agent.generate_middleware(requirements)
                st.session_state['initial_result']['code'] = code
                
                st.subheader("💻 생성된 코드")
                st.code(code, language="python")
            
            # 3. 문서 생성
            with st.spinner("문서 생성 중..."):
                documentation = generator.documentation_agent.generate_documentation(code)
                st.session_state['initial_result']['documentation'] = documentation
                
                st.subheader("📚 문서")
                st.markdown(documentation)
            
            # 4. 검증
            with st.spinner("코드 검증 중..."):
                validation = generator.validation_agent.validate_middleware(code, requirements)
                st.session_state['initial_result']['validation'] = validation
                
                st.subheader("✅ 검증 결과")
                st.markdown(validation)
        
        # 저장된 결과가 있으면 표시
        elif st.session_state['initial_result']['code']:
            st.subheader("📋 요구사항 분석")
            st.json(st.session_state['initial_result']['requirements'])
            
            st.subheader("💻 생성된 코드")
            st.code(st.session_state['initial_result']['code'], language="python")
            
            st.subheader("📚 문서")
            st.markdown(st.session_state['initial_result']['documentation'])
            
            st.subheader("✅ 검증 결과")
            st.markdown(st.session_state['initial_result']['validation'])
    
    with right_col:
        st.header("개선된 미들웨어")
        
        if st.session_state['initial_result']['code']:
            if st.button("💡 개선된 버전 생성"):
                generator = NLPMiddlewareGenerator()
                
                with st.spinner("개선된 버전 생성 중..."):
                    # 개선된 코드 생성
                    improved_code = generator.middleware_agent.generate_improved_code(
                        st.session_state['initial_result']['code'],
                        st.session_state['initial_result']['validation']
                    )
                    
                    # 개선된 문서 생성
                    improved_documentation = generator.documentation_agent.generate_documentation(
                        improved_code
                    )
                    
                    # 세션 상태 업데이트
                    st.session_state['improved_result'].update({
                        'improved_code': improved_code,
                        'improved_documentation': improved_documentation
                    })
            
            # 개선된 결과가 있으면 표시
            if st.session_state['improved_result']['improved_code'] and st.session_state['improved_result']['improved_documentation']:
                # 화면에 제시
                st.subheader("🚀 개선된 코드")
                st.code(st.session_state['improved_result']['improved_code'], language="python")
                st.subheader("📚 개선된 문서")
                st.markdown(st.session_state['improved_result']['improved_documentation'])
                # 초기 결과와 개선된 결과를 함께 저장
                try:
                    db.save_results(
                        initial_result={
                            'input_text': user_input,
                            **st.session_state['initial_result']
                        },
                        improved_result=st.session_state['improved_result']
                    )
                    st.success("결과가 성공적으로 저장되었습니다!")
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {str(e)}")

# 페이지 레이아웃을 wide로 설정
st.set_page_config(layout="wide")

def main():
    st.title("LLM Based 미들웨어 생성 Agent")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["미들웨어 생성", "히스토리 조회", "RAG 기반 생성"])
    
    with tab1:
        generate_middleware_tab()
    
    with tab2:
        show_history_tab()
        
    with tab3:
        rag_middleware_tab()

    # 세션 상태 초기화
    if 'initial_result' not in st.session_state:
        st.session_state['initial_result'] = {
            'requirements': None,
            'code': None,
            'documentation': None,
            'validation': None
        }
    
    if 'improved_result' not in st.session_state:
        st.session_state['improved_result'] = {
            'improved_code': None,
            'improved_documentation': None
        }

if __name__ == "__main__":
    main()
