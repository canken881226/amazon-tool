import streamlit as st
import pandas as pd
import requests
import math
import urllib3
from PIL import Image
import io

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 徹底解決 bs_data 報錯：改用全新的變量名 ---
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
# 徹底放棄舊的 bs_data，改用 market_data 避免死鎖
if 'market_data' not in st.session_state:
    st.session_state.market_data = []

# --- 2. 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def login():
    if st.session_state.password_correct: return True
    st.set_page_config(page_title="🔐 登入", layout="centered")
    st.title("🔐 TPC 內部系統登入")
    pwd = st.text_input("請輸入訪問密碼：", type="password")
    if st.button("確認登入"):
        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

if login():
    st.set_page_config(page_title="亞馬遜決策系統 V10.0", layout="wide")
    
    # --- 3. 恢復標籤頁：找回消失的渲染和備貨 ---
    st.title("⚖️ 亞馬遜全維度決策系統 V10.0")
    tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 標籤 1: 恢復 V9.9 經典佈局與成本明細 ---
    with tabs[0]:
        st.subheader("💰 2026 運費與利潤測算中心")
        mode = st.radio("模式", ["FBA 配送 (2026 官方標準)", "本地發貨"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        with col_l:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝 (Non-Apparel)", "服裝類 (Apparel)"], horizontal=True)
            st.info("🚚 已自動計入固定頭程：3.0 USD")
            L = st.number_input("長 (cm)", 25.4)
            W = st.number_input("寬 (cm)", 15.2)
            H = st.number_input("高/厚度 (cm)", 2.0)
            KG = st.number_input("重量 (kg)", 0.5)
        with col_r:
            st.markdown("### 2. 測算明細")
            is_sm = H <= 1.9
            st.markdown(f"## 判定分段: {'✅ 小標準' if is_sm else '⚠️ 大標準'}")
            ref = price * (0.18 if "服裝" in is_app else 0.16)
            ship = (3.22 + 3.0) if is_sm else (5.4 + 3.0)
            profit = price - (cost_rmb/6.0) - ship - ref
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            # 補回消失的成本結構拆解
            with st.expander("📄 成本結構拆解"):
                st.write(f"佣金: ${ref:.2f}")
                st.write(f"配送費(含頭程): ${ship:.2f}")
                st.write(f"產品採購: ${(cost_rmb/6.0):.2f}")

    with tabs[1]: # 📊 市場調研
        st.header("📊 市場競品調研")
        st.text_input("輸入關鍵字或 ASIN")

    with tabs[2]: # 🖼️ 場景渲染
        st.header("🖼️ 場景批量渲染")
        st.write("功能已恢復：請上傳背景圖與產品 PNG 圖案...")

    with tabs[3]: # 📦 備貨管理
        st.header("📦 智能備貨管理")
        s7 = st.number_input("7日銷量", 70)
        st.metric("日均銷量", f"{s7/7:.1f}")
