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

# --- ⚙️ 全局配置中心 ---
RAINFOREST_KEY = "40048B89139943E8B27B30A041F3A9BE"
DEEPSEEK_KEY = "sk-ce1493f77bd44bc19ee7c225aca95721"
SAFE_MARGIN = 1.05        # FBA 5% 漲價緩衝
FIXED_EXCHANGE = 6.0      # 本地發貨固定匯率
FIXED_HEAD_SHIP = 3.0     # FBA 固定頭程 3 USD
COMMISSION_NON_APP = 0.16 # 非服裝佣金 16%
COMMISSION_APP = 0.18     # 服裝類佣金 18%

st.set_page_config(page_title="亞馬遜全維度決策系統 V9.9", layout="wide")

# 初始化 Session State
if 'scenes_config' not in st.session_state: st.session_state.scenes_config = {}
if 'bs_data' not in st.session_state: st.session_state.bs_data = None
if 'nr_data' not in st.session_state: st.session_state.nr_data = None
if 'cat_report' not in st.session_state: st.session_state.cat_report = None
if 'asin_report' not in st.session_state: st.session_state.asin_report = None

# --- 🛠️ 通用工具函數 ---
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

# --- 🚀 UI 標籤頁導航 ---
main_tabs = st.tabs(["💰 利潤與運費測算", "📊 市場與競品調研", "🖼️ 場景批量渲染", "📦 智能備貨管理"])

# --- 💰 模組 1: 利潤與運費測算 (對齊 2026 官方與本地階梯) ---
with main_tabs[0]:
    st.header("💰 2026 亞馬遜雙模式測算中心")
    mode = st.radio("發貨模式選擇", ["FBA 配送 (2026 官方標準)", "本地發貨 (精確階梯運費)"], horizontal=True)
    
    col_in, col_res = st.columns([1, 1.2])
    with col_in:
        st.subheader("1. 成本參數錄入")
        price = st.number_input("產品售價 ($)", value=19.99, key="p_price_v99")
        unit_cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0, key="p_cost_v99")
        is_app = st.radio("類目性質", ["非服裝 (Non-Apparel)", "服裝類 (Apparel)"], horizontal=True, key="p_cat_v99")
        
        if mode == "FBA 配送 (2026 官方標準)":
            st.info(f"🚚 已自動計入固定頭程：**{FIXED_HEAD_SHIP} USD**")
            l_cm = st.number_input("長 (cm)", value=25.4)
            w_cm = st.number_input("寬 (cm)", value=15.2)
            h_cm = st.number_input("高 (cm)", value=2.0)
            weight_kg = st.number_input("產品重量 (kg)", value=0.5, key="fba_w_v99")
        else:
            local_kg = st.number_input("產品重量 (kg)", value=0.5, key="local_w_v99")
            st.info(f"💡 匯率固定: **{FIXED_EXCHANGE}** | 佣金率: **{COMMISSION_APP*100 if is_app=='服裝類 (Apparel)' else COMMISSION_NON_APP*100}%**")

    with col_res:
        st.subheader("2. 測算明細判定")
        comm_rate = COMMISSION_APP if is_app == "服裝類 (Apparel)" else COMMISSION_NON_APP
        referral_fee = price * comm_rate
        cost_usd = unit_cost_rmb / FIXED_EXCHANGE
        
        if mode == "FBA 配送 (2026 官方標準)":
            l_in, w_in, h_in = l_cm/2.54, w_cm/2.54, h_cm/2.54
            wt_lb = weight_kg * 2.204
            dims = sorted([l_in, w_in, h_in], reverse=True)
            # 2026 官方尺寸分段判定
            if dims[0]<=15 and dims[1]<=12 and dims[2]<=0.75 and wt_lb<=1: tier = "小標準尺寸"
            elif dims[0]<=18 and dims[1]<=14 and dims[2]<=8 and wt_lb<=20: tier = "大標準尺寸"
            elif dims[0]<=37 and dims[1]<=28 and dims[2]<=20 and wt_lb<=50: tier = "小號大件"
            elif dims[0]<=59 and dims[1]<=33 and dims[2]<=33 and wt_lb<=50: tier = "大號大件"
            else: tier = "超大件 (Oversize)"

            # 2026 費率邏輯
            if "標準" in tier:
                base_fba = 2.43 if price < 10 else (3.40 if price > 50 else 2.62) if "小標準" in tier else (3.69 if price < 10 else 5.42)
            else: base_fba = 9.80
            
            if is_app == "服裝類 (Apparel)": base_fba += 0.50
            fba_fee_final = base_fba * SAFE_MARGIN
            total_logistics = fba_fee_final + FIXED_HEAD_SHIP
        else:
            # 本地階梯運費公式
            def calculate_local(kg):
                if kg <= 0.1: return 144.0, 20.0
                elif kg <= 0.2: return 139.0, 18.0
                elif kg <= 0.45: return 133.0, 16.0
                elif kg <= 0.7: return 131.0, 16.0
                else: return 131.0, 9.0
            u_p, r_f = calculate_local(local_kg)
            total_logistics = ((local_kg * u_p) + r_f) / FIXED_EXCHANGE
            tier = "自發貨階梯計費"

        net_profit = price - cost_usd - referral_fee - total_logistics
        margin = (net_profit / price) * 100 if price > 0 else 0
        
        st.metric("判定官方分段", tier)
        st.success(f"### 預估純利: **${net_profit:.2f}**")
        st.metric("毛利率 (%)", f"{margin:.2f}%")
        with st.expander("📝 查看詳細對帳清單"):
            st.write(f"* 佣金率: {comm_rate*100}% | 佣金: ${referral_fee:.2f}")
            st.write(f"* 採購成本: ${cost_usd:.2f}")
            st.write(f"* 物流總計: ${total_logistics:.2f}")

# --- 📊 模組 2: 市場與競品調研 (全功能保留) ---
with main_tabs[1]:
    st.header("📊 市場與競品深挖")
    c_t1, c_t2 = st.tabs(["類目分析", "單品 ASIN 評價分析"])
    with c_t1:
        cat_input = st.text_input("輸入類目 ID 或搜尋詞:", key="cat_tab")
        if st.button("啟動類目調研") and cat_input:
            with st.spinner("採集數據中..."):
                def fetch_data(t, val):
                    is_id = val.isdigit()
                    p = {"api_key": RAINFOREST_KEY, "amazon_domain": "amazon.com", "type": t if is_id else "search"}
                    if is_id: p["category_id"] = val
                    else: p["search_term"] = val
                    try:
                        r = requests.get("https://api.rainforestapi.com/request", params=p, verify=False).json()
                        raw = r.get(t) or r.get("search_results") or r.get("bestsellers") or []
                        return [parse_item(x, i) for i, x in enumerate(raw[:20])]
                    except: return []
                st.session_state.bs_data = fetch_data("bestsellers", cat_input)
                st.session_state.nr_data = fetch_data("new_releases", cat_input)
                if st.session_state.bs_data:
                    prompt = f"分析數據：熱賣榜{str(st.session_state.bs_data[:5])}, 新品榜{str(st.session_state.nr_data[:5])}。"
                    res = requests.post("https://api.deepseek.com/chat/completions", headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, 
                                      json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}).json()
                    st.session_state.cat_report = res['choices'][0]['message']['content']
        if st.session_state.bs_data:
            col1, col2 = st.columns(2)
            cfg = {"跳轉": st.column_config.LinkColumn("🔗"), "標題": st.column_config.TextColumn("標題", width="large")}
            col1.subheader("🔥 熱賣榜"); col1.dataframe(st.session_state.bs_data, column_config=cfg, hide_index=True)
            col2.subheader("✨ 新品榜"); col2.dataframe(st.session_state.nr_data, column_config=cfg, hide_index=True)
            if st.session_state.cat_report: st.markdown(st.session_state.cat_report)

    with c_t2:
        asin_input = st.text_input("輸入 ASIN:", key="asin_tab")
        if st.button("啟動評價分析") and asin_input:
            with st.spinner("分析中..."):
                try:
                    p_url = f"https://api.rainforestapi.com/request?api_key={RAINFOREST_KEY}&type=product&asin={asin_input}&amazon_domain=amazon.com"
                    p_res = requests.get(p_url, verify=False).json().get("product", {})
                    rev_text = "\n".join([f"評分:{r.get('rating')} 內容:{r.get('body')[:200]}" for r in p_res.get("top_reviews", [])[:10]])
                    prompt = f"針對 {asin_input} 評價分析痛點：\n{rev_text}"
                    ai_res = requests.post("https://api.deepseek.com/chat/completions", headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, 
                                          json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}).json()
                    st.session_state.asin_report = ai_res['choices'][0]['message']['content']
                    st.markdown(st.session_state.asin_report)
                except: st.error("分析失敗")

# --- 🖼️ 模組 3: 場景批量渲染 (全功能保留) ---
with main_tabs[2]:
    st.header("🖼️ 場景批量渲染 (針對靜電膜優化)")
    col_a, col_b = st.columns(2)
    with col_a: bg_files = st.file_uploader("1. 上傳場景底圖", type=["jpg", "png"], accept_multiple_files=True)
    with col_b: pr_files = st.file_uploader("2. 上傳產品 PNG", type=["png"], accept_multiple_files=True)
    film_opacity = st.slider("玻璃膜透明度 %", 10, 100, 85)
    if bg_files:
        for bg in bg_files:
            if bg.name not in st.session_state.scenes_config:
                tw, th = load_img(bg).size
                st.session_state.scenes_config[bg.name] = {"x": tw//2, "y": th//2, "s": 40}
            with st.expander(f"📍 座標鎖定：{bg.name}"):
                conf = st.session_state.scenes_config[bg.name]
                c1, c2, c3 = st.columns(3)
                conf['x'] = c1.number_input("X", 0, 10000, conf['x'], key=f"x_{bg.name}")
                conf['y'] = c2.number_input("Y", 0, 10000, conf['y'], key=f"y_{bg.name}")
                conf['s'] = c3.slider("比例", 5, 200, conf['s'], key=f"s_{bg.name}")
                if pr_files:
                    main_bg = load_img(bg); bw, bh = main_bg.size; pre_r = 600/bw
                    pre_bg = main_bg.resize((600, int(bh*pre_r)), Image.Resampling.NEAREST)
                    sample_p = load_img(pr_files[0])
                    if film_opacity < 100: sample_p.putalpha(sample_p.split()[3].point(lambda i: i * (film_opacity/100)))
                    snw, snh = int(sample_p.width*(conf['s']/100)*pre_r), int(sample_p.height*(conf['s']/100)*pre_r)
                    pre_bg.paste(sr:=sample_p.resize((snw, snh), Image.Resampling.NEAREST), (int(conf['x']*pre_r - snw//2), int(conf['y']*pre_r - snh//2)), sr)
                    st.image(pre_bg, width=400)
        if bg_files and pr_files and st.button("🔥 啟動批量合成"):
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for bf in bg_files:
                    base = load_img(bf); conf = st.session_state.scenes_config[bf.name]
                    for pf in pr_files:
                        p = load_img(pf); nw, nh = int(p.width*(conf['s']/100)), int(p.height*(conf['s']/100))
                        if film_opacity < 100: p.putalpha(p.split()[3].point(lambda i: i * (film_opacity/100)))
                        p_res = p.resize((nw, nh), Image.Resampling.LANCZOS); canvas = base.copy()
                        canvas.paste(p_res, (conf['x'] - nw//2, conf['y'] - nh//2), p_res)
                        buf = io.BytesIO(); canvas.convert("RGB").save(buf, format='JPEG', quality=95)
                        zf.writestr(f"{bf.name.split('.')[0]}_{pf.name}.jpg", buf.getvalue())
            st.download_button("📥 下載全套圖片 (.zip)", z_buf.getvalue(), file_name="Mockups.zip", use_container_width=True)

# --- 📦 模組 4: 智能備貨管理 (全功能保留) ---
with main_tabs[3]:
    st.header("📦 智能補貨計算模型")
    col1, col2, col3 = st.columns(3)
    s7, o7 = col1.number_input("7日銷量", value=70), col1.number_input("7日斷貨天", value=0)
    s15, o15 = col2.number_input("15日銷量", value=150), col2.number_input("15日斷貨天", value=0)
    s30, o30 = col3.number_input("30日銷量", value=300), col3.number_input("30日斷貨天", value=0)
    wd = ((s7/(7-o7) if 7-o7>0 else 0)*0.5 + (s15/(15-o15) if 15-o15>0 else 0)*0.3 + (s30/(30-o30) if 30-o30>0 else 0)*0.2)
    st.info(f"💡 加權日銷：**{wd:.2f}** Pcs/天")
    ship_t = st.number_input("運輸+生產週期 (天)", value=45)
    fba_s = st.number_input("FBA 當前庫存", value=200)
    st.metric("建議下單總量", f"{max(0, int(wd * ship_t * 1.15 - fba_s))} Pcs")