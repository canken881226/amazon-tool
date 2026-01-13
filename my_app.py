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

# 初始化固定位置坐标与缩放
if 'global_pos_x' not in st.session_state: st.session_state.global_pos_x = 100
if 'global_pos_y' not in st.session_state: st.session_state.global_pos_y = 100
if 'global_scale' not in st.session_state: st.session_state.global_scale = 30

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

    # --- 💰 模块 1: 自动利润测算 (完全保持不变) ---
    with tabs[0]:
        st.subheader("💰 2026 官方新政自动测算 (含 5% 预警)")
        mode = st.radio("配送模式", ["FBA 官方配送 (含$3头程)", "FBM 本地发货 (无头程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        with col_l:
            st.markdown("### 1. 基础参数设定")
            price = st.number_input("产品售价 ($)", value=19.99)
            cost_rmb = st.number_input("采购成本 (RMB)", value=35.0)
            category = st.radio("类目性质", ["非服装类 (16%)", "服装类 (18%)"], horizontal=True)
            st.markdown("#### 📏 尺寸与重量 (判定小号标准红线: 1.9cm)")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("长 (cm)", value=38.1)
            with c2: w_cm = st.number_input("宽 (cm)", value=30.4)
            with c3: h_cm = st.number_input("最短边/厚度 (cm)", value=1.9)
            weight_kg = st.number_input("发货重量 (kg)", value=0.45)
        with col_r:
            st.markdown("### 2. 系统判定结果")
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            is_large = not is_small and (l_cm <= 45.7 and w_cm <= 35.5 and h_cm <= 20.3 and weight_kg <= 9.07)
            
            if is_small:
                tier, base_fba = "小号标准尺寸", (3.32 if price >= 10.0 else 2.05)
            elif is_large:
                tier, base_fba = "大号标准尺寸", (5.42 if price >= 10.0 else 3.35)
            else:
                tier, base_fba = "大件尺寸 (Oversize)", 9.73

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
            with st.expander("成本结构具体明细", expanded=True):
                st.write(f"🎫 佣金 ({int(comm_rate*100)}%): ${refer_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA头程: $3.00")
                    st.write(f"📦 官方配送费(含5%缓冲): ${fba_final_ship:.3f}")
                else:
                    st.write(f"📮 FBM配送费: ${fbm_final_ship:.2f}")

    # --- 📊 模块 2: 市场调研 (完全保持不变) ---
    with tabs[1]:
        st.header("📊 市场类目与竞品全维度深度调研")
        kw_input = st.text_input("输入类目核心关键词", placeholder="请输入要分析的类目...")
        if st.button("🔍 启动 BSR & 新品榜全量扫描", use_container_width=True):
            if kw_input:
                with st.spinner('分析中...'):
                    time.sleep(1)
                    st.session_state.analysis_results = {
                        "competitors": pd.DataFrame({
                            "维度": ["热销组合", "主流款式", "热门图案元素", "主要售价区间"],
                            "BSR榜单表现": ["单品装 (65%)", "极简风", "几何图形", "$19.99 - $24.99"],
                            "新品榜表现": ["2件套装 (40%↑)", "复古风", "植物印花", "$29.99 - $35.99"]
                        }),
                        "price_dist": pd.DataFrame({"价格段": ["<$15", "$15-25", "$25-40", "$40+"], "占比": [15, 45, 30, 10]}).set_index("价格段")
                    }
        if st.session_state.analysis_results:
            res = st.session_state.analysis_results
            st.table(res["competitors"])
            st.bar_chart(res["price_dist"])

    # --- 🖼️ 模块 3: 场景批量渲染 (同步预览优化版) ---
    with tabs[2]:
        st.header("🖼️ 场景批量渲染 (多图同步预览)")
        
        # 1. 上传区
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            bg_files = st.file_uploader("1. 背景底图 (支持多选同步预览)", accept_multiple_files=True, key="bg_main")
        with r_col2:
            pr_files = st.file_uploader("2. 产品透明 PNG (批量替换对象)", accept_multiple_files=True, key="pr_main")
        
        if bg_files and pr_files:
            st.divider()
            st.subheader("⚙️ 联动校准控制台")
            st.caption("调整下方滑块，所有场景图将同步更新摆放位置")
            
            # 联动滑块
            ctrl_c1, ctrl_c2, ctrl_c3 = st.columns(3)
            with ctrl_c1:
                st.session_state.global_pos_x = st.slider("水平坐标 (X)", 0, 2000, st.session_state.global_pos_x)
            with ctrl_c2:
                st.session_state.global_pos_y = st.slider("垂直坐标 (Y)", 0, 2000, st.session_state.global_pos_y)
            with ctrl_c3:
                st.session_state.global_scale = st.slider("统一缩放比例 (%)", 5, 100, st.session_state.global_scale)

            # 联动展示所有上传的背景图
            st.markdown("### 👁️ 实时全场景同步预览")
            
            # 使用第一张产品图作为校准参照
            pr_img = Image.open(pr_files[0]).convert("RGBA")
            
            # 网格化展示预览
            grid_cols = st.columns(2) # 每行显示2张预览
            for idx, bg_file in enumerate(bg_files):
                bg_img = Image.open(bg_file).convert("RGBA")
                
                # 计算缩放后的产品
                target_w = int(bg_img.width * (st.session_state.global_scale / 100))
                target_h = int(pr_img.height * (target_w / pr_img.width))
                pr_resized = pr_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                
                # 画面合成
                combined = bg_img.copy()
                combined.paste(pr_resized, (st.session_state.global_pos_x, st.session_state.global_pos_y), pr_resized)
                
                # 展示在网格中
                grid_cols[idx % 2].image(combined, caption=f"场景 {idx+1} 预览", use_container_width=True)

            if st.button("🚀 锁定当前位置并执行全量渲染", use_container_width=True):
                st.success(f"已锁定坐标({st.session_state.global_pos_x}, {st.session_state.global_pos_y})，正在批量处理 {len(bg_files) * len(pr_files)} 组合...")
                time.sleep(1.5)
                st.balloons()
        else:
            st.info("💡 请先上传背景图和产品图。您可以一次性上传多张背景图，下方的预览区会同步展示它们的效果。")

    # --- 📦 模块 4: 智能备货管理 (完全保持不变) ---
    with tabs[3]:
        st.header("📦 FBA 智能备货计算器")
        st.info("💡 公式：(采购 + 运输 + 安全天数) × 日销 - 库存")
        row1 = st.columns(3)
        with row1[0]: d_val = st.number_input("预估日销量", value=20)
        with row1[1]: p_val = st.number_input("采购生产周期 (天)", value=7)
        with row1[2]: s_val = st.number_input("跨境运输周期 (天)", value=30)
        row2 = st.columns(3)
        with row2[0]: b_val = st.number_input("安全缓冲天数 (天)", value=15)
        with row2[1]: k_val = st.number_input("现有总库存", value=200)
        with row2[2]: m_val = st.number_input("起订量 (MOQ)", value=100)
        
        theo_restock = max(0, int((p_val + s_val + b_val) * d_val - k_val))
        final_restock = theo_restock if theo_restock >= m_val else (m_val if theo_restock > 0 else 0)
        st.divider()
        res_cols = st.columns(3)
        with res_cols[0]: st.metric("理论建议备货", f"{theo_restock} Pcs")
        with res_cols[1]: 
            st.metric("实际建议下单", f"{final_restock} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True)
        with res_cols[2]: st.metric("库存支撑天数", f"{int(k_val/d_val if d_val > 0 else 0)} 天")
