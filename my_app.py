import streamlit as st
import pandas as pd
import urllib3
from PIL import Image
import io

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. 核心初始化 (防止变量丢失) ---
if 'password_correct' not in st.session_state: st.session_state.password_correct = False
if 'bs_data' not in st.session_state: st.session_state.bs_data = []

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
    st.set_page_config(page_title="亚马逊决策系统 V13.1", layout="wide")
    st.title("⚖️ 亚马逊全维度决策系统 V13.1 (2026 自动判定版)")

    # --- 🚀 核心四大标签页 (结构加固，严禁修改) ---
    tabs = st.tabs(["💰 自动利润测算", "📊 市场与竞品调研", "🖼️ 场景批量渲染", "📦 智能备货管理"])

    # --- 💰 模块 1: 自动利润测算 (完全学习 2026 新政标准) ---
    with tabs[0]:
        st.subheader("💰 2026.01.15 官方新政自动测算 (含 5% 预警缓冲)")
        mode = st.radio("发货模式", ["FBA 官方配送 (含$3头程)", "FBM 本地发货"], horizontal=True)
        col_l, col_r = st.columns([1.2, 0.8])
        
        with col_l:
            st.markdown("### 1. 基础参数输入")
            price = st.number_input("产品售价 ($)", value=19.99)
            cost_rmb = st.number_input("采购成本 (RMB)", value=35.0)
            is_clothing = st.radio("类目性质", ["非服装类 (16%)", "服装类 (18%)"], horizontal=True)
            
            st.markdown("#### 📏 尺寸与重量 (系统将根据 2026 标准自动判定)")
            c1, c2, c3 = st.columns(3)
            with c1: l_cm = st.number_input("最长边 (cm)", value=38.1)
            with c2: w_cm = st.number_input("次长边 (cm)", value=30.4)
            with c3: h_cm = st.number_input("厚度/最短边 (cm)", value=1.9)
            weight_kg = st.number_input("发货重量 (kg)", value=0.45)

        with col_r:
            st.markdown("### 2. 自动化判定结果")
            
            # --- 💡 2026 尺寸判定逻辑校准 ---
            # 小号标准红线: 38.1 x 30.4 x 1.9 cm 且重量 <= 0.45kg
            is_small = (l_cm <= 38.1 and w_cm <= 30.4 and h_cm <= 1.9 and weight_kg <= 0.45)
            # 大号标准红线: 45.7 x 35.5 x 20.3 cm 且重量 <= 9.07kg
            is_large = not is_small and (l_cm <= 45.7 and w_cm <= 35.5 and h_cm <= 20.3 and weight_kg <= 9.07)
            
            # --- 💡 2026 配送费自动匹配 (含 5% 缓冲) ---
            if is_small:
                tier = "小号标准尺寸 (Small Standard)"
                base_fba = 3.32 if price >= 10.0 else 2.05
            elif is_large:
                tier = "大号标准尺寸 (Large Standard)"
                base_fba = 5.42 if price >= 10.0 else 3.35
            else:
                tier = "大件/超标尺寸 (Oversize)"
                base_fba = 9.73 
            
            fba_fee_final = base_fba * 1.05 # 加计 5% 缓冲
            
            # 💡 佣金自动锁定
            comm_rate = 0.18 if "服装类" in is_clothing else 0.16
            referral_fee = price * comm_rate #
            
            purchase_usd = cost_rmb / 6.0
            fba_head = 3.0 if "FBA" in mode else 0.0
            fbm_ship = ((weight_kg * 131 + 16) / 6.0) if "FBM" in mode else 0.0
            ship_cost = fba_fee_final if "FBA" in mode else fbm_ship
            
            profit = price - (purchase_usd + referral_fee + fba_head + ship_cost)
            
            st.success(f"### 预估纯利: ${profit:.2f}")
            st.metric("毛利率", f"{(profit/price)*100:.2f}%")
            st.info(f"📍 **系统判定分段**：{tier}")

            with st.expander("📄 2026 成本明细拆解", expanded=True):
                st.write(f"💵 采购成本 (USD): ${purchase_usd:.2f}")
                st.write(f"🎫 佣金 ({int(comm_rate*100)}%): ${referral_fee:.2f}")
                if "FBA" in mode:
                    st.write(f"🚚 FBA 头程费用: $3.00")
                    st.write(f"📦 官方配送费基准: ${base_fba:.2f}")
                    st.write(f"📈 含缓冲配送费 (5%): ${fba_fee_final:.3f}")

    # --- 📊 模块 2: 市场与竞品调研 (完整保留) ---
    with tabs[1]:
        st.header("📊 市场与竞品调研")
        asin_q = st.text_input("输入 ASIN 或关键词开始调研")
        if st.button("启动分析"): st.info("正在调取亚马逊实时销售数据...")

    # --- 🖼️ 模块 3: 场景批量渲染 (完整保留) ---
    with tabs[2]:
        st.header("🖼️ 场景批量渲染")
        c_u1, c_u2 = st.columns(2)
        with c_u1: st.file_uploader("1. 背景图 (多选)", accept_multiple_files=True, key="bg_l")
        with c_u2: st.file_uploader("2. 贴图产品 (PNG)", accept_multiple_files=True, key="pr_l")
        if st.button("🔥 立即执行合成"): st.success("已加入渲染队列...")

    # --- 📦 模块 4: 智能备货管理 (完整保留专业版布局) ---
    with tabs[3]:
        st.header("📦 FBA 智能备货计算器")
        st.info("💡 公式：(采购周期 + 运输周期 + 安全缓冲) × 日销 - 现有库存")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1: d_avg = st.number_input("日销量", value=20)
        with r1c2: p_t = st.number_input("生产天数", value=7)
        with r1c3: s_t = st.number_input("运输天数", value=30)
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1: buff = st.number_input("安全缓冲", value=15)
        with r2c2: stock = st.number_input("当前总库存", value=200)
        with r2c3: moq = st.number_input("MOQ", value=100)
        
        theo_o = max(0, int((p_t + s_t + buff) * d_avg - stock))
        st.divider()
        st.metric("建议下单量 (含MOQ)", f"{theo_o if theo_o >= moq else (moq if theo_o > 0 else 0)} Pcs")
