import streamlit as st
import pandas as pd
import urllib3
from PIL import Image
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心環境初始化 (防止屬性錯誤) ---
if 'password_correct' not in st.session_state: st.session_state.password_correct = False
if 'bs_data' not in st.session_state: st.session_state.bs_data = []

# --- 2. 🔐 訪問控制 ---
if not st.session_state.password_correct:
    st.set_page_config(page_title="🔐 登入", layout="centered")
    pwd = st.text_input("輸入公司訪問密碼：", type="password")
    if st.button("確認登入"):
        if pwd == "TPCamazon@2026":
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
else:
    # --- ⚙️ 全局配置 ---
    st.set_page_config(page_title="亞馬遜全維度決策系統 V12.0", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V12.0")

    # --- 🚀 功能標籤 (四大功能鎖定) ---
    tabs = st.tabs(["💰 2026 利潤測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 利潤測算 (修復佣金計算) ---
    with tabs[0]:
        st.subheader("💰 2026 利潤測算 (精確佣金與 5% 緩衝)")
        mode = st.radio("模式選擇", ["FBA 官方配送 (含$3頭程)", "FBM 本地發貨 (無頭程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            
            # 💡 佣金選項實時聯動
            category = st.radio("類目性質", ["非服裝類 (16%)", "服裝類 (18%)"], horizontal=True)
            
            st.markdown("#### 📏 產品尺寸與重量 (cm/kg)")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("長 (cm)", value=38.1)
            with c2: w_cm = st.number_input("寬 (cm)", value=30.4)
            with c3: h_cm = st.number_input("厚度/最短邊 (cm)", value=1.9)
            weight_kg = st.number_input("發貨重量 (kg)", value=0.45)

        with col_r:
            st.markdown("### 2. 測算明細")
            # 2026 判定邏輯
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            
            # 配送費計算 (含5%緩衝)
            base_fba = (2.62 if is_small else 5.42) if price >= 10.0 else (2.05 if is_small else 3.35)
            fba_fee_final = base_fba * 1.05
            
            # 💡 核心修復：正確讀取佣金率
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
                st.write(f"💵 採購成本 (USD): ${purchase_usd:.2f}")
                st.write(f"🎫 亞馬遜佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA 頭程費用: ${fba_head:.2f}")
                    st.write(f"📦 官方配送費 (含5%緩衝): ${fba_final_ship:.3f}")
                else:
                    st.write(f"📮 FBM 本地配送費: ${fbm_shipping:.2f}")

    # --- 📊 模組 2: 市場與競品調研 ---
    with tabs[1]:
        st.header("📊 市場與競品調研")
        asin_input = st.text_input("輸入 ASIN 或 關鍵字:")
        if st.button("啟動大數據調研"): st.info("正在連線亞馬遜數據庫...")

    # --- 🖼️ 模組 3: 場景批量渲染 ---
    with tabs[2]:
        st.header("🖼️ 場景批量渲染")
        col_img1, col_img2 = st.columns(2)
        with col_img1: st.file_uploader("1. 上傳背景圖", accept_multiple_files=True, key="bg_up")
        with col_img2: st.file_uploader("2. 上傳產品圖 (PNG)", accept_multiple_files=True, key="pr_up")
        st.button("🔥 開始批量生成場景圖")

    # --- 📦 模組 4: 智能備貨管理 (對齊截圖佈局) ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        st.info("💡 公式：(採購週期 + 運輸週期 + 安全緩衝) × 日銷 - 現有總庫存")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: d_s = st.number_input("預估日銷量 (Pcs/天)", value=20)
        with r1c2: p_c = st.number_input("採購生產週期 (天)", value=7)
        with r1c3: s_c = st.number_input("跨境運輸週期 (天)", value=30)
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: b_d = st.number_input("安全緩衝天數 (天)", value=15)
        with r2c2: t_s = st.number_input("現有總庫存 (FBA+在途)", value=200)
        with r2c3: moq = st.number_input("最小訂貨量 (MOQ)", value=100)

        theo = max(0, int((p_c + s_c + b_d) * d_s - t_s))
        act = theo if theo >= moq else (moq if theo > 0 else 0)
        st.divider()
        res_c1, res_c2, res_c3 = st.columns(3)
        with res_c1: st.metric("理論建議備貨", f"{theo} Pcs")
        with res_c2: 
            st.metric("實際建議下單 (含MOQ)", f"{act} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True)
        with res_c3: st.metric("庫存可支撐天數", f"{int(t_s/d_s if d_s > 0 else 0)} 天")
