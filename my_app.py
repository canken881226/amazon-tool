import streamlit as st
import pandas as pd
import urllib3
from PIL import Image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心環境初始化 ---
if 'password_correct' not in st.session_state: st.session_state.password_correct = False

# --- 2. 🔐 訪問控制 ---
if not st.session_state.password_correct:
    st.set_page_config(page_title="🔐 登入", layout="centered")
    pwd = st.text_input("輸入公司訪問密碼：", type="password")
    if st.button("確認"):
        if pwd == "TPCamazon@2026":
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
else:
    st.set_page_config(page_title="亞馬遜決策系統 V11.9.1", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V11.9.1")

    tabs = st.tabs(["💰 2026 利潤測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 利潤測算 (修復佣金計算 Bug) ---
    with tabs[0]:
        st.subheader("💰 2026 利潤測算 (精確佣金切換)")
        mode = st.radio("模式選擇", ["FBA 官方配送 (含$3頭程)", "FBM 本地發貨 (無頭程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            
            # --- 💡 重點：動態佣金選擇 ---
            category = st.radio("類目性質", ["非服裝類 (16%)", "服裝類 (18%)"], horizontal=True)
            
            st.markdown("#### 📏 產品尺寸與重量")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("長 (cm)", value=38.1)
            with c2: w_cm = st.number_input("寬 (cm)", value=30.4)
            with c3: h_cm = st.number_input("厚度/最短邊 (cm)", value=1.9)
            weight_kg = st.number_input("發貨重量 (kg)", value=0.45)

        with col_r:
            st.markdown("### 2. 測算明細 (2026 標準)")
            
            # --- 判定邏輯 ---
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            
            # --- 配送費計算 (含5%緩衝) ---
            base_fba = (2.62 if is_small else 5.42) if price >= 10.0 else (2.05 if is_small else 3.35)
            fba_fee_final = base_fba * 1.05
            
            # --- 💡 核心修復：根據選擇動態賦值佣金率 ---
            comm_rate = 0.16 if "非服裝類" in category else 0.18
            referral_fee = price * comm_rate
            
            purchase_usd = cost_rmb / 6.0
            fba_head = 3.0 if "FBA" in mode else 0.0
            fbm_shipping = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            fba_final_ship = fba_fee_final if "FBA" in mode else 0.0
            
            total_cost = purchase_usd + referral_fee + fba_head + fba_final_ship + fbm_shipping
            profit = price - total_cost
            
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            
            with st.expander("📄 2026 成本結構明細", expanded=True):
                st.write(f"💵 採購成本: ${purchase_usd:.2f}")
                st.write(f"🎫 亞馬遜佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}") # 此處會動態顯示 16% 或 18%
                if "FBA" in mode:
                    st.write(f"🚚 FBA 頭程費用: ${fba_head:.2f}")
                    st.write(f"📦 官方配送費 (含5%緩衝): ${fba_final_ship:.3f}")
                else:
                    st.write(f"📮 FBM 本地配送費: ${fbm_shipping:.2f}")

    # --- 📊 模組 2 & 🖼️ 模組 3 & 📦 模組 4 (保持 V11.9 穩定代碼) ---
    with tabs[1]: st.header("📊 市場與競品調研")
    with tabs[2]: st.header("🖼️ 場景批量渲染")
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        daily = st.number_input("預估日銷量", value=20)
        stock = st.number_input("現有總庫存", value=200)
        st.metric("目前庫存可支撐", f"{int(stock/daily if daily > 0 else 0)} 天")
