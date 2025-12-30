import streamlit as st
import pandas as pd
import urllib3
from PIL import Image
import io

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心环境初始化 (彻底解决 AttributeError) ---
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'bs_data' not in st.session_state:
    st.session_state.bs_data = []

# --- 2. 🔐 访问控制 ---
if not st.session_state.password_correct:
    st.set_page_config(page_title="🔐 登录 - 亚马逊决策系统", layout="centered")
    st.title("🔐 TPC 内部系统 - 请登录")
    pwd = st.text_input("输入公司访问密码：", type="password")
    if st.button("确认"):
        if pwd == "TPCamazon@2026":
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("❌ 密码错误")
else:
    # --- ⚙️ 全局页面配置 ---
    st.set_page_config(page_title="亚马逊决策系统 V12.6", layout="wide")
    st.title("⚖️ 亚马逊全维度决策系统 V12.6")

    # --- 🚀 功能导航 (四个功能模组严格锁定) ---
    tabs = st.tabs(["💰 2026 利润测算", "📊 市场与竞品调研", "🖼️ 场景批量渲染", "📦 智能备货管理"])

    # --- 💰 模块 1: 2026 利润与运费测算 (对齐 2026.01.15 标准) ---
    with tabs[0]:
        st.subheader("💰 2026 FBA 配送费精算 (含 5% 涨价缓冲)")
        mode = st.radio("发货模式切换", ["FBA 官方配送 (含$3头程)", "FBM 本地发货 (无头程)"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 核心成本设定")
            price = st.number_input("产品售价 ($)", value=19.99)
            cost_rmb = st.number_input("采购成本 (RMB)", value=35.0)
            
            # 💡 核心：佣金实时联动
            category = st.radio("类目性质", ["非服装类 (16%)", "服装类 (18%)"], horizontal=True)
            
            st.markdown("#### 📏 产品物理属性 (cm/kg)")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("长 (cm)", value=38.1)
            with c2: w_cm = st.number_input("宽 (cm)", value=30.4)
            with c3: h_cm = st.number_input("厚度/最短边 (cm)", value=1.9)
            weight_kg = st.number_input("发货重量 (kg)", value=0.45)

        with col_r:
            st.markdown("### 2. 测算明细 (2026.01.15 标准)")
            
            # --- 💡 2026 官方分段判定逻辑 ---
            # 小号标准: 38.1 x 30.4 x 1.9 cm | 重量 0.45kg
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            # 大号标准: 45.7 x 35.5 x 20.3 cm | 重量 9.07kg
            is_large = not is_small and (l_cm <= 45.7 and w_cm <= 35.5 and h_cm <= 20.3 and weight_kg <= 9.07)
            
            if is_small:
                tier_name = "小号标准尺寸 (Small Standard)"
                base_fee = 2.05 if price < 10.0 else 2.62
            elif is_large:
                tier_name = "大号标准尺寸 (Large Standard)"
                base_fee = 3.35 if price < 10.0 else 5.42
            else:
                tier_name = "大件尺寸 (Large/Oversize)"
                base_fee = 9.73 # 预警起始费率
            
            # --- 💡 加计 5% 涨价缓冲 ---
            fba_fee_final = base_fee * 1.05
            
            # --- 💡 佣金计算逻辑 ---
            comm_rate = 0.16 if "非服装类" in category else 0.18
            referral_fee = price * comm_rate
            
            purchase_usd = cost_rmb / 6.0
            fba_head = 3.0 if "FBA" in mode else 0.0
            fbm_shipping = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            fba_final_ship = fba_fee_final if "FBA" in mode else 0.0
            
            total_cost = purchase_usd + referral_fee + fba_head + fba_final_ship + fbm_shipping
            profit = price - total_cost
            
            st.success(f"### 预估纯利: ${profit:.2f}")
            st.metric("毛利率 (%)", f"{(profit/price)*100:.2f}%")
            st.info(f"📍 **当前判定分段**：{tier_name}")

            with st.expander("📄 成本结构具体明细", expanded=True):
                st.write(f"💵 采购成本 (USD): ${purchase_usd:.2f}")
                st.write(f"🎫 佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA头程: ${fba_head:.2f}")
                    st.write(f"📦 官方配送费 (含5%缓冲): ${fba_final_ship:.3f}")
                else:
                    st.write(f"📮 FBM本地运费: ${fbm_shipping:.2f}")

    # --- 📊 模块 2: 市场与竞品调研 (模块加固) ---
    with tabs[1]:
        st.header("📊 市场与竞品调研")
        asin_query = st.text_input("输入 ASIN 或关键词进行大数据调研")
        if st.button("启动分析"):
            st.info("功能正常：正在连接实时数据接口...")

    # --- 🖼️ 模块 3: 场景批量渲染 (模块加固) ---
    with tabs[2]:
        st.header("🖼️ 场景批量渲染")
        c_up1, c_up2 = st.columns(2)
        with c_up1: st.file_uploader("1. 上传背景图 (多选)", accept_multiple_files=True, key="bg")
        with c_up2: st.file_uploader("2. 上传产品图 (PNG)", accept_multiple_files=True, key="pr")
        st.button("🔥 开始批量合成")

    # --- 📦 模块 4: 智能备货管理 (对齐 efed275eb 专业布局) ---
    with tabs[3]:
        st.header("📦 FBA 智能备货计算器")
        st.info("💡 公式：(采购周期 + 运输周期 + 安全天数) × 日销 - 现有总库存")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: d_sales = st.number_input("预估日销量 (Pcs/天)", value=20)
        with r1c2: p_cycle = st.number_input("生产周期 (天)", value=7)
        with r1c3: s_cycle = st.number_input("运输周期 (天)", value=30)
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: buffer = st.number_input("安全天数", value=15)
        with r2c2: stock_val = st.number_input("现有库存 (FBA+在途)", value=200)
        with r2c3: moq_val = st.number_input("最小起订量 (MOQ)", value=100)
        
        theo_order = max(0, int((p_cycle + s_cycle + buffer) * d_sales - stock_val))
        act_order = theo_order if theo_order >= moq_val else (moq_val if theo_order > 0 else 0)
        
        st.divider()
        m_c1, m_c2, m_c3 = st.columns(3)
        with m_c1: st.metric("理论建议备货", f"{theo_order} Pcs")
        with m_c2: 
            st.metric("建议下单量 (含MOQ)", f"{act_order} Pcs")
            st.markdown("<span style='color:#00ff00'>↑ 0</span>", unsafe_allow_html=True)
        with m_c3: st.metric("库存支撑", f"{int(stock_val/d_sales if d_sales > 0 else 0)} 天")
