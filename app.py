"""
📰 나만의 AI 데스킹 룸
──────────────────────────────────────────────────────────────────
기사 URL을 크롤링하고, 사용자의 분석글을 Claude AI에게 전송하여
20년 차 수석 논설위원의 매서운 피드백을 받아오는 Streamlit 앱.
"""

import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
import anthropic

# ── 페이지 기본 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="나만의 AI 데스킹 룸",
    page_icon="📰",
    layout="centered",
)

# ── 시스템 프롬프트 (논설위원 역할 강제) ──────────────────────────
SYSTEM_PROMPT = """당신은 20년 차 주요 일간지의 수석 논설위원이자 사회학에 정통한 데스크입니다. \
내가 제공하는 [기사 원문]과 [나의 분석]을 읽고 다음 3가지를 엄격하게 피드백하세요.

1. 논리의 비약: 내 주장이 기사에 없는 팩트를 과장하거나 성급하게 일반화하지 않았는지 매섭게 지적하세요.
2. 사회학적 데스킹: 피에르 부르디외, 미셸 푸코, 위르겐 하버마스, 지그문트 바우만, 앤서니 기든스 등의 \
현대 사회학 이론 중 가장 적절한 것을 하나 이상 적용하여, 내 글에 빠진 현상 이면의 '구조적 맥락'을 \
짚어내고 시각을 확장해 주세요.
3. 저널리즘 문장력: 수식어를 덜어내고 단문으로 쪼개어 건조하고 힘 있는 문장으로 교정해 주세요.

답변 양식은 반드시 [데스크의 총평], [논리적 허점], [사회학적 시각 확장], [문장 교정] \
4가지 단락으로 나누어 출력하세요."""


# ── 유틸: 기사 크롤링 ─────────────────────────────────────────────
def crawl_article(url: str) -> str:
    """
    주어진 URL에서 <p> 태그 텍스트를 추출하여 기사 본문으로 반환합니다.
    차단 방지를 위해 브라우저 User-Agent 헤더를 사용합니다.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    # HTTP GET 요청 (타임아웃 10초)
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # 4xx/5xx 상태코드면 예외 발생

    # BeautifulSoup으로 <p> 태그 텍스트 추출
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

    if not paragraphs:
        raise ValueError("해당 페이지에서 본문 텍스트(<p> 태그)를 추출하지 못했습니다.")

    return "\n".join(paragraphs)


# ── 유틸: Claude API 호출 ─────────────────────────────────────────
def get_desk_feedback(article_body: str, user_analysis: str) -> str:
    """
    크롤링한 기사 본문과 사용자 분석을 Claude에 전송하고
    논설위원 피드백 텍스트를 반환합니다.
    """
    # API 키: Streamlit secrets → 환경변수 순으로 참조
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Anthropic API 키를 찾을 수 없습니다. "
            ".streamlit/secrets.toml 또는 환경변수 ANTHROPIC_API_KEY를 설정해 주세요."
        )

    client = anthropic.Anthropic(api_key=api_key)

    # user 메시지: 기사 원문 + 사용자 분석을 하나의 블록으로 구성
    user_message = (
        f"[기사 원문]\n{article_body}\n\n"
        f"[나의 분석]\n{user_analysis}"
    )

    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    # 응답에서 텍스트 블록만 추출
    return message.content[0].text


# ── UI 렌더링 ─────────────────────────────────────────────────────
st.title("📰 나만의 AI 데스킹 룸")
st.caption("기사 URL과 나의 분석을 송고하면, AI 수석 논설위원이 매섭게 교열합니다.")

st.divider()

# 입력 1: 기사 URL
article_url = st.text_input(
    "🔗 기사 URL",
    placeholder="https://www.example.com/news/article-title",
    help="크롤링할 뉴스 기사의 전체 URL을 붙여넣으세요.",
)

# 입력 2: 나의 단상 및 분석
user_analysis = st.text_area(
    "✍️ 내 단상 및 분석",
    placeholder="이 기사를 읽고 느낀 점, 사회적 함의, 나만의 해석을 자유롭게 작성하세요...",
    height=220,
    help="최소 2~3문장 이상 작성할수록 풍부한 피드백을 받을 수 있습니다.",
)

st.divider()

# 송고 버튼
if st.button("🗞️ 데스크에 송고하기", use_container_width=True, type="primary"):

    # ── 입력값 유효성 검사 ──────────────────────────────────────
    if not article_url.strip():
        st.error("❌ 기사 URL을 입력해 주세요.")
        st.stop()

    if not user_analysis.strip():
        st.error("❌ 내 단상 및 분석을 입력해 주세요.")
        st.stop()

    # ── 크롤링 + AI 호출 (순차 실행) ───────────────────────────
    with st.spinner("📡 기사를 크롤링하는 중..."):
        try:
            article_body = crawl_article(article_url.strip())
        except requests.exceptions.MissingSchema:
            st.error("❌ URL 형식이 올바르지 않습니다. 'https://'로 시작하는 전체 주소를 입력해 주세요.")
            st.stop()
        except requests.exceptions.ConnectionError:
            st.error("❌ 해당 URL에 접속할 수 없습니다. 네트워크 연결 또는 URL을 확인해 주세요.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ HTTP 오류가 발생했습니다: {e}")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("❌ 요청 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
            st.stop()
        except ValueError as e:
            st.error(f"❌ 본문 추출 실패: {e}")
            st.stop()
        except Exception as e:
            st.error(f"❌ 크롤링 중 예기치 않은 오류가 발생했습니다: {e}")
            st.stop()

    # 크롤링 성공 알림 (미리보기)
    with st.expander("📄 크롤링된 기사 본문 미리보기 (클릭하여 열기)", expanded=False):
        preview = article_body[:1000] + ("..." if len(article_body) > 1000 else "")
        st.text(preview)
        st.caption(f"총 {len(article_body)}자 추출됨")

    with st.spinner("🤖 AI 논설위원이 검토 중입니다... 잠시만 기다려 주세요."):
        try:
            feedback = get_desk_feedback(article_body, user_analysis.strip())
        except EnvironmentError as e:
            st.error(f"🔑 API 키 오류: {e}")
            st.stop()
        except anthropic.AuthenticationError:
            st.error("❌ Anthropic API 키가 유효하지 않습니다. 키를 확인해 주세요.")
            st.stop()
        except anthropic.RateLimitError:
            st.error("❌ API 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.")
            st.stop()
        except Exception as e:
            st.error(f"❌ AI 호출 중 오류가 발생했습니다: {e}")
            st.stop()

    # ── 결과 출력 ───────────────────────────────────────────────
    st.success("✅ 데스크 피드백이 도착했습니다!")
    st.divider()
    st.subheader("🖊️ 논설위원 데스크의 피드백")
    st.markdown(feedback)
