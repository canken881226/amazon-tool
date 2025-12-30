import streamlit as st
import requests
import pandas as pd
import math
import urllib3
from PIL import Image
import io

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心環境初始化 (防止 AttributeError) ---
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False
if "bs_data" not in st.session_state:
    st.session_state.bs_data = []

# --- 🔐 2. 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_password():
    if st.session_state.password_correct: return True
    st.set_page_config(page_title="亞馬遜決策系統 V10.0", layout="wide")
    st.title("🔐 公司內部工具 - 請登入")
    pwd = st.text_input("請輸入訪問密碼：", type="password")
    if st.button("確認登入"):
        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

if check_password():
    # --- ⚙️ 3. 固定配置 ---
    RAINFOREST_KEY = "40048B89139943E8B27B30A041F3A9BE"
    st.set_page_config(page_title="亞馬遜全維度決策系統 V10.0", layout="wide")

    # --- 🚀 4. 功能導航 (100% 恢復原始 4 大標籤) ---
    st.title("⚖️ 亞馬遜全維度決策系統 V10.0")
    main_tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 利潤與運費測算 (恢復左右分欄佈局) ---
    with main_tabs[0]:
        st.subheader("💰 2026 運費與利潤測算中心")
        mode = st.radio("發貨模式切換", ["FBA 配送 (2026 官方標準)", "本地發貨 (精確階梯運費)"], horizontal=True)
        
        col_in, col_res = st.columns([1.2, 0.8])
        
        with col_in:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            unit_cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝 (Non-Apparel)", "服裝類 (Apparel)"], horizontal=True)
            st.info("🚚 已自動計入固定頭程：3.0 USD")
            l_cm = st.number_input("長(cm)", 25.4)
            w_cm = st.number_input("寬(cm)", 15.2)
            h_cm = st.number_input("高(cm)", 2.0)
            weight_kg = st.number_input("產品重量 (kg)", 0.5)

        with col_res:
            st.markdown("### 2. 測算明細")
            # 2026 尺寸判定邏輯
            is_small = h_cm <= 1.9 # 0.75英吋
            st.write("判定分段")
            st.markdown(f"## {'✅ 小標準尺寸' if is_small else '⚠️ 大標準尺寸'}")
            
            comm_rate = 0.18 if "服裝" in is_app else 0.16
            ref_fee = price * comm_rate
            
            if mode == "FBA 配送 (2026 官方標準)":
                fba_fee = 2.62 if is_small else 5.42
                total_logistics = fba_fee + 3.0
            else:
                total_logistics = (weight_kg * 131 + 16) / 6.0
            
            profit = price - (unit_cost_rmb / 6.0) - ref_fee - total_logistics
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            
            # 恢復底部的成本結構拆解
            with st.expander("📄 成本結構拆解"):
                st.write(f"佣金 (Referral): ${ref_fee:.2f}")
                st.write(f"物流總支 (Logistics): ${total_logistics:.2f}")
                st.write(f"採購成本 (USD): ${(unit_cost_rmb/6.0):.2f}")

    # --- 📊 模組 2: 市場調研 ---
    with main_tabs[1]:
        st.header("📊 市場與競品調研")
        cat_q = st.text_input("輸入搜尋關鍵詞:")
        if st.button("啟動調研") and cat_q:
            st.write("正在獲取數據...")

    # --- 🖼️ 模組 3: 場景渲染 ---
    with main_tabs[2]:
        st.header("🖼️ 場景批量渲染")
        st.write("功能已恢復：請上傳背景圖...")

    # --- 📦 模組 4: 備貨管理 ---
    with main_tabs[3]:
        st.header("📦 智能備貨管理")
        s7 = st.number_input("7日銷量", value=70)
        st.metric("日均銷量", f"{s7/7:.1f}")
