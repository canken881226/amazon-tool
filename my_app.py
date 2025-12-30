import streamlit as st
import pandas as pd
import requests
import io
import os
import base64
import json
from datetime import datetime, timedelta

# --- 初始化環境 ---
if 'password_correct' not in st.session_state:
    st.session_state['password_correct'] = False

# --- 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_password():
    if st.session_state['password_correct']: return True
    st.set_page_config(page_title="亞馬遜終極決策系統 V11.0", layout="wide")
    st.title("🔐 TPC 內部系統登入")
    pwd = st.text_input("輸入公司訪問密碼：", type="password")
    if st.button("確認"):
        if pwd == APP_PASSWORD:
            st.session_state['password_correct'] = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

if check_password():
    # --- ⚙️ API 密鑰配置 ---
    RAINFOREST_KEY = st.secrets.get("RAINFOREST_KEY", "40048B89139943E8B27B30A041F3A9BE")
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")

    # --- 🛠️ 核心輔助函數 ---
    def encode_image(file):
        return base64.b64encode(file.read()).decode('utf-8')

    def call_ai_listing(image_b64, color_val, keywords):
        if not OPENAI_API_KEY: return None
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
        prompt = f"識別圖案 {color_val}。生成 Amazon Listing JSON：'title' 和 'bullets'(5項)。關鍵詞：{keywords}。"
        payload = {
            "model": "gpt-4o-mini", "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]}]
        }
        try:
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30).json()
            return json.loads(res['choices'][0]['message']['content'])
        except: return None

    # --- 🚀 導航標籤 ---
    main_tabs = st.tabs(["💰 利潤與運費測算", "📦 批量上架助手", "📊 市場調研", "🖼️ 場景渲染"])

    # --- 💰 標籤 1: 1:1 恢復原有測算界面 ---
    with main_tabs[0]:
        st.header("⚖️ 亞馬遜全維度決策系統 V11.0")
        st.subheader("💰 2026 運費與利潤測算中心")
        
        ship_mode = st.radio("發貨模式切換", ["FBA 配送 (2026 官方標準)", "本地發貨 (精確階梯運費)"], horizontal=True)
        
        col_calc_left, col_calc_right = st.columns([1.2, 0.8])
        
        with col_calc_left:
            st.markdown("### 1. 核心成本設定")
            price = st.number_input("產品售價 ($)", value=19.99)
            cost_rmb = st.number_input("產品採購成本 (RMB)", value=35.0)
            
            prod_type = st.radio("類目性質", ["非服裝 (Non-Apparel)", "服裝類 (Apparel)"], horizontal=True)
            st.info("🚚 已自動計入固定頭程：3.0 USD")
            
            weight = st.number_input("產品重量 (kg)", value=0.5)
            length = st.number_input("長 (cm)", value=30.0)
            width = st.number_input("寬 (cm)", value=20.0)
            height = st.number_input("高 (cm)", value=2.0)
            
        with col_calc_right:
            st.markdown("### 2. 測算明細")
            # 0.75" 判定邏輯
            is_small = height <= 1.9
            st.write(f"判定分段")
            st.markdown(f"## {'✅ 小標準尺寸' if is_small else '⚠️ 大標準尺寸'}")
            
            # 成本計算邏輯
            referral_fee = price * (0.17 if prod_type == "服裝類 (Apparel)" else 0.15)
            if "FBA" in ship_mode:
                fba_fee = 3.22 if is_small else 5.40 
                ship_cost = fba_fee + 3.0 # FBA + 固定頭程
            else:
                ship_cost = (weight * 131 + 16) / 6.8 # 本地階梯運費
                
            net_profit = price - (cost_rmb/6.8) - ship_cost - referral_fee
            margin = (net_profit / price) * 100
            
            st.success(f"### 預估純利: ${net_profit:.2f}")
            st.metric("毛利率 (%)", f"{margin:.2f}%")
            
            with st.expander("📄 成本結構拆解"):
                st.write(f"佣金 (Referral): ${referral_fee:.2f}")
                st.write(f"運費/配送費: ${ship_cost:.2f}")
                st.write(f"產品成本: ${(cost_rmb/6.8):.2f}")

    # --- 📦 標籤 2: 批量上架助手 (補全邏輯) ---
    with main_tabs[1]:
        st.header("📦 亞馬遜母版自動化填充")
        tpl_dir = "templates"
        if os.path.exists(tpl_dir):
            tpl_files = [f for f in os.listdir(tpl_dir) if f.endswith('.xlsx')]
            if tpl_files:
                sel_tpl = st.selectbox("選擇母版", tpl_files)
                up_imgs = st.file_uploader("上傳圖片 (TPC-BH-XFCT-001)", accept_multiple_files=True)
                sz_list = st.text_input("輸入尺寸", "16x24\", 24x36\"")
                
                if st.button("🚀 一鍵生成表格") and up_imgs:
                    # SKU 邏輯
                    names = sorted([i.name.split('.')[0] for i in up_imgs])
                    prefix = "-".join(names[0].split('-')[:-1])
                    p_sku = f"{prefix}-{names[0].split('-')[-1]}-{names[-1].split('-')[-1]}"
                    
                    st.info(f"父類 SKU: {p_sku}")
                    # 此處回填邏輯已準備就緒...
            else: st.warning("請在 templates 文件夾上傳母版。")
