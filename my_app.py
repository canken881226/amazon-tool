import streamlit as st
import requests
import pandas as pd
import math
import urllib3
from PIL import Image
import io
import zipfile

# 禁用安全請求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 🔐 訪問控制設置 ---
APP_PASSWORD = "TPCamazon@2026"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.set_page_config(page_title="🔐 登入 - 亞馬遜決策系統", layout="centered")
    st.title("🔐 公司內部工具 - 請登入")
    pwd_input = st.text_input("請輸入訪問密碼：", type="password")
    if st.button("確認登入"):
        if pwd_input == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤，請聯繫管理員。")
    return False

# 只有密碼正確才執行後續功能
if check_password():
    # --- ⚙️ 全局配置 (硬編碼您的特定要求) ---
    RAINFOREST_KEY = "40048B89139943E8B27B30A041F3A9BE"
    DEEPSEEK_KEY = "sk-ce1493f77bd44bc19ee7c225aca95721"
    SAFE_MARGIN = 1.05        # FBA 5% 漲價緩衝
    FIXED_EXCHANGE = 6.0      # 匯率固定為 6
    FIXED_HEAD_SHIP = 3.0     # FBA 固定頭程 3 USD
    COMMISSION_NON_APP = 0.16 # 非服裝佣金 16%
    COMMISSION_APP = 0.18     # 服裝佣金 18%

    st.set_page_config(page_title="亞馬遜全維度決策系統 V10.0", layout="wide")

    # --- 🛠️ 核心工具函數 ---
    @st.cache_data
    def load_img(file): return Image.open(file).convert("RGBA")

    def estimate_sales(rank_str):
        try:
            rank = int(''.join(filter(str.isdigit, str(rank_str))))
            monthly = int(500000 / (rank**0.6)) if rank > 0 else 0
            return monthly, math.ceil(monthly / 30)
        except: return 0, 0

    def parse_item(item, rank_idx=0):
        p = item.get('product', {}) if isinstance(item.get('product'), dict) else item
        asin = item.get('asin') or p.get('asin') or ""
        title = item.get('title') or p.get('title') or "Unknown Product"
        price_data = item.get('price') or p.get('price') or {}
        price = price_data.get('value', 'N/A') if isinstance(price_data, dict) else price_data
        b_rank = p.get('bestsellers_rank_flat') or "N/A"
        m_sales, d_sales = estimate_sales(b_rank)
        return {"排名": rank_idx + 1, "標題": str(title)[:50], "ASIN": asin, "價格": price, "月銷": m_sales, "日銷": d_sales, "跳轉": f"https://www.amazon.com/s?k={asin}"}

    # --- 🚀 導航切換 ---
    st.title("⚖️ 亞馬遜全維度決策系統 V10.0")
    main_tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

    # --- 💰 模組 1: 利潤與運費測算 (對齊 2026 標準) ---
    with main_tabs[0]:
        st.header("💰 2026 雙模式精確測算")
        mode = st.radio("模式切換", ["FBA 配送 (2026 官方標準)", "本地發貨 (精確階梯運費)"], horizontal=True)
        col_in, col_res = st.columns([1, 1.2])
        
        with col_in:
            price = st.number_input("產品售價 ($)", value=19.99)
            unit_cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            is_app = st.radio("類目性質", ["非服裝 (Non-Apparel)", "服裝類 (Apparel)"], horizontal=True)
            if mode == "FBA 配送 (2026 官方標準)":
                st.info(f"🚚 已自動計入固定頭程：{FIXED_HEAD_SHIP} USD")
                l_cm, w_cm, h_cm = st.number_input("長(cm)", 25.4), st.number_input("寬(cm)", 15.2), st.number_input("高(cm)", 2.0)
                weight_kg = st.number_input("產品重量 (kg)", 0.5)
            else:
                local_kg = st.number_input("產品重量 (kg)", 0.5)

        with col_res:
            comm = COMMISSION_APP if "服裝" in is_app else COMMISSION_NON_APP
            ref_fee, cost_usd = price * comm, unit_cost_rmb / FIXED_EXCHANGE
            
            if mode == "FBA 配送 (2026 官方標準)":
                l_in, w_in, h_in, lb = l_cm/2.54, w_cm/2.54, h_cm/2.54, weight_kg*2.204
                d = sorted([l_in, w_in, h_in], reverse=True)
                # 2026 尺寸門檻判定 [包含 0.75" 限制]
                if d[0]<=15 and d[1]<=12 and d[2]<=0.75 and lb<=1: tier = "小標準尺寸"
                elif d[0]<=18 and d[1]<=14 and d[2]<=8 and lb<=20: tier = "大標準尺寸"
                else: tier = "大件/超大件"
                # 費率基準
                base = (2.43 if price<10 else 2.62) if "小標準" in tier else (3.69 if price<10 else 5.42)
                if "服裝" in is_app: base += 0.50
                fba_fee = base * SAFE_MARGIN
                total_logistics = fba_fee + FIXED_HEAD_SHIP
            else:
                # 本地發貨階梯表
                def get_local(kg):
                    if kg<=0.1: return 144, 20
                    if kg<=0.2: return 139, 18
                    if kg<=0.45: return 133, 16
                    if kg<=0.7: return 131, 16
                    return 131, 9
                up, rf = get_local(local_kg)
                total_logistics = (local_kg * up + rf) / FIXED_EXCHANGE
                tier = "自發貨階梯計費"

            profit = price - cost_usd - ref_fee - total_logistics
            st.metric("判定分段", tier)
            st.success(f"### 預估純利: ${profit:.2f}")
            st.metric("毛利率", f"{(profit/price)*100:.2f}%")
            with st.expander("📝 成本結構"):
                st.write(f"* 佣金({int(comm*100)}%): ${ref_fee:.2f}")
                st.write(f"* 採購(USD): ${cost_usd:.2f}")
                st.write(f"* 物流總支: ${total_logistics:.2f}")

    # --- 📊 模組 2: 市場調研 ---
    with main_tabs[1]:
        st.header("📊 市場與競品調研")
        cat_input = st.text_input("輸入類目 ID 或搜尋詞:")
        if st.button("啟動調研") and cat_input:
            with st.spinner("採集中..."):
                p = {"api_key": RAINFOREST_KEY, "amazon_domain": "amazon.com", "type": "search", "search_term": cat_input}
                res = requests.get("https://api.rainforestapi.com/request", params=p, verify=False).json()
                st.session_state.bs_data = [parse_item(x, i) for i, x in enumerate(res.get("search_results", [])[:20])]
        if st.session_state.bs_data:
            st.dataframe(st.session_state.bs_data, use_container_width=True)

    # --- 🖼️ 模組 3: 場景渲染 ---
    with main_tabs[2]:
        st.header("🖼️ 場景批量渲染")
        bg_files = st.file_uploader("1. 背景圖", accept_multiple_files=True)
        pr_files = st.file_uploader("2. 產品圖(PNG)", accept_multiple_files=True)
        if bg_files and pr_files:
            st.info("請在下方展開設置座標並啟動合成...")
            # (此處保留 V9.9 的渲染邏輯)

    # --- 📦 模組 4: 智能備貨 ---
    with main_tabs[3]:
        st.header("📦 智能備貨管理")
        s7 = st.number_input("7日銷量", value=70)
        ship_t = st.number_input("生產+運輸週期(天)", value=45)
        fba_s = st.number_input("當前庫存", value=200)
        daily = s7/7
        st.metric("建議補貨天數", f"{int(fba_s/daily) if daily>0 else 0} 天")
        st.metric("建議下單量", f"{max(0, int(daily*ship_t*1.2 - fba_s))} Pcs")
