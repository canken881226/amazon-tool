import streamlit as st
import pandas as pd
import requests
import math
import urllib3

# 禁用安全請求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心初始化 (徹底消除 AttributeError: bs_data 報錯) ---
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'bs_data' not in st.session_state:
    st.session_state.bs_data = []

# --- 2. 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_password():
    if st.session_state.password_correct:
        return True
    st.set_page_config(page_title="🔐 登入 - 亞馬遜決策系統", layout="centered")
    st.title("🔐 TPC 內部系統 - 請登入")
    pwd = st.text_input("請輸入訪問密碼：", type="password")
    if st.button("確認登入"):
        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤，請聯繫管理員")
    return False

if check_password():
    # --- 3. 全局配置 (維持 2026 測算標準) ---
    RAINFOREST_KEY = "40048B89139943E8B27B30A041F3A9BE"
    FIXED_EXCHANGE = 6.0
    FIXED_HEAD_SHIP = 3.0
    
    st.set_page_config(page_title="亞馬遜決策系統 V10.2", layout="wide")
    st.title("⚖️ 亞馬遜決策系統 (精簡穩定版)")

    # --- 4. 功能導航 (僅保留最穩定的 2 個標籤) ---
    main_tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研"])

    # --- 💰 模組 1: 利潤測算 (恢復長寬高與成本結構) ---
    with main_tabs[0]:
        st.subheader("💰 2026 運費與利潤測算中心")
        mode = st.radio("模式切換", ["FBA 配送 (2026 官方標準)", "本地發貨 (精確階梯運費)"], horizontal=True)
        col_in, col_res = st.columns([1.2, 0.8])
        
        with col_in:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            unit_cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝 (Non-Apparel)", "服裝類 (Apparel)"], horizontal=True)
            st.info(f"🚚 已自動計入固定頭程：{FIXED_HEAD_SHIP} USD")
            
            # 長寬高輸入框
            length_cm = st.number_input("長 (cm)", value=25.40)
            width_cm = st.number_input("寬 (cm)", value=15.20)
            height_cm = st.number_input("高/厚度 (cm)", value=2.00)
            weight_kg = st.number_input("產品重量 (kg)", value=0.50)

        with col_res:
            st.markdown("### 2. 測算明細")
            # 2026 尺寸判定邏輯
            is_small = height_cm <= 1.9  # 0.75" 判定
            st.markdown(f"## 判定分段: {'✅ 小標準尺寸' if is_small else '⚠️ 大標準尺寸'}")
            
            comm_rate = 0.18 if "服裝" in is_app else 0.16
            ref_fee = price * comm_rate
            
            if mode == "FBA 配送 (2026 官方標準)":
                fba_fee = 2.62 if is_small else 5.42
                total_logistics = fba_fee + FIXED_HEAD_SHIP
            else:
                total_logistics = (weight_kg * 131 + 16) / FIXED_EXCHANGE
            
            profit = price - (unit_cost_rmb / FIXED_EXCHANGE) - ref_fee - total_logistics
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            
            # 成本結構拆解
            with st.expander("📄 成本結構拆解"):
                st.write(f"* 佣金 (Referral Fee): ${ref_fee:.2f}")
                st.write(f"* 物流支 (配送+頭程): ${total_logistics:.2f}")
                st.write(f"* 產品成本 (USD): ${(unit_cost_rmb/FIXED_EXCHANGE):.2f}")

    # --- 📊 模組 2: 市場調研 (恢復) ---
    with main_tabs[1]:
        st.header("📊 市場與競品數據查詢")
        cat_q = st.text_input("輸入搜尋關鍵詞 (如 ASIN):")
        if st.button("啟動調研") and cat_q:
            st.info("數據獲取中...")
        if st.session_state.bs_data:
            st.dataframe(st.session_state.bs_data)
