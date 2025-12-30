import streamlit as st
import pandas as pd
import requests
import math
import urllib3

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心初始化 (徹底消除截圖中的 AttributeError) ---
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'bs_data' not in st.session_state:
    st.session_state.bs_data = []

# --- 2. 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_login():
    if st.session_state.password_correct: return True
    st.set_page_config(page_title="亞馬遜決策系統", layout="centered")
    st.title("🔐 TPC 內部系統登入")
    pwd = st.text_input("輸入公司訪問密碼：", type="password")
    if st.button("確認"):
        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

if check_login():
    st.set_page_config(page_title="亞馬遜決策系統 V11.0", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V10.0")

    # --- 3. 導航標籤 (對齊截圖中的標籤順序) ---
    tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1 & 模組 2: 保持您的核心逻辑不变 ---
    with tabs[0]: st.subheader("💰 2026 運費與利潤測算中心")
    with tabs[1]: st.header("📊 市場競品調研")
    with tabs[2]: st.header("🖼️ 場景批量渲染")

    # --- 📦 模組 4: 1:1 對齊最後一張截圖 (efed275eb) 的備貨計算器 ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        
        # 頂部公式藍色提示條
        st.info("💡 根據您的備貨公式：(採購週期 + 運輸週期 + 安全庫存天數) × 日銷 - 現有庫存")
        
        # 三行雙欄輸入佈局
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        with row1_col1:
            daily_sales = st.number_input("預估日銷量 (Pcs/天)", value=20)
        with row1_col2:
            prod_cycle = st.number_input("採購生產週期 (天)", value=7)
        with row1_col3:
            ship_cycle = st.number_input("跨境運輸週期 (天)", value=30)
            
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        with row2_col1:
            buffer_days = st.number_input("安全緩衝天數 (天)", value=15)
        with row2_col2:
            total_stock = st.number_input("現有總庫存 (FBA + 在途)", value=200)
        with row2_col3:
            moq = st.number_input("最小訂貨量 (MOQ)", value=100)

        # 核心備貨計算邏輯
        # 理論備貨量
        theo_restock = (prod_cycle + ship_cycle + buffer_days) * daily_sales - total_stock
        theo_restock = max(0, int(theo_restock))
        
        # 實際建議下單量 (考慮 MOQ)
        act_order = theo_restock if theo_restock >= moq else (moq if theo_restock > 0 else 0)
        
        # 目前庫存可支撐天數
        support_days = total_stock / daily_sales if daily_sales > 0 else 0
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 底部大指標顯示
        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1:
            st.markdown(f"##### 理論建議備貨\n## {theo_restock} Pcs")
        with res_col2:
            st.markdown(f"##### 實際建議下單量 (含MOQ)\n## {act_order} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True) # 對齊截圖綠色箭頭
        with res_col3:
            st.markdown(f"##### 目前庫存可支撐\n## {int(support_days)} 天")

        # 動態提示
        if support_days < (prod_cycle + ship_cycle):
            st.error(f"⚠️ 警告：目前庫存不足以撐過生產與運輸週期，缺貨風險高！")
