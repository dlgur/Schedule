import streamlit as st
import pandas as pd
import holidays
import json
import os
from datetime import datetime, date, timedelta

# 1. 초기 설정 및 스타일링
st.set_page_config(page_title="근무 일정 공유 시스템", layout="wide")

st.markdown("""
    <style>
    [data-testid="column"] {
        height: 250px !important; 
        border: 1px solid #dee2e6;
        padding: 10px !important;
        background-color: #ffffff;
        border-radius: 8px;
    }
    .worker-tag {
        display: block;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        margin-top: 5px;
        color: black;
        text-align: center;
    }
    .date-header {
        font-size: 1.2rem;
        font-weight: bold;
        border-bottom: 1px solid #eee;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 및 로그 관리 함수
DATA_FILE = "schedule_db.json"
LOG_FILE = "action_log.json"

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {} if "db" in file_path else []

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_log(date_str, action, detail):
    logs = load_json(LOG_FILE)
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": date_str,
        "action": action,
        "detail": str(detail)
    })
    save_json(LOG_FILE, logs[-50:]) # 최근 50개 유지

# 3. 상태 관리
if 'db' not in st.session_state:
    st.session_state['db'] = load_json(DATA_FILE)

WORKER_COLORS = {
    "박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", 
    "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"
}
kr_holidays = holidays.KR(language='ko')

# 4. 사이드바: 관리자 인증 및 설정
st.sidebar.title("🛠️ 메뉴")
password = st.sidebar.text_input("관리자 비밀번호", type="password")
is_admin = (password == "1234") # 실제 비밀번호로 변경하세요

selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=date.today().month - 1)

if is_admin:
    st.sidebar.success("🔓 관리자 모드 활성화")
    if st.sidebar.checkbox("변경 로그 확인"):
        st.sidebar.write("### 📜 최근 변경 기록")
        st.sidebar.table(load_json(LOG_FILE))
else:
    st.sidebar.info("🔒 현재 조회 전용 모드입니다.")

# 5. 달력 계산
current_year = 2026
first_day = date(current_year, selected_month, 1)
start_pad = (first_day.weekday() + 1) % 7 
last_day = (date(current_year, selected_month + 1, 1) if selected_month < 12 else date(current_year + 1, 1, 1)) - timedelta(days=1)

# 6. 메인 화면
col_cal, col_stat = st.columns([4, 1])

with col_cal:
    st.title(f"🗓️ {current_year}년 {selected_month}월 근무현황")
    
    header_cols = st.columns(7)
    for i, day in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
        header_cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)

    day_counter = 1
    total_slots = start_pad + last_day.day
    for w in range((total_slots + 6) // 7):
        week_cols = st.columns(7)
        for d in range(7):
            idx = w * 7 + d
            with week_cols[d]:
                if idx < start_pad or day_counter > last_day.day:
                    st.empty()
                else:
                    this_date = date(current_year, selected_month, day_counter)
                    d_str = this_date.strftime('%Y-%m-%d')
                    is_off = (this_date in kr_holidays) or (this_date.weekday() in [0, 6])
                    
                    st.markdown(f"<div class='date-header'>{day_counter}</div>", unsafe_allow_html=True)

                    # 현재 저장된 근무자
                    assigned = st.session_state['db'].get(d_str, [])

                    if not is_off:
                        if is_admin:
                            # 관리자만 수정 가능
                            selected = st.multiselect("n", list(WORKER_COLORS.keys()), default=assigned, max_selections=2, key=f"ms_{d_str}", label_visibility="collapsed")
                            if selected != assigned:
                                st.session_state['db'][d_str] = selected
                                save_json(DATA_FILE, st.session_state['db'])
                                add_log(d_str, "수정", selected)
                                st.rerun()
                        else:
                            # 동료들은 이름표만 확인
                            for name in assigned:
                                bg = WORKER_COLORS.get(name, "#eee")
                                st.markdown(f"<span class='worker-tag' style='background-color:{bg};'>{name}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='text-align:center; color:#eee; margin-top:20px;'>휴무</div>", unsafe_allow_html=True)
                    day_counter += 1

with col_stat:
    st.subheader("📊 인원별 통계")
    prefix = f"{current_year}-{selected_month:02d}"
    all_selected = [n for k, names in st.session_state['db'].items() if k.startswith(prefix) for n in names]
    for name, color in WORKER_COLORS.items():
        count = all_selected.count(name)
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:5px; margin-bottom:5px; font-weight:bold;'>{name}: {count}회</div>", unsafe_allow_html=True)