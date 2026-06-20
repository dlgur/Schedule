import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import holidays
from datetime import datetime, date, timedelta
from io import BytesIO

# ==========================================
# 1. 페이지 설정 및 공통 CSS 디자인
# ==========================================
st.set_page_config(page_title="통합 매니지먼트 시스템", layout="wide")

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
        df.to_excel(writer, index=False, sheet_name='데이터수집')
    return output.getvalue()

구글 시트의 탭 구성(구조)을 잡았는데도 이 에러가 여전히 발생한다면, streamlit-gsheets 라이브러리가 첫 번째 탭을 인식하는 기본 방식과 내부 설정 이름이 어긋나서 그렇습니다.

현재 작성되어 있는 기존 코드의 load_schedule_data() 함수는 worksheet 지정 없이 conn.read()를 바로 호출하고 있습니다. 이 경우 라이브러리는 무조건 구글 시트의 맨 첫 번째 탭을 읽으려고 시도합니다.

만약 스프레드시트의 첫 번째 탭 이름을 영어 소문자 sheet1이나 다른 이름으로 바꾸셨거나, 순서가 꼬였다면 라이브러리가 길을 잃고 WorksheetNotFound 에러를 뿜을 수 있습니다.

이를 완벽하게 해결하기 위해 코드의 데이터 로드 로직을 명확한 탭 이름 지정 방식으로 수정하는 것이 가장 안전합니다.

🛠️ 코드 수정 및 동기화 (이 부분만 덮어씌우세요)
구글 시트의 탭 이름을 아래와 같이 3개로 확실히 정하셨다면, 코드 상단의 3. 데이터베이스 연결 섹션에 있는 로드 함수들을 아래 코드로 깔끔하게 교체해 주세요.

Python
# ==========================================
# 3. 데이터베이스 연결 (Google Sheets) - 에러 방지 보완본
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# --- [DB 함수] 1. 근무 일정 데이터 로드 ---
def load_schedule_data():
    try:
        # 💡 첫 번째 탭 이름을 '근무표' 또는 'Sheet1' 등 명확하게 지정해 줍니다.
        # 여기서는 구글 시트의 첫 번째 탭 이름이 "Sheet1"이라고 가정합니다. 
        # 만약 한글로 '근무표'라고 하셨다면 worksheet="근무표" 로 수정하세요!
        df = conn.read(worksheet="Sheet1", ttl="1m") 
        
        if df is None or df.empty or 'date' not in df.columns:
            return {}
        db = {}
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['workers']):
                db[str(row['date'])] = str(row['workers']).split(',')
        return db
    except Exception as e:
        # 에러 발생 시 앱이 완전히 멈추지 않도록 빈 사전 반환
        return {}

# --- [DB 함수] 2. 재고 및 로그 데이터 로드 ---
def load_inventory_data():
    # 구글 시트에 아직 탭이 없거나 로딩 오류가 날 때를 대비해 기본 구조 선언
    df_inv = pd.DataFrame(columns=["품목코드", "품목명", "수량", "단가", "비고"])
    df_logs = pd.DataFrame(columns=["일시", "작업구분", "품목명", "내용", "작업자"])
    
    try:
        df_inv = conn.read(worksheet="inventory", ttl="0m")
    except Exception as e:
        st.sidebar.error("⚠️ 구글 시트에서 'inventory' 탭을 찾을 수 없습니다.")
        
    try:
        df_logs = conn.read(worksheet="logs", ttl="0m")
    except Exception as e:
        st.sidebar.error("⚠️ 구글 시트에서 'logs' 탭을 찾을 수 없습니다.")
        
    return df_inv, df_logs

# --- [DB 함수] 2. 재고 및 로그 데이터 로드 ---
def load_inventory_data():
    try:
        df_inv = conn.read(worksheet="inventory", ttl="0m") # 재고는 실시간 조회가 중요하므로 ttl=0
        df_logs = conn.read(worksheet="logs", ttl="0m")
        return df_inv, df_logs
    except Exception as e:
        # 시트가 비어있거나 없을 때 예외 처리 및 기본 프레임 반환
        df_inv = pd.DataFrame(columns=["품목코드", "품목명", "수량", "단가", "비고"])
        df_logs = pd.DataFrame(columns=["일시", "작업구분", "품목명", "내용", "작업자"])
        return df_inv, df_logs

# 데이터 및 설정 초기화
if 'db' not in st.session_state:
    st.session_state['db'] = load_schedule_data()

WORKER_COLORS = {
    "박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", 
    "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"
}
kr_holidays = holidays.KR(language='ko')
today_val = date.today()
current_year = 2026

# ==========================================
# 4. 사이드바 메인 공통 제어 (권한 및 메뉴)
# ==========================================
st.sidebar.title("⚙️ 통합 관리 시스템")

# 비밀번호 통합 검증 (재고 관리, 근무 수정 공용)
password = st.sidebar.text_input("관리자 비밀번호", type="password")
is_admin = (password == "1234") 

if is_admin:
    st.sidebar.success("🔓 관리자 권한 활성화")
else:
    st.sidebar.info("👁️ 조회 전용 모드")

st.sidebar.divider()

# 대메뉴 전환 기능
main_menu = st.sidebar.radio("원하는 시스템을 선택하세요", ["📅 근무 일정 관리", "📦 재고 관리 시스템"])

st.sidebar.divider()


# ==========================================
# 메뉴 A: 📅 근무 일정 관리 (기존 기능 완전히 유지)
# ==========================================
if main_menu == "📅 근무 일정 관리":
    
    # 근무 일정 전용 사이드바 옵션들
    view_mode = st.sidebar.radio("화면 모드", ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"], index=1)
    selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=today_val.month - 1)
    filter_name = st.sidebar.selectbox("🔍 근무자 필터링", ["전체보기"] + list(WORKER_COLORS.keys()))

    # 근무자 데이터 저장 함수
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
            st.error(f"저장 중 오류가 발생했습니다. 잠시 후 다시 시도하세요. ({e})")

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

# ==========================================
# 메뉴 B: 📦 재고 관리 시스템 (구글 시트 저장 및 로그 기능 추가)
# ==========================================
elif main_menu == "📦 재고 관리 시스템":
    st.title("📦 재고 관리 및 수불대장")
    
    # 구글 시트로부터 재고 데이터 로드
    df_inv, df_logs = load_inventory_data()
    
    # 내부 서브 탭 분할
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["🔍 현재 재고 조회", "🔄 재고 입/출고", "➕ 신규 품목 등록", "📜 수정 내역 로그"])
    
    # --- 서브탭 1: 현재 재고 조회 (비밀번호 불필요) ---
    with sub_tab1:
        st.subheader("🔍 실시간 재고 현황")
        search_keyword = st.text_input("품목명 검색", key="inv_search")
        
        if search_keyword:
            filtered_df = df_inv[df_inv["품목명"].str.contains(search_keyword, na=False)]
        else:
            filtered_df = df_inv

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="총 품목 종수", value=len(df_inv))
        with col2:
            if not df_inv.empty:
                df_inv["수량"] = pd.to_numeric(df_inv["수량"], errors='coerce').fillna(0)
                df_inv["단가"] = pd.to_numeric(df_inv["단가"], errors='coerce').fillna(0)
                total_value = (df_inv["수량"] * df_inv["단가"]).sum()
                st.metric(label="총 자산 가치액", value=f"{total_value:,.0f} 원")

    # --- 서브탭 2: 재고 입/출고 관리 (관리자 권한 필수) ---
    with sub_tab2:
        st.subheader("🔄 재고 수량 변경")
        if not is_admin:
            st.warning("🔒 수정 권한이 없습니다. 사이드바에 올바른 관리자 비밀번호를 입력해 주세요.")
        elif df_inv.empty:
            st.info("등록된 품목이 없습니다. 신규 품목을 먼저 등록해 주세요.")
        else:
            item_list = df_inv["품목명"].tolist()
            selected_item = st.selectbox("수정할 품목을 선택하세요", item_list)
            
            item_row = df_inv[df_inv["품목명"] == selected_item].iloc[0]
            st.info(f"현재 보유 수량: {item_row['수량']}개 | 품목 단가: {int(item_row['단가']):,}원")
            
            with st.form("inv_update_form"):
                action = st.radio("작업 선택", ["입고 (+)", "출고 (-)"])
                quantity_change = st.number_input("수량 입력", min_value=1, step=1, value=1)
                reason = st.text_input("조정 사유", value="정기 수량 조정")
                
                submit_btn = st.form_submit_button("시트 데이터 반영")
                
                if submit_btn:
                    idx = df_inv[df_inv["품목명"] == selected_item].index[0]
                    current_qty = int(df_inv.at[idx, "수량"])
                    
                    if action == "입고 (+)":
                        new_qty = current_qty + quantity_change
                        df_inv.at[idx, "수량"] = new_qty
                        log_msg = f"기존 {current_qty}개 -> {new_qty}개 (사유: {reason})"
                        st.success(f"{selected_item} {quantity_change}개 입고 처리되었습니다.")
                    elif action == "출고 (-)":
                        if current_qty < quantity_change:
                            st.error("재고가 부족하여 출고할 수 없습니다.")
                            st.stop()
                        new_qty = current_qty - quantity_change
                        df_inv.at[idx, "수량"] = new_qty
                        log_msg = f"기존 {current_qty}개 -> {new_qty}개 (사유: {reason})"
                        st.success(f"{selected_item} {quantity_change}개 출고 처리되었습니다.")
                    
                    # 구글 시트 저장
                    conn.update(worksheet="inventory", data=df_inv)
                    
                    # 로그 생성 및 저장
                    new_log = pd.DataFrame([{
                        "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "작업구분": action,
                        "품목명": selected_item,
                        "내용": log_msg,
                        "작업자": "관리자"
                    }])
                    df_logs = pd.concat([df_logs, new_log], ignore_index=True)
                    conn.update(worksheet="logs", data=df_logs)
                    st.cache_data.clear()
                    st.rerun()

    # --- 서브탭 3: 신규 품목 등록 (관리자 권한 필수) ---
    with sub_tab3:
        st.subheader("➕ 신규 품목 데이터 베이스 추가")
        if not is_admin:
            st.warning("🔒 수정 권한이 없습니다. 사이드바에 올바른 관리자 비밀번호를 입력해 주세요.")
        else:
            with st.form("inv_insert_form", clear_on_submit=True):
                code = st.text_input("품목코드 (중복 불가)")
                name = st.text_input("품목명")
                qty = st.number_input("초기 수량", min_value=0, step=1, value=0)
                price = st.number_input("단가", min_value=0, step=100, value=0)
                remark = st.text_input("비고 항목")
                
                add_btn = st.form_submit_button("신규 등록")
                
                if add_btn:
                    if not code or not name:
                        st.error("품목코드와 품목명은 필수 항목입니다.")
                    elif str(code) in df_inv["품목코드"].astype(str).values:
                        st.error("이미 등록된 품목코드입니다.")
                    else:
                        new_row = pd.DataFrame([{"품목코드": code, "품목명": name, "수량": qty, "단가": price, "비고": remark}])
                        df_inv = pd.concat([df_inv, new_row], ignore_index=True)
                        conn.update(worksheet="inventory", data=df_inv)
                        
                        # 등록 로그 기록
                        new_log = pd.DataFrame([{
                            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "작업구분": "품목등록",
                            "품목명": name,
                            "내용": f"신규 마스터 데이터 등록 (초기수량: {qty}개)",
                            "작업자": "관리자"
                        }])
                        df_logs = pd.concat([df_logs, new_log], ignore_index=True)
                        conn.update(worksheet="logs", data=df_logs)
                        st.cache_data.clear()
                        st.success(f"새로운 품목 [{name}]이 등록되었습니다.")
                        st.rerun()

    # --- 서브탭 4: 수정 내역 로그 확인 (비밀번호 불필요) ---
    with sub_tab4:
        st.subheader("📜 재고 수불 및 변경 이력 로그")
        if not df_logs.empty:
            # 최신 로그가 맨 상단에 나오도록 정렬 후 출력
            st.dataframe(df_logs.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("기록된 변경 이력이 없습니다.")
