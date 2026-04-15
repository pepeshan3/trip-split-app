import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime, timedelta, timezone

# --- 全域設定 ---
# 設定時區與幣別
TW_TIMEZONE = timezone(timedelta(hours=8))
CURRENCIES = ['TWD', 'JPY', 'USD', 'EUR', 'KRW']
INT_CURRENCIES = ['TWD', 'JPY', 'KRW', 'VND']

# 檔案路徑
DATA_FILE = 'trip_ledger.csv'      # 存帳務資料
CONFIG_FILE = 'members.json'       # 存成員名單
HISTORY_DIR = 'history'            # 歷史封存資料夾

# --- 基礎函數 ---
def load_members():
    """讀取成員名單"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_members(members_list):
    """儲存成員名單"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(members_list, f, ensure_ascii=False)

def get_ledger():
    """讀取帳本並清洗髒資料"""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # 強制清洗掉所有 Unnamed 或空白欄位
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            return df
        except:
            return pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries'])
    return pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries'])

def save_ledger(df):
    """儲存帳本"""
    # 存檔前再次確保欄位乾淨
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(DATA_FILE, index=False)

def smart_fmt(val):
    """聰明數字格式化：整數不顯示小數點"""
    try:
        f_val = float(val)
        return f"{f_val:,.0f}" if f_val.is_integer() else f"{f_val:,.2f}"
    except:
        return str(val)

# --- 頁面初始化 ---
st.set_page_config(page_title="旅程分帳助手 Pro", layout="centered", page_icon="💸")

if 'members' not in st.session_state:
    st.session_state.members = load_members()

# --- CSS 樣式增強 ---
st.markdown("""
<style>
    /* 側邊欄風格 */
    [data-testid="stSidebar"] { background-color: #1E293B; }
    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    
    /* 成員膠囊標籤 */
    .member-capsule {
        display: inline-block; background-color: rgba(255, 255, 255, 0.1);
        color: #F8FAFC; padding: 4px 12px; border-radius: 20px;
        margin: 4px 2px; font-size: 0.85rem; border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* 質感卡片 */
    .premium-card {
        background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* 轉帳票據風格 */
    .transfer-ticket {
        display: flex; align-items: center; justify-content: space-between;
        background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 10px;
        padding: 12px; margin-bottom: 8px;
    }
    .ticket-name { font-weight: 700; color: #1E293B; }
    .ticket-amount { font-weight: 800; color: #2563EB; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄：成員與設定 ---
with st.sidebar:
    st.title("👥 成員管理")
    
    # 顯示目前成員
    if st.session_state.members:
        m_html = "".join([f"<span class='member-capsule'>{m}</span>" for m in st.session_state.members])
        st.markdown(f"<div>{m_html}</div><br>", unsafe_allow_html=True)
    
    # 新增成員
    with st.container():
        new_name = st.text_input("快速新增成員", placeholder="輸入姓名...", label_visibility="collapsed")
        if st.button("➕ 新增成員", use_container_width=True):
            if new_name and new_name not in st.session_state.members:
                st.session_state.members.append(new_name)
                save_members(st.session_state.members)
                st.rerun()
            elif new_name in st.session_state.members:
                st.toast("此成員已在名單中", icon="⚠️")

    st.markdown("---")
    
    # 進階操作
    with st.expander("⚙️ 進階功能"):
        if st.session_state.members:
            edit_target = st.selectbox("選擇成員", st.session_state.members)
            new_target_name = st.text_input("修改名稱為")
            if st.button("確認修改"):
                if new_target_name:
                    st.session_state.members = [new_target_name if x == edit_target else x for x in st.session_state.members]
                    save_members(st.session_state.members)
                    # 同時更新帳本中的名字
                    df_up = get_ledger()
                    df_up['Payer'] = df_up['Payer'].replace(edit_target, new_target_name)
                    df_up['Beneficiaries'] = df_up['Beneficiaries'].apply(lambda x: x.replace(edit_target, new_target_name) if isinstance(x, str) else x)
                    save_ledger(df_up)
                    st.rerun()
            
            if st.button("🗑️ 移除此成員", type="secondary"):
                st.session_state.members.remove(edit_target)
                save_members(st.session_state.members)
                st.rerun()
        
        st.divider()
        if st.button("🔒 封存目前帳本並開新局"):
            if not os.path.exists(HISTORY_DIR): os.makedirs(HISTORY_DIR)
            ts = datetime.now(TW_TIMEZONE).strftime('%Y%m%d_%H%M%S')
            old_df = get_ledger()
            old_df.to_csv(f"{HISTORY_DIR}/ledger_{ts}.csv", index=False)
            save_ledger(pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries']))
            st.success("已封存歷史紀錄！")
            time.sleep(1)
            st.rerun()

# --- 主畫面邏輯 ---
if not st.session_state.members:
    st.info("👈 請先在側邊欄新增至少兩位夥伴，開啟旅程記帳！")
    st.stop()

df = get_ledger()

# --- 彈出視窗：新增/編輯 ---
@st.dialog("➕ 新增帳務")
def add_entry_ui(is_repayment=False):
    if not is_repayment:
        st.subheader("💸 新增支出")
        with st.form("expense_form", clear_on_submit=True):
            item = st.text_input("消費項目", placeholder="例如：居酒屋、環球影城門票")
            col1, col2 = st.columns(2)
            amount = col1.number_input("金額", min_value=0.0, step=100.0)
            curr = col2.selectbox("幣別", CURRENCIES)
            payer = st.selectbox("誰先墊錢？", st.session_state.members)
            bens = st.multiselect("分給誰？", st.session_state.members, default=st.session_state.members)
            
            if st.form_submit_button("確認儲存", type="primary"):
                if item and amount > 0 and bens:
                    new_row = {
                        'Date': datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d %H:%M'),
                        'Item': item, 'Payer': payer, 'Amount': amount, 
                        'Currency': curr, 'Beneficiaries': ",".join(bens)
                    }
                    save_ledger(pd.concat([get_ledger(), pd.DataFrame([new_row])], ignore_index=True))
                    st.success("已記錄消費！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("請填寫完整資訊")
    else:
        st.subheader("🤝 登記還款")
        with st.form("repay_form"):
            p1 = st.selectbox("誰還錢？ (付款者)", st.session_state.members)
            p2 = st.selectbox("還給誰？ (收款者)", st.session_state.members)
            col1, col2 = st.columns(2)
            amt = col1.number_input("還款金額", min_value=0.0)
            curr = col2.selectbox("幣別", CURRENCIES)
            if st.form_submit_button("確認還款"):
                if amt > 0 and p1 != p2:
                    new_row = {
                        'Date': datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d %H:%M'),
                        'Item': f"還款: {p1} ➜ {p2}", 'Payer': p1, 'Amount': amt, 
                        'Currency': curr, 'Beneficiaries': p2
                    }
                    save_ledger(pd.concat([get_ledger(), pd.DataFrame([new_row])], ignore_index=True))
                    st.rerun()

@st.dialog("✏️ 編輯帳務")
def edit_entry_ui(idx, row):
    with st.form("edit_form"):
        item = st.text_input("項目", value=row['Item'])
        amount = st.number_input("金額", value=float(row['Amount']))
        curr = st.selectbox("幣別", CURRENCIES, index=CURRENCIES.index(row['Currency']) if row['Currency'] in CURRENCIES else 0)
        payer = st.selectbox("付款人", st.session_state.members, index=st.session_state.members.index(row['Payer']) if row['Payer'] in st.session_state.members else 0)
        current_bens = str(row['Beneficiaries']).split(",")
        bens = st.multiselect("分帳人", st.session_state.members, default=[m for m in current_bens if m in st.session_state.members])
        
        if st.form_submit_button("更新資料"):
            ledger = get_ledger()
            ledger.loc[idx, ['Item', 'Amount', 'Currency', 'Payer', 'Beneficiaries']] = [item, amount, curr, payer, ",".join(bens)]
            save_ledger(ledger)
            st.rerun()
    
    if st.button("🗑️ 刪除此筆資料", type="secondary"):
        save_ledger(get_ledger().drop(idx))
        st.rerun()

# --- 主頁面佈局 ---
st.title("✈️ 旅程分帳系統")
st.markdown(f"**{len(st.session_state.members)}** 位夥伴 | **{len(df)}** 筆紀錄")

# 功能按鈕區
c_btn1, c_btn2 = st.columns(2)
if c_btn1.button("💸 新增消費", use_container_width=True, type="primary"):
    add_entry_ui(False)
if c_btn2.button("🤝 登記還款", use_container_width=True):
    add_entry_ui(True)

st.divider()

# --- 結算儀表板 ---
if not df.empty:
    st.subheader("🧾 結算概況")
    currencies_in_df = df['Currency'].unique()
    tabs = st.tabs([f"💵 {c}" for c in currencies_in_df])
    
    for i, curr in enumerate(currencies_in_df):
        with tabs[i]:
            curr_df = df[df['Currency'] == curr]
            balances = {m: 0.0 for m in st.session_state.members}
            
            for _, row in curr_df.iterrows():
                amt = float(row['Amount'])
                payer = row['Payer']
                bens = str(row['Beneficiaries']).split(",")
                
                if "還款" not in row['Item']:
                    if payer in balances: balances[payer] += amt
                    share = amt / len(bens)
                    for b in bens:
                        if b.strip() in balances: balances[b.strip()] -= share
                else:
                    # 還款邏輯：付款者平衡增加，收款者平衡減少
                    if payer in balances: balances[payer] += amt
                    if bens[0].strip() in balances: balances[bens[0].strip()] -= amt

            # 顯示收支表
            col_l, col_r = st.columns([1, 1])
            with col_l:
                st.markdown("**個人淨額狀態**")
                for m, bal in balances.items():
                    color = "#16A34A" if bal >= 0 else "#DC2626"
                    symbol = "+" if bal >= 0 else ""
                    st.markdown(f"{m}: <span style='color:{color}; font-weight:bold;'>{symbol}{smart_fmt(bal)}</span>", unsafe_allow_html=True)
            
            with col_r:
                st.markdown("**建議轉帳路徑**")
                debtors = sorted([[m, b] for m, b in balances.items() if b < -0.01], key=lambda x: x[1])
                creditors = sorted([[m, b] for m, b in balances.items() if b > 0.01], key=lambda x: x[1], reverse=True)
                
                if not debtors:
                    st.caption("目前帳目已平！")
                else:
                    d_idx, c_idx = 0, 0
                    while d_idx < len(debtors) and c_idx < len(creditors):
                        d_name, d_amt = debtors[d_idx]
                        c_name, c_amt = creditors[c_idx]
                        flow = min(abs(d_amt), c_amt)
                        
                        st.markdown(f"""
                        <div class="transfer-ticket">
                            <span class="ticket-name">{d_name}</span>
                            <span>➜</span>
                            <span class="ticket-name">{c_name}</span>
                            <span class="ticket-amount">{curr} {smart_fmt(flow)}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        debtors[d_idx][1] += flow
                        creditors[c_idx][1] -= flow
                        if abs(debtors[d_idx][1]) < 0.01: d_idx += 1
                        if abs(creditors[c_idx][1]) < 0.01: c_idx += 1

st.divider()

# --- 消費明細清單 ---
st.subheader("📝 帳務明細")
if not df.empty:
    for idx, row in df.iloc[::-1].iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                st.caption(row['Date'].split(" ")[0])
                st.markdown("🎯" if "還款" in row['Item'] else "🛒")
            with c2:
                st.markdown(f"**{row['Item']}**")
                st.caption(f"{row['Payer']} 支付，由 {row['Beneficiaries']} 分攤")
            with c3:
                st.markdown(f"**{row['Currency']}**")
                st.markdown(f"{smart_fmt(row['Amount'])}")
                if st.button("⋮", key=f"edit_{idx}"):
                    edit_entry_ui(idx, row)
else:
    st.info("目前還沒有任何紀錄喔！")

st.caption("---")
st.caption("⚡️ 提示：資料會自動存檔於同目錄下的 trip_ledger.csv")
