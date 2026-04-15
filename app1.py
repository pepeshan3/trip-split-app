  <div class="ticket-label">付款</div>
                                <div class="ticket-name">{t['from']}</div>
                            </div>
                            <div class="ticket-center">
                                <div class="ticket-arrow">➜</div>
                                <div class="ticket-amount">${smart_fmt(t['amount'])}</div>
                            </div>
                            <div class="ticket-side">
                                <div class="ticket-label">收款</div>
                                <div class="ticket-name">{t['to']}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
else:
    st.info("尚無資料")

# --- 備份區 (維持原本設計) ---
st.markdown("---")
with st.expander("📂 資料庫備份/還原 - 程式人員專用", expanded=False):
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("#### 📥 下載備份")
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                st.download_button("下載 .csv 檔", f, file_name="ledger_backup.csv", mime="text/csv")
    with col_b2:
        st.markdown("#### 📤 上傳還原")
        up_file = st.file_uploader("選擇檔案", type=["csv"], label_visibility="collapsed")
        if up_file:
            pd.read_csv(up_file).to_csv(DATA_FILE, index=False)
            st.success("還原成功！")
            time.sleep(1)
            st.rerun()
    
    st.divider()
    st.caption("📜 歷史結算封存檔：")
    if os.path.exists("history"):
        files = sorted([f for f in os.listdir("history") if f.endswith(".csv")], reverse=True)
        for f in files:
            with open(os.path.join("history", f), "rb") as hf:
                st.download_button(f"📥 {f}", hf, file_name=f, key=f)
