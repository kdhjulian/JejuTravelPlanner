"""
Graph/input_guardrails.py — 입력 가드레일(Input Guardrail) 노드

LangGraph 파이프라인의 첫 번째 노드로서, 사용자 입력이
앱이 지원하는 범위(현재: 제주 여행) 안에 있는지 LLM으로 판단합니다.

판단 흐름:
    1. OPENAI_API_KEY 존재 여부 확인 → 없으면 안전하게 차단
    2. LLM(Structured Output)으로 여행지 스코프 판단
    3. allow → 다음 노드(analyze_user_request)로 진행
       block → create_guardrail_response 노드로 분기하여 차단 메시지 생성

주의:
    - LLM 호출 자체가 실패하면 "안전한 쪽"으로 차단합니다(fail-closed 전략).
    - 이 파일은 LangGraph 노드 함수이므로 TravelAgentState를 입력받고
      부분 상태 딕셔너리를 반환합니다.
"""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from app_config import JEJU_SCOPE_BLOCK_MESSAGE, SUPPORTED_DESTINATION_NAME
from Graph.travel_state import TravelAgentState


# ──────────────────────────────────────────────────────────────
# 환경 변수 로딩
# ──────────────────────────────────────────────────────────────
# 프로젝트 루트의 .env 파일에서 OPENAI_API_KEY 등을 읽어옵니다.
# Path(__file__).resolve().parents[1] → Graph/ 폴더의 상위, 즉 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE_PATH)


# ──────────────────────────────────────────────────────────────
# 가드레일 노드 함수
# ──────────────────────────────────────────────────────────────
def guard_jeju_scope(state: TravelAgentState) -> dict[str, object]:
    """사용자 입력이 제주 여행 범위 안에 있는지 검사합니다.

    판단 원칙:
        - 제주 여행 요청이면 통과(allow)합니다.
        - 여행지가 명확하지 않은 일반 조건 입력도 통과합니다.
          예: "부모님이 오래 못 걸으셔서 동선 짧게"
        - 제주가 아닌 여행지를 명시하면 차단(block)합니다.
          예: "부산 2박 3일", "강릉 여행 짜줘"
        - "서울에서 출발해서 제주 가는 일정"처럼 출발지가 다른 도시인 경우는 통과합니다.

    Args:
        state: LangGraph 상태. user_message 필드를 읽어 판단합니다.

    Returns:
        dict — guardrail_blocked, guardrail_message, guardrail_reason,
               detected_destination 필드를 포함하는 부분 상태 업데이트.
    """

    # ── 사전 조건 검사: API 키 유무 ─────────────────────────
    # API 키가 없으면 LLM 판단 자체가 불가능하므로 안전하게 차단합니다.
    if not os.getenv("OPENAI_API_KEY"):
        return create_guardrail_failure_result(
            "OPENAI_API_KEY가 설정되지 않았습니다."
        )

    # ── 런타임 의존성 확인 ───────────────────────────────────
    # langchain_openai, pydantic은 무거운 패키지이므로
    # 함수 내에서 지연 임포트(lazy import)합니다.
    # 설치되지 않은 환경에서도 앱이 완전히 죽지 않도록 방어합니다.
    try:
        from langchain_openai import ChatOpenAI
        from pydantic import BaseModel, Field
    except ImportError:
        return create_guardrail_failure_result(
            "langchain_openai 또는 pydantic import에 실패했습니다."
        )

    # ── LLM Structured Output 스키마 정의 ────────────────────
    # Pydantic 모델로 LLM 응답 구조를 강제합니다.
    # with_structured_output()이 이 스키마를 JSON Schema로 변환하여
    # function calling 형태로 LLM에 전달합니다.
    class DestinationScopeDecision(BaseModel):
        decision: Literal["allow", "block"] = Field(
            description=(
                "allow if the request is about Jeju travel, has no clear destination, "
                "or mentions another city only as departure/transit. "
                "block if the user is asking to plan a non-Jeju destination."
            )
        )
        detected_destination: str | None = Field(
            default=None,
            description="The main destination the user wants to travel to, if any.",
        )
        reason: str = Field(
            description="Short Korean explanation.",
        )

    # ── 시스템 프롬프트 ──────────────────────────────────────
    # f-string으로 SUPPORTED_DESTINATION_NAME을 주입하여,
    # 향후 지원 여행지가 바뀌어도 프롬프트가 자동으로 반영됩니다.
    system_prompt = f"""
너는 여행 플래너 앱의 입력 가드레일이다.

현재 앱은 {SUPPORTED_DESTINATION_NAME} 여행만 지원한다.

판단 규칙:
1. 사용자가 {SUPPORTED_DESTINATION_NAME} 여행을 요청하면 allow.
2. 사용자가 여행지를 명확히 말하지 않고 조건만 말하면 allow.
   예: "부모님이 오래 못 걸으셔서 동선 짧게", "렌터카로 이동할게"
3. 사용자가 다른 도시/지역 여행을 요청하면 block.
   예: "부산 2박 3일", "강릉 여행 짜줘", "서울 맛집 일정"
4. 다른 도시가 출발지/경유지로 나온 경우는 block하지 않는다.
   예: "서울에서 출발해서 제주 가는 일정"은 allow.
5. 애매하면 allow하되 reason에 불확실성을 적어라.
"""

    # ── LLM 호출 ─────────────────────────────────────────────
    # TRAVEL_AGENT_MODEL 환경변수로 모델을 교체할 수 있습니다.
    # 기본값은 비용 효율이 좋은 gpt-4o-mini입니다.
    chat_model = ChatOpenAI(
        model=os.getenv("TRAVEL_AGENT_MODEL", "gpt-4o-mini"),
        temperature=0,  # 가드레일은 결정적(deterministic) 판단이므로 temperature=0
    )

    # with_structured_output()으로 Pydantic 모델 기반 응답을 강제합니다.
    structured_model = chat_model.with_structured_output(
        DestinationScopeDecision
    )

    try:
        decision = structured_model.invoke(
            [
                ("system", system_prompt),
                ("human", state["user_message"]),
            ]
        )
    except Exception as error:
        # LLM 호출 실패 시 fail-closed: 안전하게 차단합니다.
        return create_guardrail_failure_result(
            f"Guardrail 모델 호출에 실패했습니다: {error}"
        )

    # ── 결과 분기 ────────────────────────────────────────────
    if decision.decision == "block":
        return {
            "guardrail_blocked": True,
            "guardrail_message": JEJU_SCOPE_BLOCK_MESSAGE,
            "guardrail_reason": decision.reason,
            "detected_destination": decision.detected_destination,
        }

    # allow인 경우 — 다음 노드로 진행
    return {
        "guardrail_blocked": False,
        "guardrail_reason": decision.reason,
        "detected_destination": decision.detected_destination,
    }


# ──────────────────────────────────────────────────────────────
# 가드레일 실패 시 안전 응답 생성
# ──────────────────────────────────────────────────────────────
def create_guardrail_failure_result(reason: str) -> dict[str, object]:
    """Guardrail 판단 자체가 실패했을 때 안전하게 차단합니다.

    실패 원인(API 키 없음, Import 실패, LLM 호출 예외 등)에 관계없이
    일관된 차단 응답을 반환하여 앱이 예측 가능하게 동작하도록 합니다.

    Args:
        reason: 내부 로그용 실패 사유 문자열.

    Returns:
        dict — guardrail_blocked=True인 부분 상태 업데이트.
    """

    return {
        "guardrail_blocked": True,
        "guardrail_message": (
            "현재 제주 여행 여부를 확인하지 못했습니다. "
            "제주 여행 조건을 명확히 포함해서 다시 입력해 주세요."
        ),
        "guardrail_reason": reason,
        "detected_destination": None,
    }
