import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime, timedelta, timezone

# --- 全域設定 ---
TW_TIMEZONE = timezone(timedelta(hours=8))
CURRENCIES = ['TWD', 'JPY', 'USD', 'EUR', 'KRW']
HISTORY_DIR = 'history'
DATA_FILE = 'trip_ledger.csv'
CONFIG_FILE = 'members.json'

# --- 基礎函數 ---
def load_members():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_members(members_list):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(members_list, f, ensure_ascii=False)

def get_ledger():
    cols = ['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries', 'SplitMode', 'SplitDetails']
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            # 確保欄位齊全且處理 NaN
            for col in cols:
                if col not in df.columns:
                    df[col] = "Equal" if col == 'SplitMode' else ""
            
            # 🔥 重要修復：確保關鍵欄位沒有 NaN，否則會報 TypeError
            df['Item'] = df['Item'].fillna("未命名項目").astype(str)
            df['Payer'] = df['Payer'].fillna("未知").astype(str)
            df['Beneficiaries'] = df['Beneficiaries'].fillna("").astype(str)
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0.0)
            return df
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_ledger(df):
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(DATA_FILE, index=False)

def smart_fmt(val):
    try:
        f_val = float(val)
        return f"{f_val:,.0f}" if f_val.is_integer() else f"{f_val:,.2f}"
    except:
        return str(val)

# --- 頁面初始化 ---
st.set_page_config(page_title="旅程分帳助手 Pro", layout="centered", page_icon="💸")

if 'members' not in st.session_state:
    st.session_state.members = load_members()

# --- CSS 樣式 ---
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1E293B; }
    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    .member-capsule {
        display: inline-block; background-color: rgba(255, 255, 255, 0.1);
        color: #F8FAFC; padding: 4px 12px; border-radius: 20px;
        margin: 4px 2px; font-size: 0.85rem; border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .premium-card {
        background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .transfer-ticket {
        display: flex; align-items: center; justify-content: space-between;
        background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 10px;
        padding: 12px; margin-bottom: 8px;
    }
    .ticket-name { font-weight: 700; color: #1E293B; }
    .ticket-amount { font-weight: 800; color: #2563EB; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄 ---
with st.sidebar:
    st.title("👥 成員管理")
    if st.session_state.members:
        m_html = "".join([f"<span class='member-capsule'>{m}</span>" for m in st.session_state.members])
        st.markdown(f"<div>{m_html}</div><br>", unsafe_allow_html=True)
    
    new_name = st.text_input("快速新增成員", placeholder="輸入姓名...", key="new_mem_input", label_visibility="collapsed")
    if st.button("➕ 新增成員", use_container_width=True):
        if new_name and new_name not in st.session_state.members:
            st.session_state.members.append(new_name)
            save_members(st.session_state.members)
            st.rerun()

    with st.expander("⚙️ 進階功能"):
        if st.session_state.members:
            edit_target = st.selectbox("選擇成員", st.session_state.members)
            new_target_name = st.text_input("修改名稱為")
            if st.button("確認修改"):
                if new_target_name:
                    st.session_state.members = [new_target_name if x == edit_target else x for x in st.session_state.members]
                    save_members(st.session_state.members)
                    df_up = get_ledger()
                    df_up['Payer'] = df_up['Payer'].replace(edit_target, new_target_name)
                    def update_bens(b_str):
                        if not isinstance(b_str, str): return b_str
                        return ",".join([new_target_name if b.strip() == edit_target else b.strip() for b in b_str.split(",")])
                    df_up['Beneficiaries'] = df_up['Beneficiaries'].apply(update_bens)
                    save_ledger(df_up)
                    st.rerun()
            if st.button("🗑️ 移除此成員", type="secondary"):
                st.session_state.members.remove(edit_target)
                save_members(st.session_state.members)
                st.rerun()
        st.divider()
        if st.button("🔒 封存目前帳本"):
            if not os.path.exists(HISTORY_DIR): os.makedirs(HISTORY_DIR)
            ts = datetime.now(TW_TIMEZONE).strftime('%Y%m%d_%H%M%S')
            old_df = get_ledger()
            old_df.to_csv(f"{HISTORY_DIR}/ledger_{ts}.csv", index=False)
            save_ledger(pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries', 'SplitMode', 'SplitDetails']))
            st.success("已封存！")
            time.sleep(1)
            st.rerun()

# --- 主畫面邏輯 ---
if not st.session_state.members:
    st.info("👈 請先在側邊欄新增成員！")
    st.stop()

df = get_ledger()

@st.dialog("➕ 新增帳務")
def add_entry_ui(is_repayment=False):
    if not is_repayment:
        st.subheader("💸 新增支出")
        with st.form("expense_form", clear_on_submit=True):
            item = st.text_input("消費項目", placeholder="例如：居酒屋餐費")
            col_curr, col_payer = st.columns(2)
            curr = col_curr.selectbox("幣別", CURRENCIES)
            payer = col_payer.selectbox("誰先墊錢？", st.session_state.members)
            st.write("---")
            split_mode = st.radio("分帳方式", ["所有人平分", "自定義金額 (點餐分帳)"], horizontal=True)
            selected_bens = st.multiselect("參與成員", st.session_state.members, default=st.session_state.members)
            total_amount = 0.0
            custom_shares = {}
            if split_mode == "所有人平分":
                total_amount = st.number_input("總金額", min_value=0.0, step=100.0)
            else:
                st.info("請輸入每位成員的消費金額：")
                for m in selected_bens:
                    val = st.number_input(f"{m} 的金額", min_value=0.0, step=10.0, key=f"share_{m}")
                    custom_shares[m] = val
                total_amount = sum(custom_shares.values())
                st.markdown(f"**自動計算總額：{curr} {smart_fmt(total_amount)}**")
            if st.form_submit_button("確認儲存", type="primary"):
                if item and total_amount > 0 and selected_bens:
                    details_json = json.dumps(custom_shares) if split_mode != "所有人平分" else ""
                    new_row = {
                        'Date': datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d %H:%M'),
                        'Item': str(item), 'Payer': str(payer), 'Amount': float(total_amount), 
                        'Currency': str(curr), 'Beneficiaries': ",".join(selected_bens),
                        'SplitMode': "Manual" if split_mode != "所有人平分" else "Equal",
                        'SplitDetails': details_json
                    }
                    save_ledger(pd.concat([get_ledger(), pd.DataFrame([new_row])], ignore_index=True))
                    st.success("已儲存紀錄！")
                    st.rerun()
                else:
                    st.error("請確認資訊是否正確")
    else:
        st.subheader("🤝 登記還款")
        with st.form("repay_form"):
            p1 = st.selectbox("誰還錢？", st.session_state.members)
            p2 = st.selectbox("還給誰？", st.session_state.members)
            col1, col2 = st.columns(2)
            amt = col1.number_input("金額", min_value=0.0)
            curr = col2.selectbox("幣別", CURRENCIES)
            if st.form_submit_button("確認還款"):
                if amt > 0 and p1 != p2:
                    new_row = {
                        'Date': datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d %H:%M'),
                        'Item': f"還款: {p1} ➜ {p2}", 'Payer': str(p1), 'Amount': float(amt), 
                        'Currency': str(curr), 'Beneficiaries': str(p2), 'SplitMode': 'Equal', 'SplitDetails': ''
                    }
                    save_ledger(pd.concat([get_ledger(), pd.DataFrame([new_row])], ignore_index=True))
                    st.rerun()

@st.dialog("✏️ 編輯帳務")
def edit_entry_ui(idx, row):
    with st.form("edit_form"):
        item = st.text_input("項目", value=str(row['Item']))
        amount = st.number_input("金額", value=float(row['Amount']))
        curr = st.selectbox("幣別", CURRENCIES, index=CURRENCIES.index(row['Currency']) if row['Currency'] in CURRENCIES else 0)
        payer = st.selectbox("付款人", st.session_state.members, index=st.session_state.members.index(row['Payer']) if row['Payer'] in st.session_state.members else 0)
        current_bens = str(row['Beneficiaries']).split(",")
        bens = st.multiselect("分帳人", st.session_state.members, default=[m for m in current_bens if m in st.session_state.members])
        if st.form_submit_button("更新資料"):
            ledger = get_ledger()
            ledger.loc[idx, ['Item', 'Amount', 'Currency', 'Payer', 'Beneficiaries']] = [str(item), float(amount), str(curr), str(payer), ",".join(bens)]
            save_ledger(ledger)
            st.rerun()
    if st.button("🗑️ 刪除", type="secondary"):
        save_ledger(get_ledger().drop(idx))
        st.rerun()

# --- 主佈局 ---
st.title("✈️ 旅程分帳系統")
st.markdown(f"**{len(st.session_state.members)}** 位夥伴 | **{len(df)}** 筆紀錄")

c1, c2 = st.columns(2)
if c1.button("💸 新增支出", use_container_width=True, type="primary"):
    add_entry_ui(False)
if c2.button("🤝 登記還款", use_container_width=True):
    add_entry_ui(True)

st.divider()

# --- 消費明細清單 ---
st.subheader("📝 帳務明細")
if not df.empty:
    for idx, row in df.iloc[::-1].iterrows():
        # 🔥 這裡做了 str() 轉換，防止 NaN 導致報錯
        item_text = str(row['Item'])
        is_repayment = "還款" in item_text
        
        with st.container(border=True):
            col_icon, col_info, col_amt = st.columns([1, 4, 1.2])
            with col_icon:
                st.caption(str(row['Date']).split(" ")[0])
                st.markdown("🎯" if is_repayment else "🛒")
            with col_info:
                st.markdown(f"**{item_text}**")
                mode = " [自訂]" if row.get('SplitMode') == "Manual" else ""
                st.caption(f"{row['Payer']} 支付{mode}")
            with col_amt:
                st.markdown(f"**{row['Currency']} {smart_fmt(row['Amount'])}**")
                if st.button("編輯", key=f"edit_btn_{idx}"):
                    edit_entry_ui(idx, row)
else:
    st.info("尚無紀錄")

st.divider()

# --- 結算概況 ---
if not df.empty:
    st.subheader("🧾 結算概況")
    currs = df['Currency'].unique()
    tabs = st.tabs([f"💵 {c}" for c in currs])
    for i, curr in enumerate(currs):
        with tabs[i]:
            curr_df = df[df['Currency'] == curr]
            all_ppl = set(st.session_state.members)
            for _, r in curr_df.iterrows():
                all_ppl.add(str(r['Payer']))
                for b in str(r['Beneficiaries']).split(","):
                    if b.strip(): all_ppl.add(b.strip())
            
            bals = {m: 0.0 for m in all_ppl}
            for _, row in curr_df.iterrows():
                a, p = float(row['Amount']), str(row['Payer'])
                bens = [b.strip() for b in str(row['Beneficiaries']).split(",") if b.strip()]
                if "還款" not in str(row['Item']):
                    bals[p] += a
                    if row.get('SplitMode') == "Manual" and row.get('SplitDetails'):
                        try:
                            details = json.loads(row['SplitDetails'])
                            for m, s in details.items(): bals[m] -= float(s)
                        except: pass
                    else:
                        s = a / len(bens) if bens else 0
                        for b in bens: bals[b] -= s
                else:
                    bals[p] += a
                    if bens: bals[bens[0]] -= a

            c_l, c_r = st.columns(2)
            with c_l:
                st.markdown("**個人淨額**")
                for m, bal in bals.items():
                    if m in st.session_state.members or abs(bal) > 0.01:
                        color = "#16A34A" if bal >= 0.01 else "#DC2626" if bal <= -0.01 else "#666"
                        st.markdown(f"{m}: <span style='color:{color}; font-weight:bold;'>{'+' if bal>=0.01 else ''}{smart_fmt(bal)}</span>", unsafe_allow_html=True)
            with c_r:
                st.markdown("**建議轉帳路徑**")
                dbtr = sorted([[m, b] for m, b in bals.items() if b < -0.01], key=lambda x: x[1])
                crtr = sorted([[m, b] for m, b in bals.items() if b > 0.01], key=lambda x: x[1], reverse=True)
                if not dbtr or not crtr: st.info("帳目平衡")
                else:
                    di, ci = 0, 0
                    while di < len(dbtr) and ci < len(crtr):
                        flow = min(abs(dbtr[di][1]), crtr[ci][1])
                        if flow > 0.01:
                            st.markdown(f"<div class='transfer-ticket'><span class='ticket-name'>{dbtr[di][0]}</span> ➜ <span class='ticket-name'>{crtr[ci][0]}</span> <span class='ticket-amount'>{curr} {smart_fmt(flow)}</span></div>", unsafe_allow_html=True)
                        dbtr[di][1] += flow
                        crtr[ci][1] -= flow
                        if abs(dbtr[di][1]) < 0.01: di += 1
                        if abs(crtr[ci][1]) < 0.01: ci += 1

st.caption("---")
st.caption("⚡️ 已針對空資料進行修復。")
