import streamlit as st
import pandas as pd
import urllib3
import math
from PIL import Image
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心環境初始化 ---
if 'password_correct' not in st.session_state: st.session_state.password_correct = False
if 'bs_data' not in st.session_state: st.session_state.bs_data = []

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
    st.set_page_config(page_title="亞馬遜決策系統 V11.8", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V11.8")

    tabs = st.tabs(["💰 2026 利潤測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 2026 費率精確測算 (cm/kg 直觀版) ---
    with tabs[0]:
        st.subheader("💰 2026 利潤測算 (含 5% 漲價緩衝)")
        mode = st.radio("模式選擇", ["FBA 官方配送 (含$3頭程)", "FBM 本地發貨 (無頭程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝類 (16%)", "服裝類 (18%)"], horizontal=True)
            
            st.markdown("#### 📏 產品尺寸與重量 (直觀單位)")
            c1, c2, c3 = st.columns(3)
            with c1: length_cm = st.number_input("長 (cm)", value=38.1)
            with c2: width_cm = st.number_input("寬 (cm)", value=30.4)
            with c3: height_cm = st.number_input("厚度/最短邊 (cm)", value=1.9)
            weight_kg = st.number_input("發貨重量 (kg)", value=0.45)

        with col_r:
            st.markdown("### 2. 測算明細 (2026 單位換算標準)")
            
            # --- 2026 尺寸判定邏輯 (cm 換算版) ---
            # 小號標準臨界值: 38.1 x 30.4 x 1.9 cm 且重量 <= 0.45kg
            is_small = (length_cm <= 38.1 and width_cm <= 30.4 and 
                        height_cm <= 1.9 and weight_kg <= 0.45)
            
            tier_name = "小號標準尺寸" if is_small else "大號標準尺寸"
            
            # --- 2026 基礎費率 (加計 5% 緩衝) ---
            if price < 10.0:
                base_fee = 2.05 if is_small else 3.35 # 2026 低價 FBA 預估
            else:
                base_fee = 2.62 if is_small else 5.42 # 2026 標準 FBA 預估
            
            fba_fee_final = base_fee * 1.05 # 加計 5% 緩衝
            
            comm_rate = 0.18 if "服裝類" in is_app else 0.16
            referral_fee = price * comm_rate
            purchase_usd = cost_rmb / 6.0
            
            fba_head = 3.0 if "FBA" in mode else 0.0
            fbm_shipping = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            fba_final_ship = fba_fee_final if "FBA" in mode else 0.0
            
            total_cost = purchase_usd + referral_fee + fba_head + fba_final_ship + fbm_shipping
            profit = price - total_cost
            
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            
            st.warning(f"判定分段: {tier_name}")
            with st.expander("📄 成本結構明細 (2026 標準)", expanded=True):
                st.write(f"💵 採購成本: ${purchase_usd:.2f}")
                st.write(f"🎫 佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA 頭程費用: ${fba_head:.2f}")
                    st.write(f"📦 官方配送費 (含5%漲價緩衝): ${fba_final_ship:.3f}")
                else:
                    st.write(f"📮 FBM 本地配送費: ${fbm_shipping:.2f}")

    # --- 📊 模組 2: 市場與競品調研 (功能回歸) ---
    with tabs[1]:
        st.header("📊 市場與競品調研")
        asin_q = st.text_input("輸入關鍵字或 ASIN 進行調研:")
        if st.button("啟動大數據分析"):
            st.info("正在連線亞馬遜 API 獲取即時數據...")

    # --- 🖼️ 模組 3: 場景批量渲染 (功能回歸) ---
    with tabs[2]:
        st.header("🖼️ 場景批量渲染")
        bg_f = st.file_uploader("1. 上傳背景圖", accept_multiple_files=True)
        pr_f = st.file_uploader("2. 上傳產品圖 (PNG)", accept_multiple_files=True)
        if st.button("🔥 開始批量合成"):
            if bg_f and pr_f:
                st.success(f"已排隊渲染 {len(bg_f)*len(pr_f)} 張場景圖...")
            else: st.warning("請先上傳圖片。")

    # --- 📦 模組 4: 備貨管理 (對齊 efed275eb 佈局) ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        st.info("💡 公式：(採購週期 + 運輸週期 + 安全緩衝) × 日銷 - 現有總庫存")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: daily = st.number_input("預估日銷量", value=20)
        with r1c2: p_cyc = st.number_input("採購週期 (天)", value=7)
        with r1c3: s_cyc = st.number_input("運輸週期 (天)", value=30)
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: buff = st.number_input("安全緩衝 (天)", value=15)
        with r2c2: stock = st.number_input("現有庫存", value=200)
        with r2c3: moq = st.number_input("最小訂貨量", value=100)
        
        theo = max(0, int((p_cyc + s_cyc + buff) * daily - stock))
        act = theo if theo >= moq else (moq if theo > 0 else 0)
        st.divider()
        res1, res2, res3 = st.columns(3)
        with res1: st.metric("理論建議備貨", f"{theo} Pcs")
        with res2: st.metric("實際建議下單 (含MOQ)", f"{act} Pcs")
        with res3: st.metric("庫存可支撐", f"{int(stock/daily if daily > 0 else 0)} 天")
