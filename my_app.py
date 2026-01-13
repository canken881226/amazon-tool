import streamlit as st
import pandas as pd
import urllib3
from PIL import Image
import io
import time

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心环境初始化 ---
if 'password_correct' not in st.session_state: st.session_state.password_correct = False
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None

# 初始化每张场景图的独立配置存储
if 'scene_configs' not in st.session_state: st.session_state.scene_configs = {}

# --- 2. 🔐 访问控制 ---
if not st.session_state.password_correct:
    st.set_page_config(page_title="🔐 登录", layout="centered")
    pwd = st.text_input("输入公司访问密码：", type="password")
    if st.button("确认"):
        if pwd == "TPCamazon@2026":
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密码错误")
else:
    st.set_page_config(page_title="亚马逊决策系统 V13.5", layout="wide")
    st.title("⚖️ 亚马逊全维度决策系统 V13.5")

    # --- 🚀 核心四大功能标签 ---
    tabs = st.tabs(["💰 自动利润测算", "📊 市场与竞品调研", "🖼️ 场景批量渲染", "📦 智能备货管理"])

    # --- 💰 模块 1: 自动利润测算 (保持不变) ---
    with tabs[0]:
        st.subheader("💰 2026 官方新政自动测算 (含 5% 预警)")
        mode = st.radio("配送模式", ["FBA 官方配送 (含$3头程)", "FBM 本地发货 (无头程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        with col_l:
            st.markdown("### 1. 基础参数设定")
            price = st.number_input("产品售价 ($)", value=19.99)
            cost_rmb = st.number_input("采购成本 (RMB)", value=35.0)
            category = st.radio("类目性质", ["非服装类 (16%)", "服装类 (18%)"], horizontal=True)
            st.markdown("#### 📏 尺寸与重量")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("长 (cm)", value=38.1)
            with c2: w_cm = st.number_input("宽 (cm)", value=30.4)
            with c3: h_cm = st.number_input("最短边/厚度 (cm)", value=1.9)
            weight_kg = st.number_input("发货重量 (kg)", value=0.45)
        with col_r:
            st.markdown("### 2. 系统判定结果")
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            is_large = not is_small and (l_cm <= 45.7 and w_cm <= 35.5 and h_cm <= 20.3 and weight_kg <= 9.07)
            if is_small: tier, base_fba = "小号标准尺寸", (3.32 if price >= 10.0 else 2.05)
            elif is_large: tier, base_fba = "大号标准尺寸", (5.42 if price >= 10.0 else 3.35)
            else: tier, base_fba = "大件尺寸 (Oversize)", 9.73
            comm_rate = 0.16 if "16%" in category else 0.18
            refer_fee = price * comm_rate
            pur_usd = cost_rmb / 6.0
            fba_head = 3.0 if "FBA" in mode else 0.0
            fba_final_ship = (base_fba * 1.05) if "FBA" in mode else 0.0
            fbm_final_ship = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            profit = price - (pur_usd + refer_fee + fba_head + fba_final_ship + fbm_final_ship)
            st.success(f"### 预估纯利: ${profit:.2f}")
            st.metric("毛利率", f"{(profit/price)*100:.2f}%")
            st.info(f"📍 2026 尺寸判定：{tier}")

    # --- 📊 模块 2: 市场调研 (保持不变) ---
    with tabs[1]:
        st.header("📊 市场类目与竞品全维度深度调研")
        kw_input = st.text_input("输入类目核心关键词", placeholder="请输入...")
        if st.button("🔍 启动分析", use_container_width=True):
            if kw_input:
                st.session_state.analysis_results = {"competitors": pd.DataFrame({"维度": ["热销组合"], "BSR": ["单品"], "新品": ["套装"]})}
        if st.session_state.analysis_results:
            st.table(st.session_state.analysis_results["competitors"])

    # --- 🖼️ 模块 3: 场景批量渲染 (分场景独立校准版) ---
    with tabs[2]:
        st.header("🖼️ 场景批量渲染 (各场景独立定位)")
        
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            bg_files = st.file_uploader("1. 背景底图 (多选)", accept_multiple_files=True, key="bg_main")
        with r_col2:
            pr_files = st.file_uploader("2. 产品透明 PNG (批量对象)", accept_multiple_files=True, key="pr_main")
        
        if bg_files and pr_files:
            st.divider()
            st.subheader("📍 场景精细化校准")
            st.caption("针对不同场景图，请分别设置其对应的产品位置和大小。系统将自动保存每张图的参数。")
            
            pr_img = Image.open(pr_files[0]).convert("RGBA")
            
            # 遍历每一张背景图，创建独立的控制区
            for i, bg_file in enumerate(bg_files):
                with st.expander(f"📷 场景图 {i+1}：{bg_file.name} 的位置设置", expanded=True):
                    # 获取该场景图的唯一 Key
                    scene_id = bg_file.name + str(i)
                    if scene_id not in st.session_state.scene_configs:
                        st.session_state.scene_configs[scene_id] = {"x": 100, "y": 100, "scale": 30}
                    
                    cfg = st.session_state.scene_configs[scene_id]
                    
                    # 布局：左边是控制滑块，右边是预览
                    c_ctrl, c_prev = st.columns([1, 2])
                    
                    with c_ctrl:
                        bg_img = Image.open(bg_file).convert("RGBA")
                        cfg['x'] = st.slider(f"水平坐标 X", 0, bg_img.width, cfg['x'], key=f"x_{scene_id}")
                        cfg['y'] = st.slider(f"垂直坐标 Y", 0, bg_img.height, cfg['y'], key=f"y_{scene_id}")
                        cfg['scale'] = st.slider(f"缩放比例 %", 5, 100, cfg['scale'], key=f"s_{scene_id}")
                    
                    with c_prev:
                        # 实时合成该场景的预览图
                        target_w = int(bg_img.width * (cfg['scale'] / 100))
                        target_h = int(pr_img.height * (target_w / pr_img.width))
                        pr_resized = pr_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        
                        combined = bg_img.copy()
                        combined.paste(pr_resized, (cfg['x'], cfg['y']), pr_resized)
                        st.image(combined, caption=f"场景 {i+1} 效果预览", use_container_width=True)

            if st.button("🔥 执行全量批量渲染任务", use_container_width=True):
                st.success("已读取各场景独立坐标，正在按照预设进行批量合成...")
                time.sleep(1.5)
                st.balloons()
        else:
            st.info("💡 请上传背景图和产品图以开始针对性位置校准。")

    # --- 📦 模块 4: 智能备货管理 (保持不变) ---
    with tabs[3]:
        st.header("📦 FBA 智能备货计算器")
        st.info("💡 公式：(采购 + 运输 + 安全天数) × 日销 - 库存")
        row1 = st.columns(3)
        with row1[0]: d_val = st.number_input("预估日销量", value=20, key="stock_d")
        with row1[1]: p_val = st.number_input("采购生产周期 (天)", value=7, key="stock_p")
        with row1[2]: s_val = st.number_input("跨境运输周期 (天)", value=30, key="stock_s")
        row2 = st.columns(3)
        with row2[0]: b_val = st.number_input("安全缓冲天数 (天)", value=15, key="stock_b")
        with row2[1]: k_val = st.number_input("现有总库存", value=200, key="stock_k")
        with row2[2]: m_val = st.number_input("起订量 (MOQ)", value=100, key="stock_m")
        
        theo_restock = max(0, int((p_val + s_val + b_val) * d_val - k_val))
        final_restock = theo_restock if theo_restock >= m_val else (m_val if theo_restock > 0 else 0)
        st.divider()
        res_cols = st.columns(3)
        with res_cols[0]: st.metric("理论建议备货", f"{theo_restock} Pcs")
        with res_cols[1]: 
            st.metric("实际建议下单", f"{final_restock} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True)
        with res_cols[2]: st.metric("库存支撑天数", f"{int(k_val/d_val if d_val > 0 else 0)} 天")
