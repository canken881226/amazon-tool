import streamlit as st
import pandas as pd
import requests
import urllib3

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心環境初始化 (防止任何變量報錯) ---
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'bs_data' not in st.session_state:
    st.session_state.bs_data = []

# --- 2. 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_login():
    if st.session_state.password_correct:
        return True
    st.set_page_config(page_title="🔐 登入", layout="centered")
    st.title("🔐 TPC 內部系統登入")
    pwd = st.text_input("輸入訪問密碼：", type="password")
    if st.button("確認"):
        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤")
    return False

if check_login():
    st.set_page_config(page_title="亞馬遜決策系統 V10.5", layout="wide")
    st.title("⚖️ 亞馬遜全維度決策系統 V10.5")

    # --- 3. 導航標籤 (保留測算、調研、以及您要加回的備貨管理) ---
    tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "📦 智能備貨管理"])

    # --- 💰 模組 1: 利潤測算 (保持穩定) ---
    with tabs[0]:
        st.subheader("💰 2026 運費與利潤測算中心")
        col_in, col_res = st.columns([1.2, 0.8])
        with col_in:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            H_cm = st.number_input("厚度 (cm)", value=2.0)
            st.info("🚚 已計入固定頭程：3.0 USD")
        with col_res:
            st.markdown("### 2. 測算明細")
            is_small = H_cm <= 1.9
            st.markdown(f"## 判定: {'✅ 小標準' if is_small else '⚠️ 大標準'}")
            ship = (3.22 + 3.0) if is_small else (5.40 + 3.0)
            profit = price - (cost_rmb/6.0) - ship - (price*0.16)
            st.success(f"### 預估純利: ${profit:.2f}")
            with st.expander("📄 成本結構拆解"):
                st.write(f"配送費(含頭程): ${ship:.2f}")

    # --- 📊 模組 2: 市場調研 (保持穩定) ---
    with tabs[1]:
        st.header("📊 市場競品調研")
        st.text_input("搜尋關鍵字")

    # --- 📦 模組 3: 補回您確認過的備貨公式 ---
    with tabs[2]:
        st.header("📦 智能備貨管理系統")
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 銷售與週期")
            s7 = st.number_input("最近 7 日總銷量", value=70, help="用於計算平均日銷量")
            lead_time = st.number_input("採購+物流總天數 (Lead Time)", value=45)
        with c2:
            st.subheader("📥 庫存狀態")
            current_stock = st.number_input("當前 FBA 可用庫存", value=200)
            safe_days = st.number_input("安全庫存天數 (Buffer)", value=15)

        # --- 核心備貨公式邏輯 ---
        daily_avg = s7 / 7  # 平均日銷量
        
        if daily_avg > 0:
            # 1. 計算當前庫存還能賣幾天
            stock_days = current_stock / daily_avg
            # 2. 計算建議下單量 = (週期 + 安全天數) * 日均銷量 - 現有庫存
            suggest_order = (lead_time + safe_days) * daily_avg - current_stock
            
            st.divider()
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("日均銷量預估", f"{daily_avg:.1f} Pcs")
            with m2:
                # 判斷是否會斷貨：如果庫存天數小於物流天數，則顯示紅色警告
                color = "normal" if stock_days > lead_time else "inverse"
                st.metric("庫存預計可售天數", f"{int(stock_days)} 天", 
                          delta=f"{int(stock_days - lead_time)} 天餘裕", delta_color=color)
            with m3:
                st.metric("建議本次下單量", f"{max(0, int(suggest_order))} Pcs")

            # --- 警告與建議 ---
            if stock_days < lead_time:
                st.error(f"⚠️ 嚴重警告：庫存將在 {int(stock_days)} 天內耗盡，而下一批貨需要 {lead_time} 天才能抵達！")
                st.warning(f"🚨 預計會出現 {int(lead_time - stock_days)} 天的缺貨期，請立即處理！")
            elif stock_days < (lead_time + safe_days):
                st.warning("⚡ 提醒：庫存已進入安全區警戒線，建議近期安排補貨。")
            else:
                st.success("✅ 目前庫存水位充足，暫無斷貨風險。")
        else:
            st.info("請在左側輸入 7 日銷量數據，系統將自動計算備貨建議。")
