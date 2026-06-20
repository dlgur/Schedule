import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import holidays
from datetime import datetime, date, timedelta
from io import BytesIO

# ==========================================
# 1. 페이지 설정 및 공통 CSS 디자인
# ==========================================
st.set_page_config(page_title="통합 물류 관리 시스템", layout="wide")

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
        df.to_excel(writer, index=False, sheet_name='데이터내보내기')
    return output.getvalue()

# ==========================================
# 3. 데이터베이스 연결 및 로드 (Google Sheets)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# --- [DB 함수] 1. 근무 일정 데이터 로드 ---
def load_schedule_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl="1m") 
        if df is None or df.empty or 'date' not in df.columns:
            return {}
        db = {}
        for _, row in df.iterrows():
            if pd.notna(row['date']) and pd.notna(row['workers']):
                db[str(row['date'])] = str(row['workers']).split(',')
        return db
    except:
        return {}

# --- [DB 함수] 2. 재고 및 로그 데이터 로드 ---
def load_inventory_data():
    df_inv = pd.DataFrame(columns=["품목코드", "품목명", "수량", "비고", "박스당수량", "개당음료수"])
    df_logs = pd.DataFrame(columns=["일시", "작업구분", "품목명", "내용", "작업자"])
    
    # 캐시 무효화를 위해 ttl="0m" 유지
    try:
        df_inv = conn.read(worksheet="inventory", ttl="0m")
    except:
        st.sidebar.error("⚠️ 구글 시트에서 'inventory' 탭을 찾을 수 없습니다.")
        
    try:
        df_logs = conn.read(worksheet="logs", ttl="0m")
    except:
        st.sidebar.error("⚠️ 구글 시트에서 'logs' 탭을 찾을 수 없습니다.")
        
    return df_inv, df_logs

# 초기 데이터 전역 세션 등록
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

password = st.sidebar.text_input("관리자 비밀번호", type="password")
is_admin = (password == "1234") 

if is_admin:
    st.sidebar.success("🔓 관리자 권한 활성화")
else:
    st.sidebar.info("👁️ 조회 전용 모드")

st.sidebar.divider()
main_menu = st.sidebar.radio("원하는 시스템을 선택하세요", ["📅 근무 일정 관리", "📦 재고 관리 시스템"])
st.sidebar.divider()


# ==========================================
# 메뉴 A: 📅 근무 일정 관리
# ==========================================
if main_menu == "📅 근무 일정 관리":
    view_mode = st.sidebar.radio("화면 모드", ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"], index=1)
    selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=today_val.month - 1)
    filter_name = st.sidebar.selectbox("🔍 근무자 필터링", ["전체보기"] + list(WORKER_COLORS.keys()))

    def save_to_sheets(date_str, workers_list):
        try:
            new_db = st.session_state['db'].copy()
            new_db[date_str] = workers_list
            rows = [{"date": d, "workers": ",".join(ws)} for d, ws in new_db.items() if ws]
            df = pd.DataFrame(rows)
            conn.update(worksheet="Sheet1", data=df)
            st.session_state['db'] = new_db
            st.cache_data.clear()
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다. ({e})")

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
                "요일": ["월","화","수","목엔","금","토","일"][d_date.weekday()], 
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
# 메뉴 B: 📦 재고 관리 시스템 (TypeError 버그 완벽 해결 버전)
# ==========================================
elif main_menu == "📦 재고 관리 시스템":
    # 타이틀 라인과 실시간 새로고침 버튼 배치
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.title("📦 재고 관리 및 수불대장")
    with col_refresh:
        st.write("") # 패딩용
        if st.button("🔄 실시간 현황 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.toast("구글 시트로부터 최신 데이터를 불러왔습니다!")
            st.rerun()
    
    df_inv, df_logs = load_inventory_data()
    
    # 누락 데이터 및 전처리 안전장치
    for col in ["수량", "박스당수량", "개당음료수"]:
        if col in df_inv.columns:
            df_inv[col] = pd.to_numeric(df_inv[col], errors='coerce').fillna(0).astype(int)
        else:
            df_inv[col] = 0
            
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["🔍 현재 재고 조회", "🔄 재고 입/출고", "➕ 신규 품목 등록", "📜 수정 내역 로그"])
    
    # --- 서브탭 1: 현재 재고 조회 ---
    with sub_tab1:
        st.subheader("🔍 실시간 물류 현황")
        search_keyword = st.text_input("품목명 검색", key="inv_search")
        
        if search_keyword:
            filtered_df = df_inv[df_inv["품목명"].str.contains(search_keyword, na=False)]
        else:
            filtered_df = df_inv

        display_df = filtered_df.copy()
        
        # 1. 계산 제외 및 추산 연산 처리
        def process_rows(row):
            qty = row["수량"]
            box_unit = row["박스당수량"]
            ratio = row["개당음료수"]
            
            box_text = f"{qty // box_unit}박스 (+{qty % box_unit}개)" if box_unit > 0 else f"{qty}개"
            
            if ratio <= 0:
                drink_text = "❌ [계산 제외품]"
                raw_drinks = 999999
            else:
                raw_drinks = qty * ratio
                drink_text = f"{raw_drinks:,} 잔"
                
            return pd.Series([box_text, drink_text, raw_drinks])

        if not display_df.empty:
            display_df[["보유 재고(박스 환산)", "제조 가능 음료수(추산)", "_raw_drinks"]] = display_df.apply(process_rows, axis=1)
            
            # 노출할 최종 컬럼 목록 확정
            cols_to_show = ["품목코드", "품목명", "수량", "보유 재고(박스 환산)", "제조 가능 음료수(추산)", "비고"]
            existing_cols = [c for c in cols_to_show if c in display_df.columns]

            # 2. 10잔 이하 강조 기능 스타일링 규칙 정의
            def highlight_low_stock(row):
                # row는 데이터프레임 전체 열을 가지고 있으므로 안전하게 검색 가능
                styles = [''] * len(existing_cols)
                if row["_raw_drinks"] <= 10:
                    styles = ['background-color: #ffdde1; color: #c92a2a; font-weight: bold;'] * len(existing_cols)
                elif row["_raw_drinks"] <= 30:
                    styles = ['background-color: #fff3bf; color: #e67e22;'] * len(existing_cols)
                return pd.Series(styles, index=existing_cols)

            # [💡 버그 해결] 스타일러를 입히기 전에 화면에 노출할 컬럼과 렌더링에 필요한 컬럼만 추출하여 가공합니다.
            # 스타일을 적용할 대상을 existing_cols로 제한하되, 조건 검사는 axis=1(로우 단위) 전체 열 기준으로 수행
            styled_df = display_df.style.apply(highlight_low_stock, axis=1, subset=existing_cols)
            
            # 스트림릿에는 스타일이 입혀진 결과만 담백하게 전달합니다.
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            st.caption("💡 **안내**: 제조 가능 음료수가 **10잔 이하**인 품목은 <span style='color:#c92a2a; font-weight:bold;'>빨간색</span>, **30잔 이하**는 <span style='color:#e67e22; font-weight:bold;'>노란색</span>으로 강조 표시됩니다. (❌ 표시 품목은 계산 제외 자재입니다.)", unsafe_allow_html=True)
        else:
            st.info("조회할 재고 데이터가 없습니다.")
            
        st.divider()
        st.metric(label="총 취급 품목 종수", value=len(df_inv))

    # --- 서브탭 2: 재고 입/출고 관리 ---
    with sub_tab2:
        st.subheader("🔄 재고 수량 변경 및 박스 계산기")
        if not is_admin:
            st.warning("🔒 수정 권한이 없습니다. 사이드바에 올바른 관리자 비밀번호를 입력해 주세요.")
        elif df_inv.empty:
            st.info("등록된 품목이 없습니다. 신규 품목을 먼저 등록해 주세요.")
        else:
            item_list = df_inv["품목명"].tolist()
            selected_item = st.selectbox("수정할 품목을 선택하세요", item_list)
            
            item_row = df_inv[df_inv["품목명"] == selected_item].iloc[0]
            
            p_box_qty = int(item_row["박스당수량"]) if pd.notna(item_row["박스당수량"]) else 1
            p_drink_ratio = int(item_row["개당음료수"]) if pd.notna(item_row["개당음료수"]) else 0
            current_qty = int(item_row["수량"]) if pd.notna(item_row["수량"]) else 0
            
            ratio_info = f"{p_drink_ratio}잔 제조 가능" if p_drink_ratio > 0 else "❌ 계산 제외 품목"
            st.info(f"💡 현재 보유 낱개: {current_qty}개 | [📦 1박스 = {p_box_qty}개입] | [🥤 기준: {ratio_info}]")
            
            with st.form("inv_update_form"):
                action = st.radio("작업 선택", ["입고 (+)", "출고 (-)"])
                input_mode = st.radio("입력 방식 선택", ["📦 박스 개수로 계산해서 넣기", "✏️ 낱개 개수로 직접 넣기"])
                
                col_calc1, col_calc2 = st.columns(2)
                with col_calc1:
                    box_input = st.number_input("입력할 박스 개수", min_value=0, step=1, value=0)
                with col_calc2:
                    each_input = st.number_input("입력할 낱개 개수", min_value=0, step=1, value=0)
                
                reason = st.text_input("조정 사유", value="정기 수량 조정")
                submit_btn = st.form_submit_button("시트 데이터 반영")
                
                if submit_btn:
                    idx = df_inv[df_inv["품목명"] == selected_item].index[0]
                    
                    if input_mode == "📦 박스 개수로 계산해서 넣기":
                        if p_box_qty <= 0:
                            st.error("해당 품목의 마스터 박스당 수량 설정이 올바르지 않습니다. 낱개 입력을 이용하세요.")
                            st.stop()
                        quantity_change = box_input * p_box_qty
                        detail_text = f"{box_input}박스(총 {quantity_change}개)"
                    else:
                        quantity_change = each_input
                        detail_text = f"{each_input}개(낱개)"
                        
                    if quantity_change <= 0:
                        st.error("입력된 수량이 없습니다. 0보다 큰 값을 입력하세요.")
                        st.stop()
                        
                    if action == "입고 (+)":
                        new_qty = current_qty + quantity_change
                        if p_drink_ratio > 0:
                            calc_drinks = quantity_change * p_drink_ratio
                            log_msg = f"입고: {detail_text} | 추가 음료 생산량: +{calc_drinks}잔 추산 | 사유: {reason}"
                        else:
                            log_msg = f"입고: {detail_text} | [계산제외품목] | 사유: {reason}"
                        st.success(f"{selected_item} 상품이 {detail_text}만큼 입고 완료되었습니다.")
                    elif action == "출고 (-)":
                        if current_qty < quantity_change:
                            st.error(f"창고 재고가 부족합니다. (현재 보유: {current_qty}개 / 출고 시도: {quantity_change}개)")
                            st.stop()
                        new_qty = current_qty - quantity_change
                        log_msg = f"출고: {detail_text} | 사유: {reason}"
                        st.success(f"{selected_item} 상품이 {detail_text}만큼 출고 완료되었습니다.")
                    
                    df_inv.at[idx, "수량"] = new_qty
                    conn.update(worksheet="inventory", data=df_inv)
                    
                    # 로그 마킹
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

    # --- 서브탭 3: 신규 품목 등록 ---
    with sub_tab3:
        st.subheader("➕ 신규 품목 등록 및 마스터 규격 설정")
        if not is_admin:
            st.warning("🔒 수정 권한이 없습니다. 사이드바에 올바른 관리자 비밀번호를 입력해 주세요.")
        else:
            with st.form("inv_insert_form", clear_on_submit=True):
                code = st.text_input("품목코드 (난독화 SKU 패턴 권장)")
                name = st.text_input("품목명")
                
                st.markdown("#### 📐 수량 및 음료수 추산 기준 정의")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    box_qty = st.number_input("📦 1박스당 들어있는 기본 낱개 개수", min_value=1, step=1, value=1)
                with col_m2:
                    is_calc_disabled = st.checkbox("컵, 빨대, 얼음 등 음료수 계산 제외 품목 설정")
                    drink_ratio = st.number_input("🥤 낱개 1개당 제조 가능한 음료 잔수 (위 체크 시 무시됨)", min_value=0, step=1, value=1)
                
                st.divider()
                qty = st.number_input("초기 보유 수량 (낱개 기준)", min_value=0, step=1, value=0)
                remark = st.text_input("비고 항목")
                
                add_btn = st.form_submit_button("신규 마스터 등록")
                
                if add_btn:
                    final_ratio = 0 if is_calc_disabled else int(drink_ratio)
                    
                    if not code or not name:
                        st.error("품목코드와 품목명은 누락될 수 없습니다.")
                    elif str(code) in df_inv["품목코드"].astype(str).values:
                        st.error("동일한 품목코드가 이미 존재합니다.")
                    else:
                        new_row = pd.DataFrame([{
                            "품목코드": code, 
                            "품목명": name, 
                            "수량": int(qty), 
                            "비고": remark,
                            "박스당수량": int(box_qty),
                            "개당음료수": final_ratio
                        }])
                        df_inv = pd.concat([df_inv, new_row], ignore_index=True)
                        conn.update(worksheet="inventory", data=df_inv)
                        
                        ratio_log_text = "계산제외" if final_ratio == 0 else f"{final_ratio}잔"
                        new_log = pd.DataFrame([{
                            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "작업구분": "품목등록",
                            "품목명": name,
                            "내용": f"마스터 추가 -> 규격 [1박스={box_qty}개입 / 기준={ratio_log_text}] (초기보유: {qty}개)",
                            "작업자": "관리자"
                        }])
                        df_logs = pd.concat([df_logs, new_log], ignore_index=True)
                        conn.update(worksheet="logs", data=df_logs)
                        st.cache_data.clear()
                        st.success(f"새로운 물품 [{name}]의 마스터 규격이 성공적으로 등록되었습니다.")
                        st.rerun()

    # --- 서브탭 4: 수정 내역 로그 확인 ---
    with sub_tab4:
        st.subheader("📜 재고 수불 및 변경 이력 로그")
        if not df_logs.empty:
            st.dataframe(df_logs.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("기록된 변경 이력이 없습니다.")
