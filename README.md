# DynoLink - Dynalist to Notion 자동 동기화

Dynalist에서 작성한 일일 기록을 자동으로 Notion 데이터베이스로 동기화하는 도구입니다.
프로젝트별, 용도별로 여러 Notion 데이터베이스에 자동 분류하고, 계층적 태그 구조로 정보를 조직화합니다.

---

## 🎯 주요 기능

✅ **다중 Dynalist 문서 지원**
- 메인 문서 + 개념 문서 등 여러 문서에서 동시에 데이터 수집
- 문서별로 다른 처리 방식 적용 가능

✅ **3단계 계층 구조**
- **대분류** (Domain) - 첫 번째 태그
- **중분류** (Category) - 두 번째 태그
- **소분류+** (Tags) - 3번째 이후 모든 태그 (다중 선택)

✅ **3개 Notion 데이터베이스 자동 분류**
- 개념/단어/용어 - 개념 문서의 모든 항목 + 메인 문서의 기본값
- 업무관련 - `#업무관련` 태그가 있는 항목
- 개인용무 - `#개인용무` 태그가 있는 항목

✅ **유연한 메모 관리**
- 2000자 초과 메모는 자동으로 분할
- Notion API 제한 자동 해결

✅ **다양한 실행 옵션**
- `--once` : 일회성 실행
- `--date [YYYY-MM-DD]` : 특정 날짜 동기화
- `--date-range [시작:종료]` : 날짜 범위 동기화
- `--last-days [N]` : 최근 N일간 동기화
- 스케줄러 모드 : 매일 자정 자동 실행

---

## 📋 설치 방법

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd DynoLink
```

### 2. Python 환경 설정
```bash
# Python 3.9 이상 필요
python3 --version

# 패키지 설치
pip3 install -r requirements.txt
```

### 3. 필수 API 키 준비

#### Dynalist API 키
1. [Dynalist](https://dynalist.io) 로그인
2. 설정 → API + Integrations
3. API Token 복사

#### Notion API 키
1. [Notion Developers](https://developers.notion.com) 방문
2. 새 Integration 생성
3. Internal Integration Token 복사
4. 기존 데이터베이스에 Integration 권한 부여

---

## ⚙️ 설정 방법

### 1. 설정 파일 생성
```bash
cp config/settings.example.yaml config/settings.yaml
```

### 2. `config/settings.yaml` 편집

```yaml
dynalist:
  api_key: "your_dynalist_api_key_here"
  document_ids:
    - id: "메인_문서_ID"
      name: "메인 문서"
      type: "tagged"          # 태그로 분류
    - id: "개념_문서_ID"
      name: "개념 문서"
      type: "concept"         # 모두 개념 DB로

notion:
  api_key: "your_notion_api_key_here"
  databases:
    - name: "개념_단어_용어"
      purpose: "concept"
      database_id: "33e3d5953cda80f0afa1e5580b2fbe61"
    - name: "업무관련"
      purpose: "work"
      database_id: "3413d5953cda8061a4c3e0cd30386208"
      tag_filter: "#업무관련"
    - name: "개인용무"
      purpose: "personal"
      database_id: "3413d5953cda805286fedf8c5e50d1d1"
      tag_filter: "#개인용무"

logging:
  log_file: "logs/sync.log"

schedule:
  time: "00:00"  # 매일 자정 실행
```

### 3. Notion 데이터베이스 설정

각 Notion 데이터베이스에 다음 필드를 생성하세요:

| 필드명 | 타입 | 필수 | 설명 |
|--------|-----|------|------|
| 제목 | Title | ✅ | Dynalist 항목 제목 |
| 날짜 | Date | ✅ | 생성 날짜 |
| 대분류 | Select | ✅ | 첫 번째 태그 |
| 중분류 | Select | ✅ | 두 번째 태그 |
| 소분류 | Multi-select | ✅ | 3번째 이후 태그들 |

**필드명 변형 인식:**
- 대분류: "대분류", "영역", "Domain"
- 중분류: "중분류", "카테고리", "Category"
- 소분류: "소분류", "태그", "Tags"
- 날짜: "날짜", "Date"

---

## 🚀 실행 방법

### 1. 오늘의 기록 동기화
```bash
python3 src/main.py --once
```

### 2. 특정 날짜 동기화
```bash
python3 src/main.py --once --date 2026-04-13
```

### 3. 지난 N일 동기화 (권장: 초기 설정 시)
```bash
# 지난 7일 동기화
python3 src/main.py --once --last-days 7

# 지난 30일 동기화
python3 src/main.py --once --last-days 30
```

### 4. 날짜 범위 동기화
```bash
# 2026-04-06 ~ 2026-04-13 동기화
python3 src/main.py --once --date-range 2026-04-06:2026-04-13
```

### 5. 스케줄러 실행 (백그라운드)
```bash
# 매일 자정에 자동 실행 (설정의 schedule.time 참고)
python3 src/main.py
```

### 6. Docker로 실행
```bash
docker build -t dynolink .
docker run -v $(pwd)/config:/app/config -v $(pwd)/logs:/app/logs dynolink
```

---

## 📊 동기화 흐름도

```
┌───────────────────────────────────────────┐
│  Dynalist 2개 문서 읽기                    │
├───────────────────────────────────────────┤
│ ├─ 메인 문서 (tagged)                     │
│ │  → #업무관련 태그 있음? → 업무DB        │
│ │  → #개인용무 태그 있음? → 개인DB        │
│ │  → 기타 또는 없음? → 개념DB (기본값)    │
│ │                                         │
│ └─ 개념 문서 (concept)                    │
│    → 모두 개념DB로 (태그 무시)             │
└───────────────────────────────────────────┘
              ↓
┌───────────────────────────────────────────┐
│  Transformer (변환)                        │
├───────────────────────────────────────────┤
│ ├─ 제목 추출 (태그 제거)                   │
│ ├─ 날짜 추출                              │
│ ├─ 태그 계층화:                           │
│ │  #대분류 > #중분류 > #소분류 > #소분류+  │
│ └─ 메모 준비 (2000자 제한 처리)           │
└───────────────────────────────────────────┘
              ↓
┌───────────────────────────────────────────┐
│  Notion 3개 데이터베이스 동시 저장 ✅     │
├───────────────────────────────────────────┤
│ ├─ 개념_단어_용어 DB                      │
│ ├─ 업무관련 DB                           │
│ └─ 개인용무 DB                           │
└───────────────────────────────────────────┘
```

---

## 📝 Dynalist 작성 예시

### 예제 1: 태그 있는 업무 항목
```
📌 프로젝트 회의
  #업무관련 #회사프로젝트 #아이디어 #토론
  
  メモ:
  - 프로젝트 방향 설정
  - 팀 역할 분담
  - 다음 회의 일정: 4월 20일
```

**동기화 결과:**
- 데이터베이스: 업무관련
- 제목: 프로젝트 회의
- 대분류: #업무관련
- 중분류: #회사프로젝트
- 소분류: [#아이디어, #토론]

---

### 예제 2: 계층이 깊은 개념
```
📌 REST API의 정의
  #개념 #웹개발 #아키텍처 #HTTP > #상태코드 > #성공
  
  메모:
  Representational State Transfer의 약자로...
```

**동기화 결과:**
- 데이터베이스: 개념_단어_용어
- 제목: REST API의 정의
- 대분류: #개념
- 중분류: #웹개발
- 소분류: [#아키텍처, #HTTP, #상태코드, #성공]

---

## 📂 프로젝트 구조

```
DynoLink/
├── README.md                          # 이 파일
├── Dockerfile                         # Docker 설정
├── requirements.txt                   # Python 패키지
├── config/
│   ├── settings.example.yaml         # 설정 템플릿
│   └── settings.yaml                 # 실제 설정 (유저가 수정)
├── src/
│   ├── main.py                       # 메인 실행 파일
│   ├── dynalist_client.py            # Dynalist API 클라이언트
│   ├── notion_sync_client.py         # Notion API 클라이언트
│   └── transformer.py                # 데이터 변환 로직
├── logs/
│   └── sync.log                      # 동기화 로그
└── test_notion_sync.py               # 테스트 (선택사항)
```

---

## 🔍 로그 확인

### 실시간 로그 모니터링
```bash
tail -f logs/sync.log
```

### 최근 100줄 확인
```bash
tail -100 logs/sync.log
```

### 전체 로그 확인
```bash
cat logs/sync.log
```

### 특정 날짜의 로그 필터링
```bash
grep "2026-04-13" logs/sync.log
```

---

## 🐛 문제 해결

### 1. "API Error: Unauthorized" 에러
**원인:** Dynalist API 키가 잘못됨
```bash
# 해결: config/settings.yaml에서 API 키 재확인
# Dynalist 설정에서 새 토큰 생성
```

### 2. "Database configuration not found" 에러
**원인:** settings.yaml의 `notion.databases` 구조 오류
```bash
# 해결: settings.example.yaml 참고하여 형식 확인
```

### 3. "Failed to fetch documents" 에러
**원인:** 네트워크 문제 또는 Dynalist API 서버 장애
```bash
# 해결: 잠시 후 재시도
```

### 4. Notion 필드를 인식하지 못함
**원인:** 필드명이 정확하지 않음
```bash
# 해결: 필드명을 다음 중 하나로 정확히 설정:
# - 대분류/영역/Domain (Select)
# - 중분류/카테고리/Category (Select)
# - 소분류/태그/Tags (Multi-select)
# - 날짜/Date (Date)
```

---

## 📊 성능 및 제한사항

| 항목 | 값 |
|-----|-----|
| **Dynalist 문서 개수** | 2개 지원 |
| **Notion 데이터베이스** | 3개 (확장 가능) |
| **메모 최대 길이** | 제한 없음 (2000자마다 자동 분할) |
| **API 호출 제한** | Dynalist: 60 req/min, Notion: 3 req/sec |
| **동기화 시간** | 약 100개 항목 = 1-2초 |

---

## �️ 추후 개발 계획 (TODO)

### Phase 1: 고급 날짜 처리
- [ ] **자동 날짜 감지** - Dynalist 메모에서 날짜 텍스트 파싱
  - 예: "회의 2026-04-15" → 자동으로 2026-04-15로 설정
  - 지원 형식: "2026-04-15", "4월 15일", "다음 주 월요일" 등
  - 현재: 항목 생성날짜만 사용 → **개선**: 메모의 날짜 정보 우선 사용

### Phase 2: Dynalist 계층 구조 개선
- [ ] **태그 기반 자동 분류 (v2.0)**
  - 현재: 평면 태그 구조 (#대분류 > #중분류 > #소분류)
  - **개선**: 첫 태그는 분류 기준 (#개인용무, #업무관련)
  - 그 아래 child 노드의 태그를 계층별로 매핑
  - 예시:
    ```
    📌 연간 계획
      #개인용무 (분류 기준)
      └─ 자기계발 (중분류)
         └─ 독서 (소분류)
         └─ 코딩 (소분류)
    ```
- [ ] **무한 계층 지원** - 4단계 이상의 태그도 스마트하게 처리
  - 현재: 소분류에 모두 누적
  - **개선**: 계층 깊이 자동 감지 및 최적 분배

### Phase 3: Notion 고급 기능
- [ ] **자동 데이터베이스 생성** - API로 Notion DB 자동 생성
  - 현재: 수동으로 DB 생성 필요
  - **개선**: 첫 실행 시 자동 설정
- [ ] **관계(Relations) 필드 지원** - 데이터베이스 간 연결
  - 예: "업무관련" DB의 항목이 "개념" 항목 참조
- [ ] **템플릿 페이지 지원** - 아카이브 자동화
- [ ] **Emoji 지원** - Dynalist emoji를 Notion에 유지

### Phase 4: UI/UX 개선
- [ ] **웹 대시보드** - 동기화 상태 시각화
  - 실시간 로그 뷰
  - 동기화 통계 (일일/주간/월간)
  - 에러 알림
- [ ] **CLI의 대화형 설정** - `--init` 플래그로 대화식 설정
- [ ] **Slack/Discord 알림** - 동기화 완료/실패 시 알림

### Phase 5: 성능 및 안정성
- [ ] **배치 처리 최적화** - Notion API 호출 최소화
  - 현재: 항목당 1 API 호출
  - **개선**: 배치 업데이트로 처리량 증가
- [ ] **재시도 로직** - 실패 항목 자동 재시도
- [ ] **데이터 백업** - 동기화 전 로컬 백업
- [ ] **동기화 상태 추적** - 중복 저장 방지

### Phase 6: 보안 및 운영
- [ ] **환경변수 지원** - API 키를 .env 파일로 관리
- [ ] **로컬 암호화** - 설정 파일 암호화 저장
- [ ] **로그 로테이션** - 자동 로그 파일 정리
- [ ] **모니터링** - 에러율 추적 및 알림

### Phase 7: 통합 확장
- [ ] **Obsidian 연동** - Obsidian vault로 로컬 백업
- [ ] **Google Calendar 연동** - 날짜 기반 캘린더 이벤트 생성
- [ ] **Roam Research 지원** - 추가 백업 옵션
- [ ] **CLI as a Service** - API 서버 모드 지원

---

## 🎯 알려진 제한사항 및 개선 예정

| 항목 | 현재 | 계획 |
|-----|------|------|
| **날짜 소스** | 생성 시간만 | ✅ 메모의 날짜 텍스트 파싱 |
| **태그 분류** | 평면 구조 | ✅ Dynalist 계층 반영 |
| **DB 생성** | 수동 | ✅ API 자동 생성 |
| **다중 DB 개수** | 3개 하드코딩 | ✅ 무제한으로 확장 가능 |
| **실행 모드** | CLI만 | ✅ 웹 UI + CLI + API 서버 |
| **에러 처리** | 기본 | ✅ 재시도 + 상세 로깅 |

---

## 💡 기여 아이디어 환영합니다!

이 TODO 리스트에 없는 기능을 제안하고 싶으신가요?
[Issues](../../issues)에서 feature request를 작성해주세요!

---

## �🔐 보안 주의사항

⚠️ **API 키 보안:**
- `config/settings.yaml`은 절대 git에 커밋하지 마세요
- `.gitignore`에 이미 포함되어 있습니다
- 환경변수로 관리하는 것이 더 안전합니다 (추후 지원 예정)

⚠️ **Notion Integration 권한:**
- 필요한 데이터베이스에만 권한 부여
- 정기적으로 토큰 순환 계획 수립

---

## 📞 기여 및 지원

버그 리포트나 기능 요청은 [Issues](../../issues)에서 해주세요.

---

## 📄 라이선스

MIT License

---

## 🎓 참고 자료

- [Dynalist API 문서](https://dynalist.io/developer)
- [Notion API 문서](https://developers.notion.com/reference)
- [Python Notion Client](https://github.com/ramnes/notion-sdk-py)

---

**마지막 업데이트:** 2026년 4월 13일
