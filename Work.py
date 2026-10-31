import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import holidays
from datetime import datetime, date, timedelta
from io import BytesIO, StringIO
import csv
import uuid

import re

# ==========================================
# Interface localization (data and sheet column names remain unchanged)
# ==========================================
TRANSLATIONS = {
    "캘린더로 내보내기": "Export to Calendar",
    "현재 선택한 월의 근무 일정을 종일 일정으로 내보냅니다. 저장하기 전 근무 배정을 확인하세요.": "Export all-day shifts for the selected month. Confirm assignments before exporting.",
    "내보낼 근무자": "Staff member to export",
    "내보낼 일정:": "Events to export:",
    "Google 캘린더 (CSV)": "Google Calendar (CSV)",
    "삼성 캘린더 (ICS)": "Samsung Calendar (ICS)",
    "Apple 캘린더 (ICS)": "Apple Calendar (ICS)",
    "Google: 설정 > 가져오기 및 내보내기 > 가져오기에서 CSV 파일을 선택하세요. 삼성/Apple: ICS 파일을 캘린더 앱에서 열거나 가져오세요. 일정이 자동으로 동기화되지는 않습니다.": "Google: Import the CSV in Settings > Import & export. Samsung/Apple: Open or import the ICS file using your calendar app. Exports do not sync automatically.",
    "선택한 조건에 해당하는 근무 일정이 없습니다.": "No work shifts match the selected filters.",
    "통합 물류 관리 시스템": "Integrated Operations Management",
    "통합 관리 시스템": "Operations Management",
    "관리자 비밀번호": "Administrator password",
    "관리자 권한 활성화": "Administrator access enabled",
    "조회 전용 모드": "Read-only mode",
    "시트 데이터 다시 불러오기": "Reload spreadsheet data",
    "구글 시트 데이터를 다시 로드했습니다!": "Spreadsheet data reloaded!",
    "원하는 시스템을 선택하세요": "Choose a system",
    "근무 일정 관리": "Work Schedule",
    "재고 관리 시스템": "Inventory Management",
    "근무 현황 조회 및 배정": "View and Assign Shifts",
    "안티 요일 설정": "Unavailable Days",
    "근무자 명단 관리": "Staff Management",
    "화면 모드": "View mode",
    "달력 보기 (PC)": "Calendar (Desktop)",
    "리스트 보기 (모바일)": "List (Mobile)",
    "월 선택": "Select month",
    "근무자 필터링": "Filter staff",
    "전체보기": "All staff",
    "근무 일정 현황": "Work Schedule",
    "변경사항 구글 시트에 저장": "Save changes to Google Sheets",
    "모든 변경사항이 구글 시트에 안전하게 반영되었습니다!": "All changes saved to Google Sheets!",
    "근무 배정": "Shift assignment",
    "수동 안티 지정": "Manually mark unavailable",
    "배정 인원 없음": "No staff assigned",
    "월간 통계": "Monthly Summary",
    "내보내기": "Export",
    "Excel 다운로드": "Download Excel",
    "고정 안티 요일 설정": "Recurring unavailable days",
    "특정 근무자가 매주 반복해서 근무 불가능한 요일을 설정합니다. 설정된 요일은 근무 선택 목록에서 자동으로 제외됩니다.": "Set recurring weekdays when staff cannot work. These days will be excluded from assignment options.",
    "고정 불가능 요일 선택": "Select recurring unavailable weekdays",
    "고정 안티 요일 시트에 저장": "Save recurring unavailable days",
    "근무자 명단 및 색상 관리": "Staff and Color Management",
    "구글 시트의 `workers` 탭 데이터를 실시간 관리합니다. 이름/색상 수정 및 신규 추가, 삭제가 가능합니다.": "Manage staff names and colors from the `workers` sheet.",
    "기존 근무자 수정 및 삭제": "Edit or remove staff",
    "수정 또는 삭제할 근무자를 선택하세요": "Select staff member to edit or remove",
    "이름 변경": "Change name",
    "태그 색상 변경": "Change label color",
    "변경사항 저장": "Save changes",
    "해당 근무자 삭제": "Remove staff member",
    "현재 등록된 전체 명단 현황": "Current staff roster",
    "등록된 근무자가 없습니다. 아래에서 신규 근무자를 추가해 주세요.": "No staff registered. Add a staff member below.",
    "신규 근무자 추가": "Add staff member",
    "근무자 이름": "Staff name",
    "태그 배경 색상": "Label background color",
    "신규 근무자 추가 및 시트 저장": "Add staff and save to Sheets",
    "재고 관리 및 수불대장": "Inventory and Stock Movement",
    "실시간 현황 새로고침": "Refresh inventory",
    "최신 데이터를 성공적으로 동기화했습니다!": "Latest data synchronized!",
    "현재 재고 조회": "Current Inventory",
    "재고 입/출고": "Stock In / Out",
    "신규 품목 등록": "Register Item",
    "수정 내역 로그": "Activity Log",
    "실시간 물류 현황": "Current Stock Status",
    "품목명 검색": "Search item name",
    "재고 고갈 위험": "Critical stock",
    "재고 부족 주의": "Low stock warning",
    "조회할 재고 데이터가 없습니다.": "No inventory records found.",
    "총 취급 품목 종수": "Total item types",
    "재고 수량 변경 및 박스 계산기": "Update Stock and Box Calculator",
    "수정 권한이 없습니다. 사이드바에 올바른 관리자 비밀번호를 입력해 주세요.": "No editing permission. Enter the administrator password in the sidebar.",
    "등록된 품목이 없습니다. 신규 품목을 먼저 등록해 주세요.": "No items found. Register an item first.",
    "수정할 품목을 선택하세요": "Select item to update",
    "작업 선택": "Action",
    "입고 (+)": "Stock in (+)",
    "출고 (-)": "Stock out (-)",
    "입력 방식 선택": "Input method",
    "박스 개수로 계산해서 넣기": "Calculate using boxes",
    "낱개 개수로 직접 넣기": "Enter individual units",
    "입력할 박스 개수": "Number of boxes",
    "입력할 낱개 개수": "Number of units",
    "조정 사유": "Reason for adjustment",
    "정기 수량 조정": "Routine stock adjustment",
    "시트 데이터 반영": "Save to spreadsheet",
    "신규 품목 등록 및 마스터 규격 설정": "Register New Item and Specifications",
    "품목코드 (난독화 SKU 패턴 권장)": "Item code (unique SKU recommended)",
    "품목명": "Item name",
    "1박스당 들어있는 기본 낱개 개수": "Units per box",
    "컵, 빨대, 얼음 등 음료수 계산 제외 품목 설정": "Exclude item from drink estimates",
    "낱개 1개당 제조 가능한 음료 잔수 (위 체크 시 무시됨)": "Drinks per unit (ignored if excluded)",
    "초기 보유 수량 (낱개 기준)": "Initial quantity (units)",
    "비고 항목": "Notes",
    "신규 마스터 등록": "Register item",
    "재고 수불 및 변경 이력 로그": "Stock Movement and Change History",
    "기록된 변경 이력이 없습니다.": "No changes recorded.",
    "저장할 근무 데이터가 없거나 비어 있습니다. 덮어쓰기를 방지합니다.": "No schedule data to save. Overwrite prevented.",
    "저장할 안티 일정 데이터가 없거나 비어 있습니다.": "No unavailable-day data to save.",
    "저장할 고정 안티 요일 데이터가 비어 있어 구글 시트 반영을 중지합니다.": "Recurring unavailable-day data is empty; save cancelled.",
    "고정 안티 요일 설정이 성공적으로 저장되었습니다.": "Recurring unavailable days saved.",
    "이름은 공백일 수 없습니다.": "Name cannot be empty.",
    "이미 존재하는 근무자 이름입니다.": "This staff member already exists.",
    "올바른 근무자 이름을 입력해 주세요.": "Enter a valid staff name.",
    "구글 시트 저장 실패": "Google Sheets save failed",
    "구글 시트 삭제 처리 실패": "Google Sheets delete failed",
    "창고 재고가 부족합니다.": "Insufficient stock.",
    "입력된 수량이 없습니다.": "Enter a quantity.",
    "품목코드와 품목명은 누락될 수 없습니다.": "Item code and name are required.",
    "동일한 품목코드가 이미 존재합니다.": "This item code already exists.",
    "이름": "Name", "색상코드": "Color code", "날짜": "Date", "요일": "Weekday",
    "근무자": "Staff", "안티인원": "Unavailable staff", "비고": "Notes",
    "품목코드": "Item code", "수량": "Quantity", "보유 재고(박스 환산)": "Stock (boxes)",
    "제조 가능 음료수(추산)": "Estimated drinks", "작업구분": "Action",
    "내용": "Details", "작업자": "Operator", "일시": "Date/time",
    "근무:": "On shift:", "휴무:": "Unavailable:", "휴무": "Closed",
    "근무": "Shift", "안티": "Unavailable", "배정": "Assigned",
    "월": "Mon", "화": "Tue", "수": "Wed", "목": "Thu", "금": "Fri", "토": "Sat", "일": "Sun",
    "박스": "boxes", "개": "units", "잔": "drinks", "계산 제외품": "Excluded",
}

def T(value):
    """Translate display strings only; keep worksheet data and internal keys intact."""
    if st.session_state.get('ui_language', '한국어') != 'English':
        return value
    if not isinstance(value, str):
        return value
    for ko, en in sorted(TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        # Avoid replacing single-syllable Korean tokens inside unrelated words.
        if len(ko) == 1:
            value = en if value == ko else value
        else:
            value = value.replace(ko, en)
    return value

def T_list(values):
    return [T(value) for value in values]


# ==========================================
# Calendar exports: local all-day events (no shift hours in Sheet1)
# ==========================================
def ics_escape(value):
    return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')

def fold_ical_line(line):
    """Fold at 75 octets per RFC 5545, preserving UTF-8 code points."""
    folded, segment, length = [], '', 0
    for char in line:
        char_len = len(char.encode('utf-8'))
        if length + char_len > 75:
            folded.append(segment)
            segment, length = ' ' + char, 1 + char_len
        else:
            segment += char
            length += char_len
    folded.append(segment)
    return '\r\n'.join(folded)

def make_calendar_events(schedule, year, month, staff):
    events = []
    for dstr, assigned in sorted(schedule.items()):
        try:
            day = date.fromisoformat(str(dstr))
        except ValueError:
            continue
        if day.year != year or day.month != month:
            continue
        for worker in assigned:
            if staff == '전체보기' or worker == staff:
                events.append((day, worker))
    return events

def make_ics(events):
    stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Integrated Work Schedule//KO',
             'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Work Schedule']
    for day, worker in events:
        # Deterministic UID allows calendar clients to recognize re-imported events.
        uid = uuid.uuid5(uuid.NAMESPACE_URL, f'work-schedule:{worker}:{day.isoformat()}')
        lines.extend(['BEGIN:VEVENT', f'UID:{uid}@work-schedule.local', f'DTSTAMP:{stamp}',
                      f'DTSTART;VALUE=DATE:{day:%Y%m%d}',
                      f'DTEND;VALUE=DATE:{(day + timedelta(days=1)):%Y%m%d}',
                      f'SUMMARY:{ics_escape(worker + " 근무")}',
                      'DESCRIPTION:Exported from integrated work schedule',
                      'END:VEVENT'])
    lines.append('END:VCALENDAR')
    return ('\r\n'.join(fold_ical_line(line) for line in lines) + '\r\n').encode('utf-8')

def make_google_csv(events):
    buf = StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(['Subject', 'Start Date', 'End Date', 'All Day Event', 'Description'])
    for day, worker in events:
        writer.writerow([f'{worker} 근무', day.strftime('%m/%d/%Y'), day.strftime('%m/%d/%Y'),
                         'True', 'Exported from integrated work schedule'])
    return ('\ufeff' + buf.getvalue()).encode('utf-8')

# ==========================================
# 1. 페이지 설정 및 공통 CSS 디자인
# ==========================================
st.set_page_config(page_title="통합 물류 관리 시스템", layout="wide")

st.markdown(T("""
    <style>
    [data-testid="column"] {
        height: 310px !important; 
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
    .anti-tag {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        margin: 2px;
        color: #c92a2a;
        background-color: #ffe3e3;
        border: 1px solid #ffa8a8;
    }
    .fixed-anti-tag {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        margin: 2px;
        color: #d9480f;
        background-color: #fff4e6;
        border: 1px solid #ffd8a8;
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
    """), unsafe_allow_html=True)

# 2. 유틸리티 함수 (엑셀 변환)
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='데이터내보내기')
    return output.getvalue()

# ==========================================
# 3. 데이터베이스 연결 및 로드 (구글 시트 연동)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# --- [DB 함수 1] 근무자 목록 참조 (workers 탭) ---
def load_workers(ttl="3m"):
    default_workers = {
        "박성빈": "#FFD700", "오승현": "#FFB6C1", "우유리": "#98FB98", 
        "이지영": "#ADD8E6", "이혁": "#E6E6FA", "홍시현": "#FFCC99"
    }
    try:
        df = conn.read(worksheet="workers", ttl=ttl)
        if df is not None and not df.empty and 'name' in df.columns:
            workers = {}
            for _, row in df.iterrows():
                if pd.notna(row['name']):
                    color = row['color'] if ('color' in df.columns and pd.notna(row['color'])) else "#E6E6FA"
                    workers[str(row['name']).strip()] = str(color).strip()
            return workers if workers else default_workers
    except:
        pass
    return default_workers

# --- [DB 함수 2] 근무 일정 데이터 로드 (Sheet1 탭) ---
def load_schedule_data(ttl=0):
    db = {}
    try:
        df = conn.read(worksheet="Sheet1", ttl=ttl) 
        if df is not None and not df.empty and 'date' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row['date']) and pd.notna(row['workers']):
                    db[str(row['date'])] = [w.strip() for w in str(row['workers']).split(',') if w.strip()]
            return db
    except Exception as e:
        st.sidebar.error(T(f"⚠️ Sheet1 데이터 로드 실패: {e}"))
        if 'db' in st.session_state and st.session_state['db']:
            return st.session_state['db']
    return db

# --- [DB 함수 3] 날짜별 안티 일정 로드 (anti 탭) ---
def load_anti_data(ttl="3m"):
    anti_db = {}
    try:
        df = conn.read(worksheet="anti", ttl=ttl)
        if df is not None and not df.empty and 'date' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row['date']) and pd.notna(row['workers']):
                    anti_db[str(row['date'])] = [w.strip() for w in str(row['workers']).split(',') if w.strip()]
    except:
        pass
    return anti_db

# --- [DB 함수 4] 고정 안티 요일 데이터 로드 (anti_days 탭) ---
def load_anti_days_data(ttl="3m"):
    anti_days = {}
    try:
        df = conn.read(worksheet="anti_days", ttl=ttl)
        if df is not None and not df.empty and 'worker' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row['worker']) and pd.notna(row['days']):
                    days_list = [d.strip() for d in str(row['days']).split(',') if d.strip()]
                    anti_days[str(row['worker']).strip()] = days_list
    except:
        pass
    return anti_days

# --- [DB 함수 5] 재고 및 로그 데이터 로드 ---
def load_inventory_data(force_reload=False):
    if not force_reload and "df_inv_cached" in st.session_state and "df_logs_cached" in st.session_state:
        return st.session_state["df_inv_cached"], st.session_state["df_logs_cached"]
        
    df_inv = pd.DataFrame(columns=["품목코드", "품목명", "수량", "비고", "박스당수량", "개당음료수"])
    df_logs = pd.DataFrame(columns=["일시", "작업구분", "품목명", "내용", "작업자"])
    
    ttl_val = 0 if force_reload else "3m"
    try:
        df_inv = conn.read(worksheet="inventory", ttl=ttl_val)
        st.session_state["df_inv_cached"] = df_inv
    except:
        st.sidebar.error(T("⚠️ 구글 시트에서 'inventory' 탭을 찾을 수 없습니다."))
        
    try:
        df_logs = conn.read(worksheet="logs", ttl=ttl_val)
        st.session_state["df_logs_cached"] = df_logs
    except:
        st.sidebar.error(T("⚠️ 구글 시트에서 'logs' 탭을 찾을 수 없습니다."))
        
    return df_inv, df_logs

# 데이터 초기화 및 세션 등록
if 'worker_colors' not in st.session_state:
    st.session_state['worker_colors'] = load_workers()

if 'db' not in st.session_state:
    st.session_state['db'] = load_schedule_data()

if 'anti_db' not in st.session_state:
    st.session_state['anti_db'] = load_anti_data()

if 'anti_days_db' not in st.session_state:
    st.session_state['anti_days_db'] = load_anti_days_data()

WORKER_COLORS = st.session_state['worker_colors']
DAYS_MAP = ["월", "화", "수", "목", "금", "토", "일"]
kr_holidays = holidays.KR(language='ko')
today_val = date.today()
current_year = 2026

# ==========================================
# 4. 사이드바 메인 공통 제어 (권한, 동기화 및 메뉴)
# ==========================================
st.sidebar.selectbox(
    T("Language / 언어"), ["한국어", "English"],
    key="ui_language"
, format_func=T)
st.sidebar.title(T("⚙️ 통합 관리 시스템"))

admin_pw = st.secrets.get("ADMIN_PASSWORD", "1142")

password = st.sidebar.text_input(T("관리자 비밀번호"), type="password")
is_admin = (password == admin_pw)

if is_admin:
    st.sidebar.success(T("🔓 관리자 권한 활성화"))
else:
    st.sidebar.info(T("👁️ 조회 전용 모드"))

# --- 🔄 관리자 전용 데이터 다시 불러오기 버튼 ---
if is_admin:
    if st.sidebar.button(T("🔄 시트 데이터 다시 불러오기"), use_container_width=True):
        st.cache_data.clear()
        
        st.session_state['worker_colors'] = load_workers(ttl=0)
        st.session_state['db'] = load_schedule_data(ttl=0)
        st.session_state['anti_db'] = load_anti_data(ttl=0)
        st.session_state['anti_days_db'] = load_anti_days_data(ttl=0)
        load_inventory_data(force_reload=True)
        
        st.sidebar.success(T("구글 시트 데이터를 다시 로드했습니다!"))

st.sidebar.divider()
main_menu = st.sidebar.radio(T("원하는 시스템을 선택하세요"), ["📅 근무 일정 관리", "📦 재고 관리 시스템"], format_func=T)
st.sidebar.divider()

# ==========================================
# 메뉴 A: 📅 근무 일정 관리
# ==========================================
if main_menu == "📅 근무 일정 관리":
    tab_titles = ["📅 근무 현황 조회 및 배정"]
    if is_admin:
        tab_titles.extend(["🚫 안티 요일 설정", "👥 근무자 명단 관리"])
    
    tabs = st.tabs( T_list(tab_titles))

    # --- [안전장치 적용] 근무 일정 구글 시트 동기화 ---
    def sync_schedule_to_sheets():
        try:
            rows = [{"date": d, "workers": ",".join(ws)} for d, ws in st.session_state['db'].items() if ws]
            if not rows:
                st.warning(T("⚠️ 저장할 근무 데이터가 없거나 비어 있습니다. 덮어쓰기를 방지합니다."))
                return False
            df = pd.DataFrame(rows)
            conn.update(worksheet="Sheet1", data=df)
            return True
        except Exception as e:
            st.error(T(f"Sheet1 저장 중 오류가 발생했습니다: {e}"))
            return False

    # --- [안전장치 적용] 날짜별 안티 구글 시트 동기화 ---
    def sync_anti_to_sheets():
        try:
            rows = [{"date": d, "workers": ",".join(ws)} for d, ws in st.session_state['anti_db'].items() if ws]
            if not rows:
                st.warning(T("⚠️ 저장할 안티 일정 데이터가 없거나 비어 있습니다."))
                return True
            df = pd.DataFrame(rows)
            conn.update(worksheet="anti", data=df)
            return True
        except Exception as e:
            st.error(T(f"anti 탭 저장 중 오류가 발생했습니다: {e}"))
            return False

    # --- [안전장치 적용] 고정 안티 요일 동기화 ---
    def save_anti_days_to_sheets(anti_days_dict):
        try:
            rows = [{"worker": w, "days": ",".join(ds)} for w, ds in anti_days_dict.items() if ds]
            if not rows:
                st.warning(T("⚠️ 저장할 고정 안티 요일 데이터가 비어 있어 구글 시트 반영을 중지합니다."))
                return
            df = pd.DataFrame(rows)
            conn.update(worksheet="anti_days", data=df)
            st.session_state['anti_days_db'] = anti_days_dict
            st.cache_data.clear()
            st.success(T("고정 안티 요일 설정이 성공적으로 저장되었습니다."))
        except Exception as e:
            st.error(T(f"안티 요일 저장 오류. 시트에 'anti_days' 탭을 확인하세요. ({e})"))

    # ----------------------------------------------------
    # TAB 1: 📅 근무 현황 메인 달력 / 모바일 리스트
    # ----------------------------------------------------
    with tabs[0]:
        view_mode = st.sidebar.radio(T("화면 모드"), ["📅 달력 보기 (PC)", "📱 리스트 보기 (모바일)"], index=1, format_func=T)
        selected_month = st.sidebar.selectbox(T("월 선택"), list(range(1, 13)), index=today_val.month - 1, format_func=T)
        filter_name = st.sidebar.selectbox(T("🔍 근무자 필터링"), ["전체보기"] + list(WORKER_COLORS.keys()), format_func=T)

        first_day = date(current_year, selected_month, 1)
        last_day = (date(current_year, selected_month + 1, 1) if selected_month < 12 else date(current_year + 1, 1, 1)) - timedelta(days=1)
        start_pad = (first_day.weekday() + 1) % 7 

        col_cal, col_stat = st.columns([4, 1])

        with col_cal:
            col_hdr1, col_hdr2 = st.columns([3, 1])
            with col_hdr1:
                st.title((f"{selected_month} Monthly Work Schedule" if st.session_state.get("ui_language") == "English" else f"{selected_month}월 근무 일정 현황"))
            with col_hdr2:
                if is_admin:
                    st.write(T(""))
                    if st.button(T("💾 변경사항 구글 시트에 저장"), type="primary", use_container_width=True):
                        s1_ok = sync_schedule_to_sheets()
                        s2_ok = sync_anti_to_sheets()
                        if s1_ok and s2_ok:
                            st.cache_data.clear()
                            st.success(T("모든 변경사항이 구글 시트에 안전하게 반영되었습니다!"))

            if view_mode == "📱 리스트 보기 (모바일)":
                for d in range(1, last_day.day + 1):
                    t_date = date(current_year, selected_month, d)
                    d_str = t_date.strftime('%Y-%m-%d')
                    day_name = DAYS_MAP[t_date.weekday()]
                    
                    assigned = st.session_state['db'].get(d_str, [])
                    anti_assigned = st.session_state['anti_db'].get(d_str, [])
                    fixed_anti_workers = [w for w, days in st.session_state['anti_days_db'].items() if day_name in days]
                    all_anti = list(set(anti_assigned + fixed_anti_workers))
                    
                    is_match = (filter_name == "전체보기") or (filter_name in assigned) or (filter_name in all_anti)
                    is_today = (t_date == today_val)
                    is_off = (t_date in kr_holidays) or (t_date.weekday() in [0, 6])
                    
                    card_style = f"opacity: {'1.0' if is_match else '0.3'}; {'border:2px solid #fcc419; background-color:#fff9db;' if is_today else ''}"
                    today_badge = "<span class='today-badge'>TODAY</span>" if is_today else ""
                    
                    st.markdown(T(f"""
                        <div class='mobile-card' style='{card_style}'>
                            <div style='color:{"red" if is_off else "black"}; font-weight:bold; font-size:1.1rem;'>
                                {d}일 ({day_name}) {kr_holidays.get(t_date, "")} {today_badge}
                            </div>
                        </div>
                    """), unsafe_allow_html=True)
                    
                    if not is_off:
                        available_options = [w for w in WORKER_COLORS.keys() if w not in all_anti]
                        valid_assigned = [w for w in assigned if w in available_options]

                        if is_admin:
                            col_m1, col_m2 = st.columns(2)
                            with col_m1:
                                st.caption(T("🟢 근무 배정"))
                                new = st.multiselect(T(f"m_edit_{d}"), available_options, default=valid_assigned, key=f"m_{d_str}", label_visibility="collapsed", format_func=T)
                                if new != assigned:
                                    st.session_state['db'][d_str] = new
                            with col_m2:
                                st.caption(T("🚫 수동 안티 지정"))
                                new_anti = st.multiselect(T(f"m_anti_{d}"), list(WORKER_COLORS.keys()), default=anti_assigned, key=f"m_anti_{d_str}", label_visibility="collapsed", format_func=T)
                                if new_anti != anti_assigned:
                                    st.session_state['anti_db'][d_str] = new_anti
                                    # 안티 지정 시 기존 근무 배정 자동 정제
                                    updated_assigned = [w for w in st.session_state['db'].get(d_str, []) if w not in new_anti]
                                    st.session_state['db'][d_str] = updated_assigned
                        else:
                            if valid_assigned:
                                tags = "".join([f"<span class='worker-tag' style='background-color:{WORKER_COLORS.get(n, '#eee')}'>{n}</span>" for n in valid_assigned])
                                st.markdown(T(f"<div><b>근무:</b> {tags}</div>"), unsafe_allow_html=True)
                            else:
                                st.caption(T("배정 인원 없음"))
                    else:
                        st.caption(T("휴무"))
                    st.write(T(""))

            else: 
                header_cols = st.columns(7)
                for i, day in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
                    header_cols[i].markdown(T(f"<div style='text-align:center; font-weight:bold;'>{day}</div>"), unsafe_allow_html=True)

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
                                day_name = DAYS_MAP[t_date.weekday()]
                                
                                assigned = st.session_state['db'].get(t_str, [])
                                anti_assigned = st.session_state['anti_db'].get(t_str, [])
                                fixed_anti_workers = [w for w, days in st.session_state['anti_days_db'].items() if day_name in days]
                                all_anti = list(set(anti_assigned + fixed_anti_workers))
                                
                                is_today = (t_date == today_val)
                                is_off = (t_date in kr_holidays) or (t_date.weekday() in [0, 6])
                                is_match = (filter_name == "전체보기") or (filter_name in assigned) or (filter_name in all_anti)

                                box_class = "today-box" if is_today else ""
                                dim_style = f"opacity: {'1.0' if is_match else '0.3'};"
                                
                                st.markdown(T(f"<div class='date-header {box_class}' style='{dim_style} color: {'red' if is_off else 'black'};'>{day_counter}</div>"), unsafe_allow_html=True)
                                
                                if not is_off:
                                    available_options = [w for w in WORKER_COLORS.keys() if w not in all_anti]
                                    valid_assigned = [w for w in assigned if w in available_options]

                                    if is_admin:
                                        st.caption(T("🟢 근무"))
                                        new = st.multiselect(T(f"p_edit_{day_counter}"), available_options, default=valid_assigned, key=f"p_{t_str}", label_visibility="collapsed", format_func=T)
                                        if new != assigned:
                                            st.session_state['db'][t_str] = new

                                        st.caption(T("🚫 안티"))
                                        new_anti = st.multiselect(T(f"p_anti_{day_counter}"), list(WORKER_COLORS.keys()), default=anti_assigned, key=f"p_anti_{t_str}", label_visibility="collapsed", format_func=T)
                                        if new_anti != anti_assigned:
                                            st.session_state['anti_db'][t_str] = new_anti
                                            updated_assigned = [w for w in st.session_state['db'].get(t_str, []) if w not in new_anti]
                                            st.session_state['db'][t_str] = updated_assigned
                                    else:
                                        for n in valid_assigned:
                                            st.markdown(T(f"<span class='worker-tag' style='background-color:{WORKER_COLORS.get(n, '#eee')}'>{n}</span>"), unsafe_allow_html=True)

                                day_counter += 1

        with col_stat:
            st.subheader(T("📊 월간 통계"))
            export_data = []
            month_workers = []
            month_antis = []
            
            for d in range(1, last_day.day + 1):
                d_date = date(current_year, selected_month, d)
                d_str = d_date.strftime('%Y-%m-%d')
                day_name = DAYS_MAP[d_date.weekday()]
                
                assigned = st.session_state['db'].get(d_str, [])
                anti_assigned = st.session_state['anti_db'].get(d_str, [])
                fixed_anti_workers = [w for w, days in st.session_state['anti_days_db'].items() if day_name in days]
                all_anti = list(set(anti_assigned + fixed_anti_workers))
                
                month_workers.extend(assigned)
                month_antis.extend(all_anti)
                
                row_data = {
                    "날짜": d_str, 
                    "요일": day_name, 
                    "근무자": ", ".join(assigned), 
                    "비고": kr_holidays.get(d_date, "")
                }
                if is_admin:
                    row_data["안티인원"] = ", ".join(all_anti)
                export_data.append(row_data)
            
            for name, color in WORKER_COLORS.items():
                if filter_name != "전체보기" and name != filter_name: continue
                count = month_workers.count(name)
                anti_count = month_antis.count(name)
                anti_stat_text = f" | 🚫 휴무: {anti_count}회" if is_admin else ""
                st.markdown(T(f"""
                    <div style='background-color:{color}; padding:8px; border-radius:5px; margin-bottom:5px; color:black;'>
                        <b>{name}</b><br>
                        <small>🟢 근무: {count}회{anti_stat_text}</small>
                    </div>
                """), unsafe_allow_html=True)
            
            st.divider()
            st.subheader(T("💾 내보내기"))
            if export_data:
                excel_data = to_excel(pd.DataFrame(export_data))
                st.download_button(
                    label=T("📊 Excel 다운로드"), 
                    data=excel_data, 
                    file_name=f"근무및안티표_{selected_month}월.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.divider()
            st.subheader(T("📅 캘린더로 내보내기 / Calendar export"))
            st.caption(T("현재 선택한 월의 근무 일정을 종일 일정으로 내보냅니다. 저장하기 전 근무 배정을 확인하세요."))
            export_worker = st.selectbox(
                T("내보낼 근무자"), ["전체보기"] + list(WORKER_COLORS.keys()),
                index=0 if filter_name == "전체보기" else list(WORKER_COLORS.keys()).index(filter_name) + 1,
                format_func=T, key="calendar_export_worker")
            calendar_events = make_calendar_events(
                st.session_state['db'], current_year, selected_month, export_worker)
            st.caption((f"Events to export: {len(calendar_events)}" if st.session_state.get("ui_language") == "English" else f"내보낼 일정: {len(calendar_events)}개"))
            if calendar_events:
                google_csv = make_google_csv(calendar_events)
                standard_ics = make_ics(calendar_events)
                col_g, col_s, col_a = st.columns(3)
                with col_g:
                    st.download_button(
                        T("Google 캘린더 (CSV)"), data=google_csv,
                        file_name=f"work_schedule_google_{current_year}_{selected_month:02d}.csv",
                        mime="text/csv", use_container_width=True)
                with col_s:
                    st.download_button(
                        T("삼성 캘린더 (ICS)"), data=standard_ics,
                        file_name=f"work_schedule_samsung_{current_year}_{selected_month:02d}.ics",
                        mime="text/calendar", use_container_width=True)
                with col_a:
                    st.download_button(
                        T("Apple 캘린더 (ICS)"), data=standard_ics,
                        file_name=f"work_schedule_apple_{current_year}_{selected_month:02d}.ics",
                        mime="text/calendar", use_container_width=True)
                st.caption(T("Google: 설정 > 가져오기 및 내보내기 > 가져오기에서 CSV 파일을 선택하세요. 삼성/Apple: ICS 파일을 캘린더 앱에서 열거나 가져오세요. 일정이 자동으로 동기화되지는 않습니다."))
            else:
                st.info(T("선택한 조건에 해당하는 근무 일정이 없습니다."))

    # ----------------------------------------------------
    # TAB 2: 🚫 관리자 전용 - 고정 안티 요일 설정
    # ----------------------------------------------------
    if is_admin:
        with tabs[1]:
            st.title(T("🚫 근무자별 고정 안티 요일 설정"))
            st.info(T("특정 근무자가 매주 반복해서 근무 불가능한 요일을 설정합니다. 설정된 요일은 근무 선택 목록에서 자동으로 제외됩니다."))
            
            current_anti_days = st.session_state['anti_days_db'].copy()
            updated_anti_days = {}

            with st.form("anti_days_form"):
                for worker in WORKER_COLORS.keys():
                    st.subheader(T(f"👤 {worker}"))
                    default_days = current_anti_days.get(worker, [])
                    
                    selected = st.multiselect(
                        T(f"{worker}님의 고정 불가능 요일 선택"),
                        options=["화", "수", "목", "금", "토"],
                        default=[d for d in default_days if d in ["화", "수", "목", "금", "토"]],
                        key=f"anti_day_select_{worker}"
                    , format_func=T)
                    if selected:
                        updated_anti_days[worker] = selected
                    st.divider()

                submit_anti_days = st.form_submit_button(T("💾 고정 안티 요일 시트에 저장"))
                if submit_anti_days:
                    save_anti_days_to_sheets(updated_anti_days)
                    st.rerun()

        # ----------------------------------------------------
        # TAB 3: 👥 관리자 전용 - 근무자 명단 및 색상 관리
        # ----------------------------------------------------
        with tabs[2]:
            st.title(T("👥 근무자 명단 및 색상 관리 (`workers` 탭 연동)"))
            st.info(T("구글 시트의 `workers` 탭 데이터를 실시간 관리합니다. 이름/색상 수정 및 신규 추가, 삭제가 가능합니다."))
            
            # 1. 기존 근무자 정보 수정 및 삭제
            st.subheader(T("✏️ 기존 근무자 수정 및 삭제"))
            
            if WORKER_COLORS:
                selected_worker = st.selectbox(T("수정 또는 삭제할 근무자를 선택하세요"), list(WORKER_COLORS.keys()), format_func=T)
                
                if selected_worker:
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        edit_name = st.text_input(T("이름 변경"), value=selected_worker, key=f"edit_name_{selected_worker}")
                    with col_e2:
                        edit_color = st.color_picker(T("태그 색상 변경"), value=WORKER_COLORS[selected_worker], key=f"edit_color_{selected_worker}")
                    
                    btn_col1, btn_col2 = st.columns(2)
                    
                    # [수정 저장]
                    with btn_col1:
                        if st.button(T("💾 변경사항 저장"), use_container_width=True):
                            new_name_clean = edit_name.strip()
                            if not new_name_clean:
                                st.error(T("이름은 공백일 수 없습니다."))
                            else:
                                new_worker_colors = {}
                                for k, v in WORKER_COLORS.items():
                                    if k == selected_worker:
                                        new_worker_colors[new_name_clean] = edit_color
                                    else:
                                        new_worker_colors[k] = v
                                
                                rows = [{"name": k, "color": v} for k, v in new_worker_colors.items()]
                                # 안전장치: 빈 데이터 덮어쓰기 방지
                                if not rows:
                                    st.error(T("⚠️ 저장할 근무자 목록이 비어있어 저장 작업을 중단합니다."))
                                else:
                                    try:
                                        conn.update(worksheet="workers", data=pd.DataFrame(rows))
                                        st.session_state['worker_colors'] = new_worker_colors
                                        st.cache_data.clear()
                                        st.success(T(f"[{new_name_clean}] 님의 정보가 수정되었습니다."))
                                        st.rerun()
                                    except Exception as e:
                                        st.error(T(f"구글 시트 저장 실패: {e}"))
                                    
                    # [근무자 삭제]
                    with btn_col2:
                        if st.button(T("🗑️ 해당 근무자 삭제"), type="primary", use_container_width=True):
                            new_worker_colors = {k: v for k, v in WORKER_COLORS.items() if k != selected_worker}
                            rows = [{"name": k, "color": v} for k, v in new_worker_colors.items()]
                            # 안전장치: 전체 삭제로 빈 DataFrame 저장되는 현상 방지
                            if not rows:
                                st.error(T("⚠️ 전체 삭제로 인해 명단이 완전히 비게 됩니다. 안전을 위해 1명 이상의 명단을 유지해야 합니다."))
                            else:
                                try:
                                    conn.update(worksheet="workers", data=pd.DataFrame(rows))
                                    st.session_state['worker_colors'] = new_worker_colors
                                    st.cache_data.clear()
                                    st.success(T(f"[{selected_worker}] 님이 명단에서 삭제되었습니다."))
                                    st.rerun()
                                except Exception as e:
                                    st.error(T(f"구글 시트 삭제 처리 실패: {e}"))

                st.divider()
                st.caption(T("📋 현재 등록된 전체 명단 현황"))
                df_workers_list = pd.DataFrame([{"이름": k, "색상코드": v} for k, v in WORKER_COLORS.items()])
                st.dataframe(df_workers_list, use_container_width=True, hide_index=True)
            else:
                st.warning(T("등록된 근무자가 없습니다. 아래에서 신규 근무자를 추가해 주세요."))
                
            st.divider()
            
            # 2. 신규 근무자 간편 추가
            with st.form("add_worker_form", clear_on_submit=True):
                st.subheader(T("➕ 신규 근무자 추가"))
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    new_w_name = st.text_input(T("근무자 이름"))
                with col_w2:
                    new_w_color = st.color_picker(T("태그 배경 색상"), "#E6E6FA")
                
                add_w_btn = st.form_submit_button(T("신규 근무자 추가 및 시트 저장"))
                if add_w_btn:
                    clean_name = new_w_name.strip() if new_w_name else ""
                    if clean_name and clean_name not in WORKER_COLORS:
                        WORKER_COLORS[clean_name] = new_w_color
                        rows = [{"name": k, "color": v} for k, v in WORKER_COLORS.items()]
                        if not rows:
                            st.error(T("⚠️ 저장할 데이터가 비어있습니다."))
                        else:
                            try:
                                conn.update(worksheet="workers", data=pd.DataFrame(rows))
                                st.session_state['worker_colors'] = WORKER_COLORS
                                st.cache_data.clear()
                                st.success(T(f"새 근무자 [{clean_name}] 님이 추가되었습니다."))
                                st.rerun()
                            except Exception as e:
                                st.error(T(f"구글 시트 'workers' 탭 업데이트 실패: {e}"))
                    elif clean_name in WORKER_COLORS:
                        st.warning(T("이미 존재하는 근무자 이름입니다."))
                    else:
                        st.warning(T("올바른 근무자 이름을 입력해 주세요."))

# ==========================================
# 메뉴 B: 📦 재고 관리 시스템
# ==========================================
elif main_menu == "📦 재고 관리 시스템":
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.title(T("📦 재고 관리 및 수불대장"))
    with col_refresh:
        st.write(T("")) 
        if st.button(T("🔄 실시간 현황 새로고침"), use_container_width=True):
            st.cache_data.clear()
            load_inventory_data(force_reload=True)
            st.toast(T("최신 데이터를 성공적으로 동기화했습니다!"))
    
    df_inv, df_logs = load_inventory_data()
    
    for col in ["수량", "박스당수량", "개당음료수"]:
        if col in df_inv.columns:
            df_inv[col] = pd.to_numeric(df_inv[col], errors='coerce').fillna(0).astype(int)
        else:
            df_inv[col] = 0
            
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs( T_list(["🔍 현재 재고 조회", "🔄 재고 입/출고", "➕ 신규 품목 등록", "📜 수정 내역 로그"]))
    
    with sub_tab1:
        st.subheader(T("🔍 실시간 물류 현황"))
        search_keyword = st.text_input(T("품목명 검색"), key="inv_search")
        
        filtered_df = df_inv[df_inv["품목명"].str.contains(search_keyword, na=False)] if search_keyword else df_inv
        display_df = filtered_df.copy()
        
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
            
            low_stock_items = display_df[display_df["_raw_drinks"] <= 10]["품목명"].tolist()
            warning_stock_items = display_df[(display_df["_raw_drinks"] > 10) & (display_df["_raw_drinks"] <= 30)]["품목명"].tolist()
            
            if low_stock_items:
                st.error(T(f"🚨 **재고 고갈 위험 (10잔 이하):** {', '.join(low_stock_items)} -> 빠른 발주 필요!"))
            elif warning_stock_items:
                st.warning(T(f"⚠️ **재고 부족 주의 (30잔 이하):** {', '.join(warning_stock_items)}"))

            cols_to_show = ["품목코드", "품목명", "수량", "보유 재고(박스 환산)", "제조 가능 음료수(추산)", "비고"]
            existing_cols = [c for c in cols_to_show if c in display_df.columns]
            
            def style_by_index(row):
                idx = row.name
                raw_drinks_val = display_df.loc[idx, "_raw_drinks"]
                if raw_drinks_val <= 10:
                    return ['background-color: #ffdde1; color: #c92a2a; font-weight: bold;'] * len(row)
                elif raw_drinks_val <= 30:
                    return ['background-color: #fff3bf; color: #e67e22;'] * len(row)
                return [''] * len(row)

            final_view_df = display_df[existing_cols]
            styled_df = final_view_df.style.apply(style_by_index, axis=1)
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info(T("조회할 재고 데이터가 없습니다."))
            
        st.divider()
        st.metric(label=T("총 취급 품목 종수"), value=len(df_inv))

    with sub_tab2:
        st.subheader(T("🔄 재고 수량 변경 및 박스 계산기"))
        if not is_admin:
            st.warning(T("🔒 수정 권한이 없습니다. 사이드바에 올바른 관리자 비밀번호를 입력해 주세요."))
        elif df_inv.empty:
            st.info(T("등록된 품목이 없습니다. 신규 품목을 먼저 등록해 주세요."))
        else:
            item_list = df_inv["품목명"].tolist()
            selected_item = st.selectbox(T("수정할 품목을 선택하세요"), item_list, format_func=T)
            
            item_row = df_inv[df_inv["품목명"] == selected_item].iloc[0]
            
            p_box_qty = int(item_row["박스당수량"]) if pd.notna(item_row["박스당수량"]) else 1
            p_drink_ratio = int(item_row["개당음료수"]) if pd.notna(item_row["개당음료수"]) else 0
            current_qty = int(item_row["수량"]) if pd.notna(item_row["수량"]) else 0
            
            ratio_info = f"{p_drink_ratio}잔 제조 가능" if p_drink_ratio > 0 else "❌ 계산 제외 품목"
            st.info(T(f"💡 현재 보유 낱개: {current_qty}개 | [📦 1박스 = {p_box_qty}개입] | [🥤 기준: {ratio_info}]"))
            
            with st.form("inv_update_form"):
                action = st.radio(T("작업 선택"), ["입고 (+)", "출고 (-)"], format_func=T)
                input_mode = st.radio(T("입력 방식 선택"), ["📦 박스 개수로 계산해서 넣기", "✏️ 낱개 개수로 직접 넣기"], format_func=T)
                
                col_calc1, col_calc2 = st.columns(2)
                with col_calc1:
                    box_input = st.number_input(T("입력할 박스 개수"), min_value=0, step=1, value=0)
                with col_calc2:
                    each_input = st.number_input(T("입력할 낱개 개수"), min_value=0, step=1, value=0)
                
                reason = st.text_input(T("조정 사유"), value="정기 수량 조정")
                submit_btn = st.form_submit_button(T("시트 데이터 반영"))
                
                if submit_btn:
                    idx = df_inv[df_inv["품목명"] == selected_item].index[0]
                    
                    if input_mode == "📦 박스 개수로 계산해서 넣기":
                        if p_box_qty <= 0:
                            st.error(T("해당 품목의 마스터 박스당 수량 설정이 올바르지 않습니다."))
                            st.stop()
                        quantity_change = box_input * p_box_qty
                        detail_text = f"{box_input}박스(총 {quantity_change}개)"
                    else:
                        quantity_change = each_input
                        detail_text = f"{each_input}개(낱개)"
                        
                    if quantity_change <= 0:
                        st.error(T("입력된 수량이 없습니다."))
                        st.stop()
                        
                    if action == "입고 (+)":
                        new_qty = current_qty + quantity_change
                        log_msg = f"입고: {detail_text} | 사유: {reason}"
                        st.success(T(f"{selected_item} 상품이 {detail_text}만큼 입고 완료되었습니다."))
                    elif action == "출고 (-)":
                        if current_qty < quantity_change:
                            st.error(T("창고 재고가 부족합니다."))
                            st.stop()
                        new_qty = current_qty - quantity_change
                        log_msg = f"출고: {detail_text} | 사유: {reason}"
                        st.success(T(f"{selected_item} 상품이 {detail_text}만큼 출고 완료되었습니다."))
                    
                    df_inv.at[idx, "수량"] = new_qty
                    
                    # 안전장치: 재고 데이터 덮어쓰기 방지
                    if not df_inv.empty:
                        conn.update(worksheet="inventory", data=df_inv)
                        st.session_state["df_inv_cached"] = df_inv
                    
                    new_log = pd.DataFrame([{
                        "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "작업구분": action,
                        "품목명": selected_item,
                        "내용": log_msg,
                        "작업자": "관리자"
                    }])
                    df_logs = pd.concat([df_logs, new_log], ignore_index=True)
                    
                    # 안전장치: 로그 데이터 덮어쓰기 방지
                    if not df_logs.empty:
                        conn.update(worksheet="logs", data=df_logs)
                        st.session_state["df_logs_cached"] = df_logs
                    
                    st.cache_data.clear()
                    st.rerun()

    with sub_tab3:
        st.subheader(T("➕ 신규 품목 등록 및 마스터 규격 설정"))
        if not is_admin:
            st.warning(T("🔒 수정 권한이 없습니다. 사이드바에 올바른 관리자 비밀번호를 입력해 주세요."))
        else:
            with st.form("inv_insert_form", clear_on_submit=True):
                code = st.text_input(T("품목코드 (난독화 SKU 패턴 권장)"))
                name = st.text_input(T("품목명"))
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    box_qty = st.number_input(T("📦 1박스당 들어있는 기본 낱개 개수"), min_value=1, step=1, value=1)
                with col_m2:
                    is_calc_disabled = st.checkbox(T("컵, 빨대, 얼음 등 음료수 계산 제외 품목 설정"))
                    drink_ratio = st.number_input(T("🥤 낱개 1개당 제조 가능한 음료 잔수 (위 체크 시 무시됨)"), min_value=0, step=1, value=1)
                
                st.divider()
                qty = st.number_input(T("초기 보유 수량 (낱개 기준)"), min_value=0, step=1, value=0)
                remark = st.text_input(T("비고 항목"))
                
                add_btn = st.form_submit_button(T("신규 마스터 등록"))
                
                if add_btn:
                    final_ratio = 0 if is_calc_disabled else int(drink_ratio)
                    
                    if not code or not name:
                        st.error(T("품목코드와 품목명은 누락될 수 없습니다."))
                    elif str(code) in df_inv["품목코드"].astype(str).values:
                        st.error(T("동일한 품목코드가 이미 존재합니다."))
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
                        
                        # 안전장치: 재고 데이터 덮어쓰기 방지
                        if not df_inv.empty:
                            conn.update(worksheet="inventory", data=df_inv)
                            st.session_state["df_inv_cached"] = df_inv
                        
                        ratio_log_text = "계산제외" if final_ratio == 0 else f"{final_ratio}잔"
                        new_log = pd.DataFrame([{
                            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "작업구분": "품목등록",
                            "품목명": name,
                            "내용": f"마스터 추가 -> 규격 [1박스={box_qty}개입 / 기준={ratio_log_text}] (초기보유: {qty}개)",
                            "작업자": "관리자"
                        }])
                        df_logs = pd.concat([df_logs, new_log], ignore_index=True)
                        
                        # 안전장치: 로그 데이터 덮어쓰기 방지
                        if not df_logs.empty:
                            conn.update(worksheet="logs", data=df_logs)
                            st.session_state["df_logs_cached"] = df_logs
                        
                        st.cache_data.clear()
                        st.success(T(f"새로운 물품 [{name}]의 마스터 규격이 성공적으로 등록되었습니다."))
                        st.rerun()

    with sub_tab4:
        st.subheader(T("📜 재고 수불 및 변경 이력 로그"))
        if not df_logs.empty:
            st.dataframe(df_logs.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info(T("기록된 변경 이력이 없습니다."))

st.markdown(T("---"))
st.markdown(
    T("""
    <div style='
        text-align: center; 
        padding: 10px; 
        background-color: #f8f9fa; 
        border: 1px solid #e9ecef; 
        border-radius: 6px; 
        color: #868e96; 
        font-size: 0.8rem;
        margin-top: 20px;
    '>
        <p style='margin: 0;'>© 2026 Integrated Logistics Management System | Developed for Team Efficiency</p>
        <p style='margin: 0; font-size: 0.75rem; color: #adb5bd;'>Version 2.4.1 • All rights reserved</p>
        <p style='margin: 0; font-size: 0.75rem; color: #adb5bd;'>Made with Gemini 3.6 flash / GPT 6.0 </p>
    </div>
    """),
    unsafe_allow_html=True,
)
