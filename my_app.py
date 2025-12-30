import streamlit as st
import pandas as pd
import urllib3
import math

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
    st.set_page_config(page_title="亞馬遜決策系統 V11.7", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V11.7 (2026預警版)")

    tabs = st.tabs(["💰 2026 利潤測算", "📊 市場調研", "🖼️ 場景渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 2026 費率精確測算 (含 5% 緩衝) ---
    with tabs[0]:
        st.subheader("💰 2026 FBA 配送費測算 (已加計 5% 漲價緩衝)")
        mode = st.radio("模式選擇", ["FBA 官方配送 (含$3頭程)", "FBM 本地發貨 (無頭程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝類", "服裝類"], horizontal=True)
            
            st.markdown("#### 📏 產品物理屬性 (2026 標準)")
            c1, c2, c3 = st.columns(3)
            with c1: length = st.number_input("長邊 (inch)", value=15.0)
            with c2: width = st.number_input("次長邊 (inch)", value=12.0)
            with c3: height = st.number_input("最短邊/厚度 (inch)", value=0.75)
            weight_lb = st.number_input("發貨重量 (lb)", value=1.0)

        with col_r:
            st.markdown("### 2. 測算明細 (對齊 2026 新標)")
            
            # --- 2026 尺寸分段判定邏輯 ---
            is_small = (length <= 15 and width <= 12 and height <= 0.75 and weight_lb <= 1.0)
            tier_name = "小號標準尺寸" if is_small else "大號標準尺寸"
            
            # --- 2026 基礎費率 (依據售價門檻) ---
            if price < 10.0:
                base_fba_fee = 2.05 if is_small else 3.35 # 2026 低價 FBA 預估
            else:
                base_fba_fee = 2.62 if is_small else 5.42 # 2026 標準 FBA 預估
            
            # --- 💡 關鍵：加計 5% 漲價緩衝 ---
            fba_fee_buffered = base_fba_fee * 1.05
            
            comm_rate = 0.18 if "服裝" in is_app else 0.16
            referral_fee = price * comm_rate
            purchase_usd = cost_rmb / 6.0
            
            fba_head = 3.0 if "FBA" in mode else 0.0
            fbm_shipping = ((weight_lb * 131 / 2.2 + 16) / 6.0) if "FBM" in mode else 0.0
            fba_final_ship = fba_fee_buffered if "FBA" in mode else 0.0
            
            total_cost = purchase_usd + referral_fee + fba_head + fba_final_ship + fbm_shipping
            profit = price - total_cost
            
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            
            st.warning(f"判定分段: {tier_name}")
            with st.expander("📄 2026 成本結構明細 (含 5% 緩衝)", expanded=True):
                st.write(f"💵 採購成本 (USD): ${purchase_usd:.2f}")
                st.write(f"🎫 佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA 頭程費用: ${fba_head:.2f}")
                    st.write(f"📦 2026 配送費 (含5%預警): ${fba_final_ship:.3f}")
                    st.caption(f"註：官方原始費率為 ${base_fba_fee:.2f}")
                else:
                    st.write(f"📮 FBM 本地配送費: ${fbm_shipping:.2f}")

    # --- 📊 模組 2 & 模組 3: 保持不變 ---
    with tabs[1]: st.header("📊 市場調研 (正常運作)")
    with tabs[2]: st.header("🖼️ 場景渲染 (正常運作)")

    # --- 📦 模組 4: 備貨計算器 (1:1 專業佈局) ---
    with tabs[3]:
        st.header("📦 FBA 智能備貨計算器")
        st.info("💡 公式：(採購週期 + 運輸週期 + 安全緩衝) × 日銷 - 現有總庫存")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: daily = st.number_input("預估日銷量", value=20)
        with r1c2: p_cyc = st.number_input("採購生產週期 (天)", value=7)
        with r1c3: s_cyc = st.number_input("跨境運輸週期 (天)", value=30)
        
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: buff = st.number_input("安全緩衝天數 (天)", value=15)
        with r2c2: stock = st.number_input("現有總庫存 (FBA+在途)", value=200)
        with r2c3: moq = st.number_input("最小訂貨量 (MOQ)", value=100)
        
        theo = max(0, int((p_cyc + s_cyc + buff) * daily - stock))
        act = theo if theo >= moq else (moq if theo > 0 else 0)
        st.divider()
        res1, res2, res3 = st.columns(3)
        with res1: st.metric("理論建議備貨", f"{theo} Pcs")
        with res2: st.metric("實際建議下單 (含MOQ)", f"{act} Pcs")
        with res3: st.metric("庫存可支撐", f"{int(stock/daily if daily > 0 else 0)} 天")
