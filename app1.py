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

def save_members(members_list):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(members_list, f, ensure_ascii=False)

# --- 2. 初始化 ---
st.set_page_config(page_title="旅程分帳系統 V2.0", layout="centered")
if 'members' not in st.session_state:
    st.session_state['members'] = load_members()

# --- 3. 側邊欄 (深色質感) ---
with st.sidebar:
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #1E293B; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p { color: #E2E8F0 !important; }
        .member-capsule { display: inline-block; background-color: rgba(255, 255, 255, 0.1); color: #F8FAFC; padding: 4px 12px; border-radius: 20px; margin: 4px 2px; font-size: 0.9rem; border: 1px solid rgba(255, 255, 255, 0.2); }
        .custom-divider { margin: 20px 0; border-top: 1px dashed rgba(255, 255, 255, 0.2); }
    </style>
    """, unsafe_allow_html=True)

    st.header("👥 成員名單")
    if st.session_state['members']:
        m_html = "".join([f"<span class='member-capsule'>{m}</span>" for m in st.session_state['members']])
        st.markdown(f"<div style='margin-bottom: 15px;'>{m_html}</div>", unsafe_allow_html=True)
    
    col_add_1, col_add_2 = st.columns([2, 1])
    with col_add_1:
        new_name = st.text_input("輸入名字", placeholder="你的名字", label_visibility="collapsed", key="sidebar_name_input")
    with col_add_2:
        if st.button("➕", use_container_width=True, key="sidebar_add_btn"):
            if new_name and new_name not in st.session_state['members']:
                st.session_state['members'].append(new_name)
                save_members(st.session_state['members'])
                st.rerun()

    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
    with st.expander("⚙️ 設定與進階操作"):
        if st.session_state['members']:
            target_member = st.selectbox("選擇對象", st.session_state['members'], key="sidebar_target_sel")
            if st.button(f"移除 {target_member}", type="primary", key="sidebar_del_btn"):
                st.session_state['members'].remove(target_member)
                save_members(st.session_state['members'])
                st.rerun()

# --- 4. 核心功能函數 ---
def save_entry(item, payer, amount, currency, beneficiaries):
    df_l = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries'])
    df_l = df_l.loc[:, ~df_l.columns.str.contains('^Unnamed')]
    tw_now = datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d %H:%M')
    new_e = {'Date': tw_now, 'Item': item, 'Payer': payer, 'Amount': amount, 'Currency': currency, 'Beneficiaries': ",".join(beneficiaries)}
    pd.concat([df_l, pd.DataFrame([new_e])], ignore_index=True).to_csv(DATA_FILE, index=False)

# --- 5. 功能對話框 ---
@st.dialog("➕ 新增紀錄")
def add_entry_dialog(mode):
    if mode == 0:
        st.subheader("💸 新增消費")
        with st.form("add_exp"):
            it = st.text_input("項目", placeholder="如: 晚餐")
            am = st.number_input("金額", min_value=0.0, format="%g")
            py = st.selectbox("誰墊錢?", st.session_state['members'])
            be = st.multiselect("分給誰?", st.session_state['members'], default=st.session_state['members'])
            if st.form_submit_button("💾 儲存消費", type="primary"):
                if am > 0 and it: save_entry(it, py, am, "TWD", be); st.rerun()
    elif mode == 1:
        st.subheader("🤝 登記還款")
        with st.form("add_stl"):
            p_s = st.selectbox("誰還錢?", st.session_state['members'])
            r_s = st.selectbox("還給誰?", st.session_state['members'])
            a_s = st.number_input("還款金額", min_value=0.0, format="%g")
            if st.form_submit_button("🤝 確認還款", type="primary"):
                if a_s > 0 and p_s != r_s: save_entry(f"還款: {p_s}->{r_s}", p_s, a_s, "TWD", [r_s]); st.rerun()

@st.dialog("🤖 AI 智慧辨識分帳")
def ai_ocr_dialog():
    st.write("📸 上傳收據照片，由 AI 自動解析品項與金額。")
    up = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"], key="ocr_upload")
    if up:
        with st.status("🔍 AI 正在解析收據內容...") as s:
            time.sleep(1.5); s.update(label="✅ 辨識完成！", state="complete")
        mock = [{"n": "特製牛肉麵", "p": 180}, {"n": "招牌大滷麵", "p": 150}, {"n": "滷味拼盤", "p": 85}]
        py_ocr = st.selectbox("誰墊錢?", st.session_state['members'], key="ocr_payer_sel")
        for i, d in enumerate(mock):
            c1, c2 = st.columns([2, 3])
            c1.write(f"**{d['n']}** (${d['p']})")
            sel = c2.multiselect("誰吃的?", st.session_state['members'], key=f"ocr_m_{i}")
            if st.button(f"匯入 {d['n']}", key=f"ocr_b_{i}"):
                if sel: save_entry(d['n'], py_ocr, d['p'], "TWD", sel); st.toast(f"已匯入 {d['n']}")
        if st.button("✅ 全部完成", use_container_width=True): st.rerun()

# --- 6. 主介面展示 ---
if not st.session_state['members']:
    st.info("👈 請先在左側新增成員"); st.stop()

df = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame(columns=['Date', 'Item', 'Payer', 'Amount', 'Currency', 'Beneficiaries'])
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

st.markdown("<h1 style='font-weight:800; font-size:2.5rem; color:#1F2937;'>✈️ 旅程分帳系統 V2.0</h1>", unsafe_allow_html=True)
with st.container(border=True):
    cl1, cl2, cl3 = st.columns(3)
    if cl1.button("💸 一般消費", use_container_width=True, type="primary"): add_entry_dialog(0)
    if cl2.button("🤝 登記還款", use_container_width=True): add_entry_dialog(1)
    if cl3.button("🤖 AI 辨識", use_container_width=True): ai_ocr_dialog()

# (此處銜接你原本的「帳務明細」與「結算儀表板」邏輯)
st.divider()
if not df.empty:
    st.subheader("📝 帳務明細")
    st.dataframe(df.iloc[::-1], use_container_width=True)
else:
    st.info("目前尚無資料")
