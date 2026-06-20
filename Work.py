import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import holidays
from datetime import datetime, date, timedelta
from io import BytesIO

# ==========================================
# 1. 페이지 공통 초기 설정 및 DB 연결
# ==========================================
# ⚠️ st.set_page_config는 오직 메인 스크립트 최상단에서 '한 번만' 호출되어야 합니다.
st.set_page_config(page_title="통합 근무 관리 시스템", layout="wide")

# CSS 스타일 정의 (모든 페이지 공통 적용)
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

# 엑셀 다운로드 유틸리티 함수
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='근무일정')
    return output.getvalue()

# 구글 시트 커넥션 및 데이터 로드
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
        new_db = st.session_state['db'].copy()
        new_db[date_str] = workers_list
        rows = [{"date": d, "workers": ",".join(ws)} for d, ws in new_db.items() if ws]
        df = pd.DataFrame(rows)
        conn.update(data=df)
        st.session_state['db'] = new_db
        st.cache_data.clear()
    except Exception as e:
        st.error(f"저장 중 오류가 발생했습니다. ({e})")

# 전역 데이터 초기화
if 'db' not in st.session_state:
    st.session_state['db'] = load_data()

WORKER_COLORS = {
    "박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", 
    "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"
}
kr_holidays = holidays.KR(language='ko')
today_val = date.today()
current_year = 2026


# ==========================================
# 2. 각 페이지별 독립 함수(콘텐츠) 정의
# ==========================================

# 📄 [페이지 1]: 기존 근무 일정 관리 및 달력
def show_schedule_page():
    # 사이드바 제어 설정 (페이지 내부에서 동작할 사이드바 위젯들)
    st.sidebar.subheader("📅 일정 필터 옵션")
    view_mode = st.sidebar.radio("화면 모드", ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"], index=1, key="view_mode")
    selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=today_val.month - 1, key="selected_month")
    filter_name = st.sidebar.selectbox("🔍 근무자 필터링", ["전체보기"] + list(WORKER_COLORS.keys()), key="filter_name")

    # 날짜 계산
    first_day = date(current_year, selected_month, 1)
    last_day = (date(current_year, selected_month + 1, 1) if selected_month < 12 else date(current_year + 1, 1, 1)) - timedelta(days=1)
    start_pad = (first_day.weekday() + 1) % 7 

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
                    if st.session_state.get('is_admin', False):
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
                                if st.session_state.get('is_admin', False):
                                    new = st.multiselect(f"p_edit_{day_counter}", list(WORKER_COLORS.keys()), default=assigned, key=f"p_{t_str}", label_visibility="collapsed")
                                    if new != assigned:
                                        save_to_sheets(t_str, new)
                                        st.rerun()
                                else:
                                    for n in assigned:
                                        st.markdown(f"<span class='worker-tag' style='background-color:{WORKER_COLORS[n]}'>{n}</span>", unsafe_allow_html=True)
                            day_counter += 1

    # 우측 통계 및 엑셀 출력 레이아웃
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


# 📄 [페이지 2]: 신규 추가하고 싶은 기능 화면 (예: 공지사항 또는 마이페이지 설정 등)
def show_management_page():
    st.title("👤 근무자 인적사항 및 시스템 관리")
    st.write("이 페이지는 멀티페이지 예시 공간입니다. 신규 근무자 추가 정보입력 대시보드나 공지사항 탭 등으로 커스텀할 수 있습니다.")
    
    st.subheader("📋 현재 등록된 고정 근무자 리스트")
    df_workers = pd.DataFrame([
        {"근무자명": name, "식별 컬러색상": color, "소속": "운영팀"} 
        for name, color in WORKER_COLORS.items()
    ])
    st.table(df_workers)
    
    st.subheader("📢 관리자 알림 설정")
    if st.session_state.get('is_admin', False):
        st.text_area("근무자들에게 전달할 공지사항을 입력하세요", placeholder="여기에 작성한 내용은 저장할 수 있습니다.")
        st.button("공지사항 저장 (예시용)")
    else:
        st.info("🔒 공지사항 작성 기능은 관리자 비밀번호 인증 시에만 활성화됩니다.")


# ==========================================
# 3. 사이드바 공통 관리자 인증 및 내비게이션 제어
# ==========================================
st.sidebar.title("⚙️ 시스템 메인 제어")

# 공통 비밀번호 확인
password = st.sidebar.text_input("🔑 관리자 비밀번호", type="password")
st.session_state['is_admin'] = (password == "1234")

if st.session_state['is_admin']:
    st.sidebar.success("🔓 관리자 모드 가동 중")
else:
    st.sidebar.info("👁️ 조회 전용 모드")

st.sidebar.divider()

# 최신 Streamlit 방식을 이용한 네비게이션 선언 및 실행
page_schedule = st.Page(show_schedule_page, title="📅 근무 일정 조회/수정", icon="📆")
page_manage = st.Page(show_management_page, title="👤 근무자 및 정보 관리", icon="⚙️")

# 라우팅 맵 선언
pg = st.navigation([page_schedule, page_manage])
pg.run()
