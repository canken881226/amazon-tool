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
    st.set_page_config(page_title="亞馬遜決策系統 V13.3", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V13.3")

    # --- 🚀 核心四大功能標籤頁 (嚴禁修改結構) ---
    tabs = st.tabs(["💰 自動利潤測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 自動利潤測算 ---
    with tabs[0]:
        st.subheader("💰 2026 官方新政自動測算 (含 5% 預警)")
        mode = st.radio("配送模式切換", ["FBA 官方配送 (含$3頭程)", "FBM 本地發貨 (無頭程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 基礎參數設定")
            price = st.number_input("產品售價 ($)", value=19.99, key="price")
            cost_rmb = st.number_input("採購成本 (RMB)", value=35.0, key="cost")
            category = st.radio("類目性質", ["非服裝類 (16%)", "服裝類 (18%)"], horizontal=True)
            
            st.markdown("#### 📏 物理屬性 (自動判定分段)")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("長 (cm)", value=38.1)
            with c2: w_cm = st.number_input("寬 (cm)", value=30.4)
            with c3: h_cm = st.number_input("厚度/最短邊 (cm)", value=1.9)
            weight_kg = st.number_input("發貨重量 (kg)", value=0.45)

        with col_r:
            st.markdown("### 2. 計算結果")
            # 2026 判定
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            is_large = not is_small and (l_cm <= 45.7 and w_cm <= 35.5 and h_cm <= 20.3 and weight_kg <= 9.07)
            
            if is_small:
                tier, base_fba = "小號標準尺寸", (3.32 if price >= 10.0 else 2.05)
            elif is_large:
                tier, base_fba = "大號標準尺寸", (5.42 if price >= 10.0 else 3.35)
            else:
                tier, base_fba = "大件尺寸", 9.73

            # 費用計算
            comm_rate = 0.16 if "16%" in category else 0.18
            referral_fee = price * comm_rate
            purchase_usd = cost_rmb / 6.0
            fba_head = 3.0 if "FBA" in mode else 0.0
            fba_ship = (base_fba * 1.05) if "FBA" in mode else 0.0
            fbm_ship = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            
            total_cost = purchase_usd + referral_fee + fba_head + fba_ship + fbm_ship
            profit = price - total_cost
            
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率", f"{(profit/price)*100:.2f}%")
            st.info(f"📍 **系統判定**：{tier}")
            with st.expander("明細"):
                st.write(f"🎫 佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode: st.write(f"📦 FBA配送(含緩衝): ${fba_ship:.3f}")
                else: st.write(f"📮 FBM配送費: ${fbm_ship:.2f}")

    # --- 📊 模組 2: 市場調研 (保留) ---
    with tabs[1]:
        st.header("📊 市場與競品調研")
        asin_input = st.text_input("ASIN / 關鍵字")
        st.button("啟動調研")

    # --- 🖼️ 模組 3: 渲染 (保留) ---
    with tabs[2]:
        st.header("🖼️ 場景批量渲染")
        st.file_uploader("上傳背景與PNG", accept_multiple_files=True)
        st.button("執行渲染")

    # --- 📦 模組 4: 智能備貨管理 (完整恢復並鎖定) ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        st.info("💡 備貨公式：(採購 + 運輸 + 安全緩衝) × 日銷 - 庫存")
        
        r1, r2, r3 = st.columns(3)
        with r1: daily_s = st.number_input("預估日銷量 (Pcs)", value=20)
        with r2: prod_t = st.number_input("生產週期 (天)", value=7)
        with r3: ship_t = st.number_input("運輸週期 (天)", value=30)
        
        r4, r5, r6 = st.columns(3)
        with r4: safe_t = st.number_input("安全緩衝 (天)", value=15)
        with r5: cur_stock = st.number_input("現有總庫存 (FBA+在途)", value=200)
        with r6: min_moq = st.number_input("最小起訂量 (MOQ)", value=100)
        
        # 計算邏輯
        theo_order = max(0, int((prod_t + ship_t + safe_t) * daily_s - cur_stock))
        act_order = theo_order if theo_order >= min_moq else (min_moq if theo_order > 0 else 0)
        
        st.divider()
        res1, res2, res3 = st.columns(3)
        with res1: st.metric("理論建議備貨", f"{theo_order} Pcs")
        with res2: 
            st.metric("建議下單量 (含MOQ)", f"{act_order} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True)
        with res3: st.metric("庫存支撐天數", f"{int(cur_stock/daily_s if daily_s > 0 else 0)} 天")
