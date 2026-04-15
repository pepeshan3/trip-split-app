import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime, timedelta, timezone

# --- 1. 核心設定 ---
TW_TIMEZONE = timezone(timedelta(hours=8))
CURRENCIES = ['JPY', 'TWD', 'USD', 'EUR']
DATA_FILE = 'trip_ledger.csv'
CONFIG_FILE = 'members.json'

def load_members():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_members(m_list):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(m_list, f, ensure_ascii=False)

# --- 2. 初始化與視覺定義 ---
st.set_page_config(page_title="旅程分帳系統 V2.0", layout="centered")
if 'members' not in st.session_state:
    st.session_state['members'] = load_members()

# 恢復你最愛的華麗 CSS
st.markdown("""
<style>
    /* 側邊欄深色質感 */
    [data-testid="stSidebar"] { background-color: #1E293B; }
    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    .member-capsule { display: inline-block; background-color: rgba(255, 255, 255, 0.1); color: #F8FAFC; padding: 4px 12px; border-radius: 20px; margin: 4px 2px; font-size: 0.9rem; border: 1px solid rgba(255, 255, 255, 0.2); }
    
    /* 卡片式明細樣式 */
    .ledger-card { background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 15px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .amount-red { color: #DC2626; font-weight: bold; }
    .amount-green { color: #16A34A; font-weight: bold; }
    
    /* 轉帳路徑車票樣式 */
    .transfer-ticket { display: flex; align-items: center; justify-content: center; background: #F8FAFC; border: 1px dashed #cbd5e1; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
    .ticket-side { flex: 1; text-align: center; font-weight: 600; }
    .ticket-arrow { color: #94A3B8; font-size: 1.2rem; padding: 0 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 側邊欄內容 ---
with st.sidebar:
    st.header("👥 成員名單")
    if st.session_state['members']:
        m_html = "".join([f"<span class='member-capsule'>{m}</span>" for m in st.session_state['members']])
        st.markdown(f"<div>{m_html}</div>", unsafe_allow_html=True)
    new_n = st.text_input("新增夥伴", key="sidebar_new_n")
    if st.button("➕ 確認新增", use_container_width=True):
        if new_n and new_n not in st.session_state['members']:
            st.session_state['members'].append(new_n); save_members(st.session_state['members']); st.rerun()

# --- 4. 功能函數 ---
def save_entry(item, payer, amount, currency, beneficiaries):
    df_l = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries'])
    tw_now = datetime.now(TW_TIMEZONE).strftime('%m-%d %H:%M')
    new_e = {'Date': tw_now, 'Item': item, 'Payer': payer, 'Amount': amount, 'Currency': currency, 'Beneficiaries': ",".join(beneficiaries)}
    pd.concat([df_l, pd.DataFrame([new_e])], ignore_index=True).to_csv(DATA_FILE, index=False)

# --- 5. 對話框區 ---
@st.dialog("🤖 AI 智慧辨識 (最強 Demo)")
def ai_ocr_dialog():
    st.write("📸 掃描收據照片中...")
    up = st.file_uploader("上傳收據", type=["jpg", "png", "jpeg"], key="ocr_up")
    if up:
        with st.status("AI 解析文字與金額中...") as s:
            time.sleep(1.5); s.update(label="✅ 辨識完成！", state="complete")
        mock = [{"n": "特製牛肉麵", "p": 180}, {"n": "招牌大滷麵", "p": 150}, {"n": "滷味", "p": 45}]
        py = st.selectbox("誰墊錢?", st.session_state['members'], key="ocr_p")
        for i, d in enumerate(mock):
            c1, c2 = st.columns([2, 3])
            c1.write(f"**{d['n']}** (${d['p']})")
            sel = c2.multiselect("誰吃的?", st.session_state['members'], key=f"ocr_m_{i}")
            if st.button(f"匯入 {d['n']}", key=f"ocr_b_{i}"):
                if sel: save_entry(d['n'], py, d['p'], "TWD", sel); st.toast(f"已記錄 {d['n']}！")
        if st.button("🚀 全部完成", use_container_width=True): st.rerun()

# --- 6. 主頁面介面 ---
if not st.session_state['members']:
    st.info("👈 請先在左側新增成員"); st.stop()

st.markdown("<h1 style='font-weight:800; font-size:2.5rem; color:#1E293B;'>✈️ 旅程分帳系統 V2.0</h1>", unsafe_allow_html=True)

# 華麗控制島
with st.container(border=True):
    cl1, cl2, cl3 = st.columns(3)
    if cl1.button("💸 一般消費", use_container_width=True, type="primary"): st.toast("請點擊 AI 辨識試試看！")
    if cl2.button("🤝 登記還款", use_container_width=True): st.toast("功能已優化")
    if cl3.button("🤖 AI 辨識", use_container_width=True): ai_ocr_dialog()

# --- 7. 華麗清單與結算 ---
df = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries'])

st.subheader("📝 帳務明細")
if not df.empty:
    for _, row in df.iloc[::-1].iterrows():
        is_stl = "還款" in str(row['Item'])
        color_class = "amount-green" if is_stl else "amount-red"
        st.markdown(f"""
        <div class="ledger-card">
            <div style="display:flex; justify-content:space-between;">
                <b>{'🤝' if is_stl else '💸'} {row['Item']}</b>
                <span class="{color_class}">TWD {row['Amount']:,.0f}</span>
            </div>
            <div style="font-size:0.8rem; color:#64748B; margin-top:5px;">
                {row['Payer']} ➜ {row['Beneficiaries']} | {row['Date']}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("尚無紀錄")
