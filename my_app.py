import streamlit as st
import pandas as pd
import requests
import io
import os
import base64
import json
from datetime import datetime, timedelta

# --- 初始化 (防止 AttributeError) ---
if 'password_correct' not in st.session_state:
    st.session_state['password_correct'] = False

# --- 🔐 訪問控制 ---
APP_PASSWORD = "TPCamazon@2026"

def check_password():
    if st.session_state['password_correct']: return True
    st.set_page_config(page_title="亞馬遜全維度決策系統 V11.0", layout="wide")
    st.title("🔐 TPC 內部系統登入")
    pwd = st.text_input("請輸入密碼：", type="password")
    if st.button("確認"):
        if pwd == APP_PASSWORD:
            st.session_state['password_correct'] = True
            st.rerun()
        else: st.error("密碼錯誤")
    return False

if check_password():
    # --- ⚙️ API 密鑰配置 (從 Secrets 獲取) ---
    RAINFOREST_KEY = st.secrets.get("RAINFOREST_KEY", "")
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")

    # --- 🛠️ 輔助功能 ---
    def encode_image(file):
        return base64.b64encode(file.read()).decode('utf-8')

    def call_openai_listing(image_b64, color_val, keywords):
        if not OPENAI_API_KEY: return None
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
        prompt = f"識別圖中元素，生成亞馬遜 Listing：標題(含尺寸占位符), 5個五點描述。關鍵詞：{keywords}。以 JSON 返回，含 'title' 和 'bullets' (list)。"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]}],
            "response_format": { "type": "json_object" }
        }
        try:
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30).json()
            return json.loads(res['choices'][0]['message']['content'])
        except: return None

    # --- 🚀 導航標籤頁 ---
    tabs = st.tabs(["💰 利潤測算", "📦 批量上架助手", "📊 市場調研"])

    # --- 💰 模組 1: 利潤測算 (完全恢復 V10 邏輯) ---
    with tabs[0]:
        st.header("💰 2026 雙模式精確測算")
        mode = st.radio("模式切換", ["FBA 配送 (2026 官方標準)", "本地發貨 (精確階梯運費)"], horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("產品售價 ($)", value=19.99)
            cost = st.number_input("採購成本 (RMB)", value=35.0)
            weight = st.number_input("產品重量 (kg)", value=0.5)
            h = st.number_input("產品厚度 (cm)", value=2.0)
        
        # 0.75" 判定邏輯 (1.9cm)
        is_small = h <= 1.9
        
        if "FBA" in mode:
            fba_fee = 3.22 if is_small else 5.40 
            head_ship = 3.0
            total_cost = (cost/6.8) + fba_fee + head_ship + (price * 0.15)
        else:
            # 本地發貨階梯逻辑
            ship_fee = (weight * 131 + 16) / 6.8
            total_cost = (cost/6.8) + ship_fee + (price * 0.15)

        profit = price - total_cost
        st.metric("預估純利", f"${profit:.2f}")
        st.info(f"分段判定: {'✅ 小標準 (<=0.75\")' if is_small else '⚠️ 大標準 (>0.75\")'}")

    # --- 📦 模組 2: 批量上架助手 (完整補全版) ---
    with tabs[1]:
        st.header("📦 亞馬遜母版自動化填充")
        tpl_dir = "templates"
        
        if not os.path.exists(tpl_dir):
            st.error("❌ 找不到 templates 文件夾，請在 GitHub 創建。")
        else:
            tpl_files = [f for f in os.listdir(tpl_dir) if f.endswith(('.xlsx', '.xls'))]
            if not tpl_files:
                st.warning("請在 templates 文件夾內上傳 Excel 母版。")
            else:
                sel_tpl = st.selectbox("1. 選擇店鋪母版", tpl_files)
                imgs = st.file_uploader("2. 上傳圖案 (格式: TPC-BH-XFCT-001)", accept_multiple_files=True)
                sz_list = st.text_input("3. 尺寸 (如: 16x24\", 24x36\")", "16x24\", 24x36\"")
                keywords = st.text_input("4. SEO 關鍵詞", "home decor, canvas art")
                
                if st.button("🔥 一鍵生成上架表格") and imgs:
                    with st.spinner("AI 正在解析圖片並生成變體..."):
                        # SKU 匯總邏輯
                        names = sorted([i.name.split('.')[0] for i in imgs])
                        prefix = "-".join(names[0].split('-')[:-1])
                        p_sku = f"{prefix}-{names[0].split('-')[-1]}-{names[-1].split('-')[-1]}"
                        
                        base_df = pd.read_excel(os.path.join(tpl_dir, sel_tpl))
                        rows = [{"item_sku": p_sku, "parentage": "parent", "variation_theme": "SizeColor"}]
                        
                        for img in imgs:
                            b_name = img.name.split('.')[0]
                            color_val = b_name.split('-')[-1]
                            ai_data = call_openai_listing(encode_image(img), color_val, keywords)
                            
                            for s in [x.strip() for x in sz_list.split(",")]:
                                rows.append({
                                    "item_sku": f"{b_name}-{s}",
                                    "parent_sku": p_sku,
                                    "parentage": "child",
                                    "item_name": f"{ai_data['title']} - {s}" if ai_data else f"{b_name} {s}",
                                    "bullet_point1": ai_data['bullets'][0] if ai_data else "",
                                    "color_name": color_val,
                                    "size_name": s
                                })
                        
                        final_df = pd.concat([base_df, pd.DataFrame(rows)], ignore_index=True)
                        buf = io.BytesIO()
                        final_df.to_excel(buf, index=False)
                        st.download_button("📥 下載表格", buf.getvalue(), f"Upload_{p_sku}.xlsx")

    # --- 📊 模組 3: 市場調研 ---
    with tabs[2]:
        st.header("📊 競品數據查詢")
        asin = st.text_input("輸入 ASIN")
        if st.button("查詢數據") and RAINFOREST_KEY:
            st.write(f"正在分析 {asin}...")
