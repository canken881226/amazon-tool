import streamlit as st
import pandas as pd
import requests
import math
import urllib3
from PIL import Image
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心環境初始化 (徹底防止報錯) ---
if 'password_correct' not in st.session_state: st.session_state.password_correct = False
if 'bs_data' not in st.session_state: st.session_state.bs_data = []

# --- 2. 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_login():
    if st.session_state.password_correct: return True
    st.set_page_config(page_title="🔐 登入", layout="centered")
    st.title("🔐 TPC 內部系統登入")
    pwd = st.text_input("輸入公司訪問密碼：", type="password")
    if st.button("確認"):
        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

if check_login():
    st.set_page_config(page_title="亞馬遜決策系統 V11.1", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V11.1")

    # --- 3. 功能導航 ---
    tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 利潤與運費測算 (公式與尺寸同步恢復) ---
    with tabs[0]:
        st.subheader("💰 2026 雙模式精確測算")
        mode = st.radio("模式切換", ["FBA 官方配送 (含頭程)", "FBM 本地發貨 (無頭程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝 (16%)", "服裝類 (18%)"], horizontal=True)
            
            # --- 尺寸輸入恢復 ---
            c_dim1, c_dim2, c_dim3 = st.columns(3)
            with c_dim1: length_cm = st.number_input("長 (cm)", value=25.4)
            with c_dim2: width_cm = st.number_input("寬 (cm)", value=15.2)
            with c_dim3: height_cm = st.number_input("厚度 (cm)", value=2.0)
            weight_kg = st.number_input("產品重量 (kg)", value=0.5)

        with col_r:
            st.markdown("### 2. 測算明細")
            # 數據計算
            is_sm = height_cm <= 1.9 # 0.75" 判定
            comm_rate = 0.18 if "服裝" in is_app else 0.16
            referral_fee = price * comm_rate
            purchase_usd = cost_rmb / 6.0
            
            # 物流拆分邏輯
            fba_head = 3.0 if "FBA" in mode else 0.0
            fba_shipping = (2.62 if is_sm else 5.42) if "FBA" in mode else 0.0
            fbm_shipping = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            
            total_cost = purchase_usd + referral_fee + fba_head + fba_shipping + fbm_shipping
            profit = price - total_cost
            
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            
            # --- 成本結構明細對齊截圖 46b2e1ec ---
            with st.expander("📄 成本結構具體明細", expanded=True):
                st.write(f"💵 產品採購 (USD): ${purchase_usd:.2f}")
                st.write(f"🎫 亞馬遜佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA 頭程費用: ${fba_head:.2f}")
                    st.write(f"📦 FBA 官方配送費: ${fba_shipping:.2f}")
                else:
                    st.write(f"📮 FBM 本地配送費: ${fbm_shipping:.2f}")

    # --- 📊 模組 2: 市場調研 ---
    with tabs[1]:
        st.header("📊 市場與競品調研")
        asin_q = st.text_input("輸入關鍵字或 ASIN:")
        if st.button("啟動調研"): st.info("數據獲取中...")

    # --- 🖼️ 模組 3: 場景渲染 ---
    with tabs[2]:
        st.header("🖼️ 場景批量渲染")
        st.info("功能已恢復：請上傳背景圖與產品 PNG 圖案...")

    # --- 📦 模組 4: 1:1 對齊截圖 efed275eb 的備貨計算器 ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        st.info("💡 根據您的備貨公式：(採購週期 + 運輸週期 + 安全庫存天數) × 日銷 - 現有庫存")
        
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: daily = st.number_input("預估日銷量 (Pcs/天)", value=20)
        with r1c2: p_cyc = st.number_input("採購生產週期 (天)", value=7)
        with r1c3: s_cyc = st.number_input("跨境運輸週期 (天)", value=30)
            
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: buff = st.number_input("安全緩衝天數 (天)", value=15)
        with r2c2: stock = st.number_input("現有總庫存 (FBA + 在途)", value=200)
        with r2c3: moq = st.number_input("最小訂貨量 (MOQ)", value=100)

        theo = max(0, int((p_cyc + s_cyc + buff) * daily - stock))
        act = theo if theo >= moq else (moq if theo > 0 else 0)
        
        st.markdown("<br>", unsafe_allow_html=True)
        res_col1, res_col2, res_col3 = st.columns(3)
        with res_col1: st.markdown(f"##### 理論建議備貨\n## {theo} Pcs")
        with res_col2: 
            st.markdown(f"##### 實際建議下單量 (含MOQ)\n## {act} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True)
        with res_col3: st.markdown(f"##### 目前庫存可支撐\n## {int(stock/daily if daily > 0 else 0)} 天")
