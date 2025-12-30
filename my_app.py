import streamlit as st
import pandas as pd
import urllib3
from PIL import Image
import io

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心初始化 ---
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
    st.set_page_config(page_title="亞馬遜決策系統 V13.2", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V13.2")

    # --- 🚀 四大功能標籤 ---
    tabs = st.tabs(["💰 自動利潤測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 自動化利潤測算 (修復版) ---
    with tabs[0]:
        st.subheader("💰 2026 官方新政自動測算 (含 5% 預警)")
        # 模式選擇
        mode = st.radio("配送模式切換", ["FBA 官方配送 (含$3頭程)", "FBM 本地發貨 (無頭程)"], horizontal=True)
        
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 基礎參數設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("採購成本 (RMB)", value=35.0)
            
            # 💡 佣金鎖定邏輯 (修正點 1)
            category = st.radio("類目性質", ["非服裝類 (16%)", "服裝類 (18%)"], horizontal=True)
            
            st.markdown("#### 📏 物理屬性 (系統自動判定分段)")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("最長邊 (cm)", value=38.1)
            with c2: w_cm = st.number_input("次長邊 (cm)", value=30.4)
            with c3: h_cm = st.number_input("厚度/最短邊 (cm)", value=1.9)
            weight_kg = st.number_input("發貨重量 (kg)", value=0.45)

        with col_r:
            st.markdown("### 2. 系統判定與計算結果")
            
            # --- 2026 官方判定標準 ---
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            is_large = not is_small and (l_cm <= 45.7 and w_cm <= 35.5 and h_cm <= 20.3 and weight_kg <= 9.07)
            
            # --- FBA 基準配送費 (2026.01.15) ---
            if is_small:
                tier = "小號標準尺寸"
                base_fba = 3.32 if price >= 10.0 else 2.05
            elif is_large:
                tier = "大號標準尺寸"
                base_fba = 5.42 if price >= 10.0 else 3.35
            else:
                tier = "大件/超標尺寸"
                base_fba = 9.73
            
            # --- 各項費用計算 ---
            # 1. 佣金計算 (修正點 1)
            comm_rate = 0.16 if "16%" in category else 0.18
            referral_fee = price * comm_rate
            
            # 2. 採購成本
            purchase_usd = cost_rmb / 6.0
            
            # 3. FBA 模式費用
            fba_head = 3.0 if "FBA" in mode else 0.0
            fba_ship = (base_fba * 1.05) if "FBA" in mode else 0.0
            
            # 4. FBM 模式費用 (修正點 2: 補回丟失的配送費)
            # 公式: (重量kg * 131 + 16) / 6.0
            fbm_ship = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            
            # 5. 總成本與利潤
            total_cost = purchase_usd + referral_fee + fba_head + fba_ship + fbm_ship
            profit = price - total_cost
            
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率", f"{(profit/price)*100:.2f}%")
            st.info(f"📍 **當前判定分段**：{tier}")

            with st.expander("📄 成本明細", expanded=True):
                st.write(f"🎫 類目佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA 頭程: ${fba_head:.2f}")
                    st.write(f"📦 2026 配送費 (含5%緩衝): ${fba_ship:.3f}")
                else:
                    st.write(f"📮 FBM 本地配送費: ${fbm_ship:.2f}")

    # --- 📊 模組 2: 市場與競品調研 ---
    with tabs[1]:
        st.header("📊 市場與競品調研")
        asin_q = st.text_input("輸入 ASIN 或 關鍵字")
        st.button("啟動調研分析")

    # --- 🖼️ 模組 3: 場景批量渲染 ---
    with tabs[2]:
        st.header("🖼️ 場景批量渲染")
        c1, c2 = st.columns(2)
        with c1: st.file_uploader("1. 背景圖", accept_multiple_files=True, key="bg")
        with c2: st.file_uploader("2. 產品 PNG", accept_multiple_files=True, key="pr")
        st.button("🔥 開始渲染")

    # --- 📦 模組 4: 智能備貨管理 ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        st.info("💡 公式：(採購週期 + 運輸週期 + 安全天數) × 日銷 - 庫存")
        r1, r2, r3 = st.columns(3)
        with r1: daily = st.number_input("日銷量", value=20)
        with r2: stock = st.number_input("當前總庫存", value=200)
        with r3: moq = st.number_input("最小訂貨量", value=100)
        theo = max(0, int((7 + 30 + 15) * daily - stock))
        st.metric("建議補貨量", f"{theo if theo >= moq else (moq if theo > 0 else 0)} Pcs")
