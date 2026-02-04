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
    /* PC 달력 칸 스타일 */
    [data-testid="column"] {
        height: 250px !important; 
        border: 1px solid #dee2e6;
        padding: 10px !important;
        background-color: #ffffff;
        border-radius: 8px;
    }
    /* 모바일 카드 스타일 */
    .mobile-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
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
        border: 1px solid rgba(0,0,0,0.1);
    }
    .date-header {
        font-size: 1.2rem;
        font-weight: bold;
        border-bottom: 2px solid #f1f3f5;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 및 로그 관리 함수
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

def add_log(date_str, action, detail):
    logs = load_json(LOG_FILE)
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": date_str,
        "action": action,
        "detail": str(detail)
    })
    save_json(LOG_FILE, logs[-50:])

# 3. 데이터 초기화
if 'db' not in st.session_state:
    st.session_state['db'] = load_json(DATA_FILE)

WORKER_COLORS = {
    "박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", 
    "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"
}
kr_holidays = holidays.KR(language='ko')

# 4. 사이드바 제어
st.sidebar.title("🛠️ 설정 및 관리")
password = st.sidebar.text_input("관리자 비밀번호", type="password")
is_admin = (password == "1234") # 실제 비번으로 변경 권장

view_mode = st.sidebar.radio("화면 모드", ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"])
selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=date.today().month - 1)

if is_admin:
    st.sidebar.success("🔓 관리자 모드 활성화")
    if st.sidebar.checkbox("📜 변경 로그 확인"):
        st.sidebar.write("### 최근 변경 기록")
        st.sidebar.table(load_json(LOG_FILE))
else:
    st.sidebar.info("🔒 조회 전용 모드")

# 5. 날짜 계산
current_year = 2026
first_day = date(current_year, selected_month, 1)
start_pad = (first_day.weekday() + 1) % 7 
last_day = (date(current_year, selected_month + 1, 1) if selected_month < 12 else date(current_year + 1, 1, 1)) - timedelta(days=1)

# 6. 메인 화면 출력
col_cal, col_stat = st.columns([4, 1])

with col_cal:
    st.title(f"{selected_month}월 근무현황")

    if view_mode == "📱 리스트 보기 (모바일)":
        for d in range(1, last_day.day + 1):
            this_date = date(current_year, selected_month, d)
            d_str = this_date.strftime('%Y-%m-%d')
            is_off = (this_date in kr_holidays) or (this_date.weekday() in [0, 6])
            h_name = kr_holidays.get(this_date, "")
            weekday_name = ["월", "화", "수", "목", "금", "토", "일"][this_date.weekday()]
            
            st.markdown(f"""<div class='mobile-card'><div class='mobile-date' style='color:{"red" if is_off else "black"}; font-weight:bold;'>
                        {d}일 ({weekday_name}) {h_name}</div>""", unsafe_allow_html=True)
            
            assigned = st.session_state['db'].get(d_str, [])
            if not is_off:
                if is_admin:
                    selected = st.multiselect(f"edit_{d}", list(WORKER_COLORS.keys()), default=assigned, key=f"mob_{d_str}", label_visibility="collapsed")
                    if selected != assigned:
                        st.session_state['db'][d_str] = selected
                        save_json(DATA_FILE, st.session_state['db'])
                        add_log(d_str, "수정(모바일)", selected)
                        st.rerun()
                else:
                    for name in assigned:
                        bg = WORKER_COLORS.get(name, "#eee")
                        st.markdown(f"<span class='worker-tag' style='background-color:{bg};'>{name}</span>", unsafe_allow_html=True)
            else:
                st.markdown("<small style='color:#ccc;'>휴무</small>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    else: # PC 달력 보기
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
                        st.markdown(f"<div class='date-header' style='color: {'red' if is_off else 'black'};'>{day_counter}</div>", unsafe_allow_html=True)
                        
                        assigned = st.session_state['db'].get(d_str, [])
                        if not is_off:
                            if is_admin:
                                selected = st.multiselect("n", list(WORKER_COLORS.keys()), default=assigned, max_selections=2, key=f"pc_{d_str}", label_visibility="collapsed")
                                if selected != assigned:
                                    st.session_state['db'][d_str] = selected
                                    save_json(DATA_FILE, st.session_state['db'])
                                    add_log(d_str, "수정(PC)", selected)
                                    st.rerun()
                            else:
                                for name in assigned:
                                    st.markdown(f"<span class='worker-tag' style='background-color:{WORKER_COLORS.get(name)};'>{name}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='text-align:center; color:#eee; margin-top:20px;'>휴무</div>", unsafe_allow_html=True)
                        day_counter += 1

with col_stat:
    st.subheader("📊 통계")
    prefix = f"{current_year}-{selected_month:02d}"
    all_selected = [n for k, names in st.session_state['db'].items() if k.startswith(prefix) for n in names]
    for name, color in WORKER_COLORS.items():
        count = all_selected.count(name)
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:5px; margin-bottom:5px; font-weight:bold; border:1px solid #ddd;'>{name}: {count}회</div>", unsafe_allow_html=True)
    
    if is_admin and st.button("🔄 데이터 초기화"):
        st.session_state['db'] = {}
        save_json(DATA_FILE, {})
        add_log("ALL", "초기화", "전체삭제")
        st.rerun()
