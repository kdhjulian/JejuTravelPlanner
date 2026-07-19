# 코드 검수 리포트 — 제주 여행 플래너

## 전체 평가

잘 설계된 프로젝트입니다. LangGraph + Flet 조합으로 관심사 분리가 명확하고,
가드레일 → 분석 → 생성/수정 → 응답의 파이프라인 구조가 읽기 쉽습니다.

---

## 장점

- **관심사 분리**: UI(Flet), 비즈니스 로직(LangGraph 노드), 상태(TypedDict), 설정(app_config)이 깔끔하게 분리됨
- **Fail-safe 설계**: LLM 호출 실패 시 fallback, API 키 없을 때 방어, 가드레일 실패 시 안전 차단(fail-closed)
- **2단계 수정 전략**: 카드 단위 patch → Day 전체 교체 순으로 시도하여 세밀한 수정과 대규모 변경을 모두 지원
- **원자적 검증**: patch operations를 all-or-nothing으로 검증하여 부분 적용으로 인한 비정상 상태 방지
- **열린 분류 체계**: 여행 조건의 category를 고정 enum이 아닌 자유 문자열로 설계하여 LLM이 유연하게 분류 가능
- **테마 계층**: Base → Derived → Semantic 3단계 색상 체계로 일관성 유지

---

## 개선 제안

### 우선도 높음

1. **비동기 LLM 호출**
   - `handle_send_message`에서 `run_travel_agent()`가 동기 실행되어 UI가 멈춤
   - `asyncio` 또는 Flet의 `threading` 지원을 활용해 비동기 처리 권장
   - 로딩 인디케이터(스피너) 표시도 함께 고려

2. **ui_state 타입 안전성**
   - 현재 `dict`로 관리 → `dataclass` 또는 `TypedDict`로 변경하면 필드명 오타를 정적 분석으로 검출 가능

3. **LLM 예외 처리 개선**
   - `except Exception`으로 광범위하게 잡는 곳이 여러 군데 있음
   - 최소한 로깅(`logging` 모듈)을 추가하여 실패 원인을 추적 가능하게 할 것

### 우선도 중간

4. **Day 검색 함수 중복**
   - `find_selected_itinerary_day` (itinerary_panel.py)
   - `find_selected_map_day` (map_panel.py)
   - `find_itinerary_day` (dashboard_view.py)
   - `find_itinerary_day_by_number` (nodes.py)
   - 모두 동일 로직 → 공통 유틸리티 모듈로 추출 권장

5. **Pydantic 모델 외부 정의**
   - 함수 내부에서 `class ... (BaseModel):`을 정의하는 패턴이 반복됨
   - 별도 `schemas.py`에 정의하면 재사용성·가독성 향상

6. **환경 변수 로딩 중복**
   - `nodes.py`와 `input_guardrails.py` 양쪽에서 `load_dotenv()` 호출
   - 프로젝트 진입점(main.py)에서 한 번만 로딩하는 것이 일반적

### 우선도 낮음

7. **`destination_name` 매개변수 사실상 미사용**
   - `run_travel_agent()`가 `destination_name` 인자를 받지만 항상 `SUPPORTED_DESTINATION_NAME`으로 덮어씀
   - 향후 여행지 확장 전까지는 매개변수를 제거하거나 주석으로 의도를 명시

8. **시간 파싱 엣지 케이스**
   - `parse_schedule_time_to_minutes`에서 "오전 12:30" → 30분으로 변환됨 (정확)
   - 하지만 "24:00", "25시" 같은 비표준 입력은 None 반환 → 사용자 안내가 있으면 좋음

9. **테스트 부재**
   - 특히 `validate_item_patch_operation`, `parse_schedule_time_to_minutes`,
     `extract_numeric_trip_day_count` 등 순수 함수는 단위 테스트 작성 용이

---

## 파일별 주석 추가 내역

| 파일 | 주석 유형 |
|------|----------|
| `main.py` | 모듈 docstring, 함수 docstring, 인라인 주석 |
| `app_config.py` | 모듈 docstring, 각 상수 설명 |
| `Graph/travel_state.py` | 모듈 docstring, 구조 개요, 각 TypedDict 필드별 설명 |
| `Graph/input_guardrails.py` | 모듈 docstring, 판단 흐름 설명, 함수 docstring, 인라인 주석 |
| `Graph/travel_graph.py` | 모듈 docstring, Mermaid 그래프 구조, 함수 docstring |
| `Graph/nodes.py` | 모듈 docstring, 13개 섹션 구분, 전체 함수 docstring, 인라인 주석 |
| `UI/theme.py` | 모듈 docstring, 색상 계층 설명, 각 색상 변수 역할 설명 |
| `UI/agent_panel.py` | 모듈 docstring, 컴포넌트 구조 ASCII 다이어그램 |
| `UI/itinerary_panel.py` | 모듈 docstring, 컴포넌트 구조, 함수 docstring |
| `UI/map_panel.py` | 모듈 docstring, 향후 개선 사항, 검수 의견 |
| `UI/dashboard_view.py` | 모듈 docstring, 레이아웃 구조, 클로저 패턴 설명, 검수 의견 |
