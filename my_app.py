import streamlit as st
import pandas as pd
import requests
import math
import urllib3
from PIL import Image
import io

# 禁用安全請求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心初始化 (徹底解決所有 AttributeError 報錯) ---
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'bs_data' not in st.session_state:
    st.session_state.bs_data = []

# --- 2. 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_login():
    if st.session_state.password_correct: return True
    st.set_page_config(page_title="🔐 登入", layout="centered")
    st.title("🔐 TPC 內部系統登入")
    pwd = st.text_input("輸入公司訪問密碼：", type="password")
    if st.button("確認登入"):
        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

if check_login():
    st.set_page_config(page_title="亞馬遜決策系統 V11.0", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V11.0")

    # --- 3. 功能導航 (恢復 4 個標籤) ---
    tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 利潤與運費測算 ---
    with tabs[0]:
        st.subheader("💰 2026 運費與利潤測算中心")
        mode = st.radio("模式", ["FBA 配送 (2026 官方標準)", "本地發貨"], horizontal=True)
        col_in, col_res = st.columns([1.2, 0.8])
        with col_in:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝 (Non-Apparel)", "服裝類 (Apparel)"], horizontal=True)
            st.info("🚚 已自動計入固定頭程：3.0 USD")
            L = st.number_input("長 (cm)", 25.40); W = st.number_input("寬 (cm)", 15.20)
            H = st.number_input("高 (cm)", 2.00); KG = st.number_input("重量 (kg)", 0.50)
        with col_res:
            st.markdown("### 2. 測算明細")
            is_sm = H <= 1.9
            st.markdown(f"## 判定: {'✅ 小標準' if is_sm else '⚠️ 大標準'}")
            ship = (3.22 + 3.0) if is_sm else (5.40 + 3.0)
            profit = price - (cost_rmb/6.0) - ship - (price*0.16)
            st.success(f"### 預估純利: ${profit:.2f}")
            with st.expander("📄 成本結構拆解"):
                st.write(f"配送費(含頭程): ${ship:.2f}")

    # --- 📊 模組 2: 市場調研 ---
    with tabs[1]:
        st.header("📊 市場與競品調研")
        cat_q = st.text_input("輸入搜尋關鍵字或 ASIN:")
        if st.button("啟動調研") and cat_q:
            st.info("數據獲取中...")

    # --- 🖼️ 模組 3: 場景渲染 ---
    with tabs[2]:
        st.header("🖼️ 場景批量渲染")
        bg_files = st.file_uploader("1. 背景圖 (多選)", accept_multiple_files=True)
        pr_files = st.file_uploader("2. 產品圖 (PNG)", accept_multiple_files=True)
        if st.button("🔥 批量合成"):
            if bg_files and pr_files:
                for bg in bg_files:
                    for pr in pr_files:
                        img_bg = Image.open(bg).convert("RGBA")
                        img_bg.paste(Image.open(pr).convert("RGBA"), (100, 100))
                        st.image(img_bg, use_container_width=True)

    # --- 📦 模組 4: 1:1 對齊截圖 efed275eb 的備貨計算器 ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        st.info("💡 根據您的備貨公式：(採購週期 + 運輸週期 + 安全庫存天數) × 日銷 - 現有庫存")
        
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: daily_sales = st.number_input("預估日銷量 (Pcs/天)", value=20)
        with r1c2: prod_cycle = st.number_input("採購生產週期 (天)", value=7)
        with r1c3: ship_cycle = st.number_input("跨境運輸週期 (天)", value=30)
            
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: buffer_days = st.number_input("安全緩衝天數 (天)", value=15)
        with r2c2: total_stock = st.number_input("現有總庫存 (FBA + 在途)", value=200)
        with r2c3: moq = st.number_input("最小訂貨量 (MOQ)", value=100)

        theo_restock = max(0, int((prod_cycle + ship_cycle + buffer_days) * daily_sales - total_stock))
        act_order = theo_restock if theo_restock >= moq else (moq if theo_restock > 0 else 0)
        support_days = total_stock / daily_sales if daily_sales > 0 else 0
        
        st.markdown("<br>", unsafe_allow_html=True)
        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1: st.markdown(f"##### 理論建議備貨\n## {theo_restock} Pcs")
        with res_col2: 
            st.markdown(f"##### 實際建議下單量 (含MOQ)\n## {act_order} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True)
        with res_col3: st.markdown(f"##### 目前庫存可支撐\n## {int(support_days)} 天")
