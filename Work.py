import streamlit as st
import pandas as pd
import holidays
import json
import os
from datetime import datetime, date, timedelta

# 1. 페이지 설정 및 디자인 (CSS)
st.set_page_config(page_title="근무 일정 관리 시스템", layout="wide")

st.markdown("""
    <style>
    /* 필터링 시 강조 효과 */
    .highlight-card {
        border: 3px solid #4dabf7 !important;
        box-shadow: 0px 0px 15px rgba(77, 171, 247, 0.4) !important;
    }
    .dimmed-card {
        opacity: 0.4;
    }
    /* 기존 스타일 유지 */
    [data-testid="column"] {
        height: 250px !important; 
        border: 1px solid #dee2e6;
        padding: 10px !important;
        background-color: #ffffff;
        border-radius: 8px;
    }
    .today-box { background-color: #fff9db !important; border: 2px solid #fcc419 !important; }
    .mobile-card { border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 10px; background-color: white; }
    .worker-tag { display: block; padding: 6px 10px; border-radius: 6px; font-size: 14px; font-weight: bold; margin-top: 5px; color: black; text-align: center; border: 1px solid rgba(0,0,0,0.1); }
    .date-header { font-size: 1.2rem; font-weight: bold; border-bottom: 2px solid #f1f3f5; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 관리 함수 (기존과 동일)
DATA_FILE = "schedule_db.json"
LOG_FILE = "action_log.json"
def load_json(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else ({} if "db" in file_path else [])
    except: pass
    return {} if "db" in file_path else []

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 3. 상태 및 기본 설정
if 'db' not in st.session_state: st.session_state['db'] = load_json(DATA_FILE)
WORKER_COLORS = {"박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"}
kr_holidays = holidays.KR(language='ko')
today_val = date.today()

# 4. 사이드바 제어
st.sidebar.title("🛠️ 설정 및 관리")
password = st.sidebar.text_input("관리자 비밀번호", type="password")
is_admin = (password == "1234") 

view_mode = st.sidebar.radio("화면 모드", ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"], index=1)
selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=today_val.month - 1)

# 5. 통계 및 필터링 (우측 탭이었으나 로직상 위로 올림)
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 근무자 필터링")
filter_name = st.sidebar.selectbox("강조할 사람 선택", ["전체보기"] + list(WORKER_COLORS.keys()))

# 6. 날짜 계산
current_year = 2026
first_day = date(current_year, selected_month, 1)
start_pad = (first_day.weekday() + 1) % 7 
last_day = (date(current_year, selected_month + 1, 1) if selected_month < 12 else date(current_year + 1, 1, 1)) - timedelta(days=1)

# 7. 메인 화면
col_cal, col_stat = st.columns([4, 1])

with col_cal:
    st.title(f"{selected_month}월 근무현황")

    if view_mode == "📱 리스트 보기 (모바일)":
        for d in range(1, last_day.day + 1):
            this_date = date(current_year, selected_month, d)
            d_str = this_date.strftime('%Y-%m-%d')
            assigned = st.session_state['db'].get(d_str, [])
            
            # 필터링 로직: 선택된 사람이 포함되어 있나?
            is_match = (filter_name == "전체보기") or (filter_name in assigned)
            card_class = "highlight-card" if (filter_name != "전체보기" and is_match) else ""
            if filter_name != "전체보기" and not is_match: card_class = "dimmed-card"
            
            is_today = (this_date == today_val)
            is_off = (this_date in kr_holidays) or (this_date.weekday() in [0, 6])
            
            st.markdown(f"""
                <div class='mobile-card {card_class}' style='{"border: 2px solid #fcc419;" if is_today else ""}'>
                    <div style='color:{"red" if is_off else "black"}; font-weight:bold;'>
                        {d}일 {kr_holidays.get(this_date, "")} {"(오늘)" if is_today else ""}
                    </div>
                """, unsafe_allow_html=True)
            
            if not is_off:
                if is_admin:
                    selected = st.multiselect(f"e_{d}", list(WORKER_COLORS.keys()), default=assigned, key=f"m_{d_str}", label_visibility="collapsed")
                    if selected != assigned:
                        st.session_state['db'][d_str] = selected
                        save_json(DATA_FILE, st.session_state['db']); st.rerun()
                else:
                    for name in assigned:
                        # 필터링된 사람만 더 진하게 표시
                        opacity = "1.0" if (filter_name == "전체보기" or name == filter_name) else "0.3"
                        st.markdown(f"<span class='worker-tag' style='background-color:{WORKER_COLORS.get(name)}; opacity:{opacity};'>{name}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    else: # PC 달력
        header_cols = st.columns(7)
        for i, day in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
            header_cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)
        
        day_counter = 1
        for w in range(((start_pad + last_day.day) + 6) // 7):
            cols = st.columns(7)
            for d in range(7):
                idx = w * 7 + d
                with cols[d]:
                    if idx < start_pad or day_counter > last_day.day: st.empty()
                    else:
                        this_date = date(current_year, selected_month, day_counter)
                        d_str = this_date.strftime('%Y-%m-%d')
                        assigned = st.session_state['db'].get(d_str, [])
                        is_match = (filter_name == "전체보기") or (filter_name in assigned)
                        
                        # 강조/흐리게 스타일 적용
                        div_style = ""
                        if filter_name != "전체보기":
                            div_style = "border: 3px solid #4dabf7;" if is_match else "opacity: 0.3;"

                        st.markdown(f"<div style='{div_style} padding:5px; border-radius:5px;'>", unsafe_allow_html=True)
                        st.markdown(f"<b>{day_counter}</b>", unsafe_allow_html=True)
                        for name in assigned:
                            st.markdown(f"<span class='worker-tag' style='background-color:{WORKER_COLORS.get(name)};'>{name}</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        day_counter += 1

with col_stat:
    st.subheader("📊 통계")
    prefix = f"{current_year}-{selected_month:02d}"
    all_data = [n for k, names in st.session_state['db'].items() if k.startswith(prefix) for n in names]
    
    for name, color in WORKER_COLORS.items():
        if filter_name != "전체보기" and name != filter_name: continue # 필터링 시 해당 인원만 노출
        count = all_data.count(name)
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:5px; margin-bottom:5px; font-weight:bold; color:black;'>{name}: {count}회</div>", unsafe_allow_html=True)
