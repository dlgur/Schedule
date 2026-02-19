import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import holidays
import json
from datetime import datetime, date, timedelta
from io import BytesIO

# 1. 페이지 설정 및 CSS 디자인
st.set_page_config(page_title="근무 일정 관리 시스템", layout="wide")

st.markdown("""
    <style>
    [data-testid="column"] {
        height: 250px !important; 
        border: 1px solid #dee2e6;
        padding: 10px !important;
        background-color: #ffffff;
        border-radius: 8px;
    }
    .today-box { background-color: #fff9db !important; border: 2px solid #fcc419 !important; }
    .mobile-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .worker-tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        margin: 2px;
        color: black;
        border: 1px solid rgba(0,0,0,0.1);
    }
    .today-badge {
        background-color: #fcc419;
        color: black;
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 5px;
        display: inline-block;
    }
    .date-header {
        font-size: 1.2rem;
        font-weight: bold;
        border-bottom: 2px solid #f1f3f5;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 유틸리티 함수 (엑셀 변환)
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='근무일정')
    return output.getvalue()

# 3. 데이터베이스 연결 (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(ttl="1m") 
        if df is None or df.empty or 'date' not in df.columns:
            return {}
        db = {}
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['workers']):
                db[str(row['date'])] = str(row['workers']).split(',')
        return db
    except:
        return {}

def save_to_sheets(date_str, workers_list):
    try:
        # API 과부하 방지: 현재 메모리 데이터를 기반으로 업데이트
        new_db = st.session_state['db'].copy()
        new_db[date_str] = workers_list
        
        rows = [{"date": d, "workers": ",".join(ws)} for d, ws in new_db.items() if ws]
        df = pd.DataFrame(rows)
        
        # 구글 시트 전송
        conn.update(data=df)
        
        # 메모리 즉시 반영 및 캐시 삭제
        st.session_state['db'] = new_db
        st.cache_data.clear()
    except Exception as e:
        st.error(f"저장 중 오류가 발생했습니다. 잠시 후 다시 시도하세요. ({e})")

# 4. 데이터 및 설정 초기화
if 'db' not in st.session_state:
    st.session_state['db'] = load_data()

WORKER_COLORS = {
    "박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", 
    "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"
}
kr_holidays = holidays.KR(language='ko')
today_val = date.today()

# 5. 사이드바 제어
st.sidebar.title("🛠️ 설정 및 관리")
password = st.sidebar.text_input("관리자 비밀번호", type="password")
is_admin = (password == "1234") 

view_mode = st.sidebar.radio("화면 모드", ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"], index=1)
selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=today_val.month - 1)
filter_name = st.sidebar.selectbox("🔍 근무자 필터링", ["전체보기"] + list(WORKER_COLORS.keys()))

# 6. 날짜 계산
current_year = 2026
first_day = date(current_year, selected_month, 1)
last_day = (date(current_year, selected_month + 1, 1) if selected_month < 12 else date(current_year + 1, 1, 1)) - timedelta(days=1)
start_pad = (first_day.weekday() + 1) % 7 

# 7. 메인 화면 구성
col_cal, col_stat = st.columns([4, 1])

with col_cal:
    st.title(f"{selected_month}월 근무현황")

    if view_mode == "📱 리스트 보기 (모바일)":
        for d in range(1, last_day.day + 1):
            t_date = date(current_year, selected_month, d)
            d_str = t_date.strftime('%Y-%m-%d')
            assigned = st.session_state['db'].get(d_str, [])
            
            is_match = (filter_name == "전체보기") or (filter_name in assigned)
            is_today = (t_date == today_val)
            is_off = (t_date in kr_holidays) or (t_date.weekday() in [0, 6])
            
            # 카드 렌더링 (HTML 태그 깨짐 방지 처리)
            card_style = f"opacity: {'1.0' if is_match else '0.3'}; {'border:2px solid #fcc419; background-color:#fff9db;' if is_today else ''}"
            today_badge = "<span class='today-badge'>TODAY</span>" if is_today else ""
            
            st.markdown(f"""
                <div class='mobile-card' style='{card_style}'>
                    <div style='color:{"red" if is_off else "black"}; font-weight:bold; font-size:1.1rem;'>
                        {d}일 ({["월","화","수","목","금","토","일"][t_date.weekday()]}) {kr_holidays.get(t_date, "")} {today_badge}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if not is_off:
                if is_admin:
                    new = st.multiselect(f"m_edit_{d}", list(WORKER_COLORS.keys()), default=assigned, key=f"m_{d_str}", label_visibility="collapsed")
                    if new != assigned:
                        save_to_sheets(d_str, new)
                        st.rerun()
                else:
                    if assigned:
                        tags = "".join([f"<span class='worker-tag' style='background-color:{WORKER_COLORS[n]}'>{n}</span>" for n in assigned])
                        st.markdown(f"<div>{tags}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("배정 인원 없음")
            else:
                st.caption("휴무")
            st.write("")

    else: # PC 달력 보기
        header_cols = st.columns(7)
        for i, day in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
            header_cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)

        day_counter = 1
        for w in range(((start_pad + last_day.day) + 6) // 7):
            cols = st.columns(7)
            for d in range(7):
                idx = w * 7 + d
                with cols[d]:
                    if idx < start_pad or day_counter > last_day.day:
                        st.empty()
                    else:
                        t_date = date(current_year, selected_month, day_counter)
                        t_str = t_date.strftime('%Y-%m-%d')
                        assigned = st.session_state['db'].get(t_str, [])
                        is_today = (t_date == today_val)
                        is_off = (t_date in kr_holidays) or (t_date.weekday() in [0, 6])
                        is_match = (filter_name == "전체보기") or (filter_name in assigned)

                        box_class = "today-box" if is_today else ""
                        dim_style = f"opacity: {'1.0' if is_match else '0.3'};"
                        
                        st.markdown(f"<div class='date-header {box_class}' style='{dim_style} color: {'red' if is_off else 'black'};'>{day_counter}</div>", unsafe_allow_html=True)
                        
                        if not is_off:
                            if is_admin:
                                new = st.multiselect(f"p_edit_{day_counter}", list(WORKER_COLORS.keys()), default=assigned, key=f"p_{t_str}", label_visibility="collapsed")
                                if new != assigned:
                                    save_to_sheets(t_str, new)
                                    st.rerun()
                            else:
                                for n in assigned:
                                    st.markdown(f"<span class='worker-tag' style='background-color:{WORKER_COLORS[n]}'>{n}</span>", unsafe_allow_html=True)
                        day_counter += 1

# 8. 통계 및 엑셀 내보내기
with col_stat:
    st.subheader("📊 통계")
    export_data = []
    month_workers = []
    
    for d in range(1, last_day.day + 1):
        d_date = date(current_year, selected_month, d)
        d_str = d_date.strftime('%Y-%m-%d')
        assigned = st.session_state['db'].get(d_str, [])
        month_workers.extend(assigned)
        export_data.append({
            "날짜": d_str, 
            "요일": ["월","화","수","목","금","토","일"][d_date.weekday()], 
            "근무자": ", ".join(assigned), 
            "비고": kr_holidays.get(d_date, "")
        })
    
    for name, color in WORKER_COLORS.items():
        if filter_name != "전체보기" and name != filter_name: continue
        count = month_workers.count(name)
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:5px; margin-bottom:5px; font-weight:bold; color:black;'>{name}: {count}회</div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("💾 내보내기")
    if export_data:
        excel_data = to_excel(pd.DataFrame(export_data))
        st.download_button(
            label="📊 Excel 다운로드", 
            data=excel_data, 
            file_name=f"근무표_{selected_month}월.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
