import streamlit as st
import pandas as pd
import holidays
import json
import os
from datetime import datetime, date, timedelta
from io import BytesIO

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
    /* 강조 효과 */
    .today-box { background-color: #fff9db !important; border: 2px solid #fcc419 !important; }
    .highlight-card { border: 3px solid #4dabf7 !important; box-shadow: 0px 0px 15px rgba(77, 171, 247, 0.4) !important; }
    .dimmed-card { opacity: 0.3; }
    
    /* 모바일 카드 스타일 */
    .mobile-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .today-badge {
        background-color: #fcc419;
        color: black;
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 5px;
        vertical-align: middle;
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

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='근무일정')
    return output.getvalue()

# 3. 데이터 초기화
if 'db' not in st.session_state:
    st.session_state['db'] = load_json(DATA_FILE)

WORKER_COLORS = {
    "박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", 
    "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"
}
kr_holidays = holidays.KR(language='ko')
today_val = date.today()

# 4. 사이드바 제어
st.sidebar.title("🛠️ 설정 및 관리")
password = st.sidebar.text_input("관리자 비밀번호", type="password")
is_admin = (password == "1234") 

view_mode = st.sidebar.radio("화면 모드", ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"], index=1)
selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=today_val.month - 1)
filter_name = st.sidebar.selectbox("🔍 근무자 필터링", ["전체보기"] + list(WORKER_COLORS.keys()))

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
            assigned = st.session_state['db'].get(d_str, [])
            
            is_match = (filter_name == "전체보기") or (filter_name in assigned)
            is_today = (this_date == today_val)
            is_off = (this_date in kr_holidays) or (this_date.weekday() in [0, 6])
            
            card_class = "highlight-card" if (filter_name != "전체보기" and is_match) else ""
            if filter_name != "전체보기" and not is_match: card_class = "dimmed-card"
            today_style = "border: 2px solid #fcc419; background-color: #fff9db;" if is_today else ""
            
            # 카드 컨테이너 시작
            st.markdown(f"""
                <div class='mobile-card {card_class}' style='{today_style}'>
                    <div style='color:{"red" if is_off else "black"}; font-weight:bold; font-size:1.1rem;'>
                        {d}일 ({["월","화","수","목","금","토","일"][this_date.weekday()]}) 
                        {kr_holidays.get(this_date, "")} {"<span class='today-badge'>TODAY</span>" if is_today else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 근무자 표시 및 수정 (태그 오류 방지를 위해 div 밖에서 처리)
            if not is_off:
                if is_admin:
                    selected = st.multiselect(f"m_edit_{d}", list(WORKER_COLORS.keys()), default=assigned, key=f"mob_{d_str}", label_visibility="collapsed")
                    if selected != assigned:
                        st.session_state['db'][d_str] = selected
                        save_json(DATA_FILE, st.session_state['db'])
                        add_log(d_str, "수정(모바일)", selected)
                        st.rerun()
                else:
                    if assigned:
                        for name in assigned:
                            op = "1.0" if (filter_name == "전체보기" or name == filter_name) else "0.3"
                            st.markdown(f"<span class='worker-tag' style='background-color:{WORKER_COLORS.get(name)}; opacity:{op};'>{name}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<small style='color:#ccc;'>배정 인원 없음</small>", unsafe_allow_html=True)
            else:
                st.markdown("<small style='color:#ccc;'>휴무</small>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    else: # PC 달력 보기
        header_cols = st.columns(7)
        for i, day in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
            header_cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)

        day_counter = 1
        for w in range(((start_pad + last_day.day) + 6) // 7):
            week_cols = st.columns(7)
            for d in range(7):
                idx = w * 7 + d
                with week_cols[d]:
                    if idx < start_pad or day_counter > last_day.day:
                        st.empty()
                    else:
                        this_date = date(current_year, selected_month, day_counter)
                        d_str = this_date.strftime('%Y-%m-%d')
                        assigned = st.session_state['db'].get(d_str, [])
                        is_today = (this_date == today_val)
                        is_off = (this_date in kr_holidays) or (this_date.weekday() in [0, 6])
                        is_match = (filter_name == "전체보기") or (filter_name in assigned)

                        today_class = "today-box" if is_today else ""
                        dim_style = "opacity: 0.3;" if (filter_name != "전체보기" and not is_match) else ""
                        highlight_style = "border: 3px solid #4dabf7;" if (filter_name != "전체보기" and is_match) else ""

                        st.markdown(f"<div class='date-header {today_class}' style='{dim_style} {highlight_style} color: {'red' if is_off else 'black'};'>{day_counter} {'(오늘)' if is_today else ''}</div>", unsafe_allow_html=True)
                        
                        if not is_off:
                            if is_admin:
                                selected = st.multiselect(f"p_edit_{day_counter}", list(WORKER_COLORS.keys()), default=assigned, key=f"pc_{d_str}", label_visibility="collapsed")
                                if selected != assigned:
                                    st.session_state['db'][d_str] = selected
                                    save_json(DATA_FILE, st.session_state['db'])
                                    add_log(d_str, "수정(PC)", selected)
                                    st.rerun()
                            else:
                                for name in assigned:
                                    op = "1.0" if (filter_name == "전체보기" or name == filter_name) else "0.3"
                                    st.markdown(f"<span class='worker-tag' style='background-color:{WORKER_COLORS.get(name)}; opacity:{op};'>{name}</span>", unsafe_allow_html=True)
                        day_counter += 1

with col_stat:
    st.subheader("📊 통계")
    prefix = f"2026-{selected_month:02d}"
    
    export_data = []
    all_selected_workers = []
    
    for d in range(1, last_day.day + 1):
        d_date = date(2026, selected_month, d)
        d_str = d_date.strftime('%Y-%m-%d')
        assigned = st.session_state['db'].get(d_str, [])
        all_selected_workers.extend(assigned)
        export_data.append({"날짜": d_str, "요일": ["월","화","수","목","금","토","일"][d_date.weekday()], "근무자": ", ".join(assigned), "비고": kr_holidays.get(d_date, "")})
    
    for name, color in WORKER_COLORS.items():
        if filter_name != "전체보기" and name != filter_name: continue
        count = all_selected_workers.count(name)
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:5px; margin-bottom:5px; font-weight:bold; color:black;'>{name}: {count}회</div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("💾 내보내기")
    excel_data = to_excel(pd.DataFrame(export_data))
    st.download_button(label="📊 Excel 다운로드", data=excel_data, file_name=f"근무표_{selected_month}월.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if is_admin and st.button("🔄 데이터 초기화"):
        st.session_state['db'] = {}
        save_json(DATA_FILE, {})
        st.rerun()
