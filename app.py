import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 제미나이 API 키 설정
genai.configure(api_key=st.secrets["AIzaSyACRyarhB_C3U4sz4aBC8O3V7UM-0I1JWw"])
model = genai.GenerativeModel('gemini-2.5-flash')

st.title("📰 나만의 AI 데스킹 룸")

url_input = st.text_input("기사 URL을 입력하세요")
user_analysis = st.text_area("내 단상 및 분석을 입력하세요")

if st.button("데스크에 송고하기"):
    if not url_input or not user_analysis:
        st.error("URL과 분석을 모두 입력해주세요.")
    else:
        with st.spinner("데스크가 기사를 읽고 있습니다..."):
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url_input, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                paragraphs = soup.find_all('p')
                article_text = ' '.join([p.text for p in paragraphs])
                
                prompt = f"""
                당신은 20년 차 주요 일간지의 수석 논설위원이자 사회학에 정통한 데스크입니다. 다음 [기사 원문]과 [나의 분석]을 읽고 엄격하게 피드백하세요.
                
                1. 논리의 비약: 내 주장이 기사에 없는 팩트를 과장하거나 성급하게 일반화하지 않았는지 매섭게 지적하세요.
                2. 사회학적 데스킹: 피에르 부르디외, 미셸 푸코, 위르겐 하버마스, 지그문트 바우만, 앤서니 기든스 등의 현대 사회학 이론 중 가장 적절한 것을 하나 이상 적용하여, 현상 이면의 구조적 맥락을 짚어내고 시각을 확장해 주세요.
                3. 저널리즘 문장력: 수식어를 덜어내고 단문으로 쪼개어 건조하고 힘 있는 문장으로 교정해 주세요.
                
                답변 양식은 [데스크의 총평], [논리적 허점], [사회학적 시각 확장], [문장 교정] 4가지 단락으로 출력하세요.
                
                [기사 원문]
                {article_text}
                
                [나의 분석]
                {user_analysis}
                """
                
                response = model.generate_content(prompt)
                st.success("데스킹 완료!")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"크롤링 또는 분석 중 오류가 발생했습니다: {e}")
