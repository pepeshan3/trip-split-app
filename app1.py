import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime, timedelta, timezone

# --- 1. 基本設定 ---
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

# --- 3. 側邊欄 (唯一版本) ---
with st.sidebar:
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #1E293B; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #E2E8F0 !important; }
        .member-capsule { display: inline-block; background-color: rgba(255, 255, 255, 0.1); color: #F8FAFC; padding: 4px 12px; border-radius: 20px; margin: 4px 2px; font-size: 0.9rem; border: 1px solid rgba(255, 255, 255, 0.2); }
    </style>
    """, unsafe_allow_html=True)
    st.header("👥 成員名單")
    if st.session_state['members']:
        member_html = "".join([f"<span class='member-capsule'>{m}</span>" for m in st.session_state['members']])
        st.markdown(f"<div style='margin-bottom:15px;'>{member_html}</div>", unsafe_allow_html=True)
    
    new_name = st.text_input("輸入名字", placeholder="你的名字", key="sidebar_new_member")
    if st.button("➕ 新增成員", use_container_width=True):
        if new_name and new_name not in st.session_state['members']:
            st.session_state['members'].append(new_name)
            save_members(st.session_state['members'])
            st.rerun()

# --- 4. 核心功能 (AI 辨識對話框) ---
@st.dialog("🤖 AI 智慧辨識 (模擬模式)")
def ai_ocr_dialog():
    st.write("📸 上傳收據照片，由 AI 自動解析品項與金額。")
    uploaded_file = st.file_uploader("選擇照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        with st.status("🔍 解析中...", expanded=True) as status:
            time.sleep(1.5)
            status.update(label="✅ 辨識完成！", state="complete")
        mock_items = [{"n": "特製牛肉麵", "p": 180}, {"n": "大滷麵", "p": 150}, {"n": "滷蛋", "p": 15}]
        payer = st.selectbox("誰墊錢?", st.session_state['members'])
        for i, item in enumerate(mock_items):
            c1, c2 = st.columns([2, 3])
            c1.write(f"**{item['n']}** (${item['p']})")
            st.multiselect("誰吃的?", st.session_state['members'], key=f"ocr_item_{i}")
        if st.button("🚀 匯入帳本", type="primary", use_container_width=True):
            st.success("已成功匯入！")
            st.balloons()
            time.sleep(1)
            st.rerun()

# --- 5. 主介面 ---
if not st.session_state['members']:
    st.info("👈 請先在左側新增成員")
    st.stop()

st.title("✈️ 旅程分帳系統 V2.0")
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    if col1.button("💸 一般消費", use_container_width=True, type="primary"): st.toast("請點擊彈窗功能")
    if col2.button("🤝 登記還款", use_container_width=True): st.toast("請點擊彈窗功能")
    if col3.button("🤖 AI 辨識", use_container_width=True): ai_ocr_dialog()

# 資料讀取與顯示 (簡化版示意)
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    st.subheader("📝 帳務明細")
    st.dataframe(df, use_container_width=True)
else:
    st.info("目前尚無資料")
