import streamlit as st
import google.generativeai as genai
from lunar_python import Solar, Lunar, JieQi
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="AI 命理大师 - 智能算命系统",
    page_icon="🔮",
    layout="wide"
)

# --- 2. 基础数据与工具函数 ---
# 简易城市经度字典（用于真太阳时校正，MVP版本内置，后续可对接API）
CITY_LONGITUDE = {
    "北京": 116.40, "上海": 121.47, "广州": 113.26, "深圳": 114.05,
    "成都": 104.06, "杭州": 120.15, "武汉": 114.30, "西安": 108.93,
    "重庆": 106.55, "南京": 118.79, "天津": 117.20, "沈阳": 123.43,
    "长沙": 112.93, "昆明": 102.83, "郑州": 113.62, "福州": 119.30,
    "香港": 114.17, "台北": 121.50, "其他": 0.00
}

def get_true_solar_time(year, month, day, hour, minute, longitude):
    """
    计算真太阳时
    """
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    # 如果经度不为0（选择了具体城市或手动输入），则使用 lunar-python 内置的经度校正
    if longitude != 0.00:
        return solar.getSolarTimeByLongitude(longitude)
    return solar

def get_chart_data(solar, gender_input):
    """
    核心排盘逻辑：调用 lunar-python 生成八字、紫微、奇门基础数据
    """
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()
    ziwei = bazi.getZiWei()
    
    # 1. 八字数据
    bazi_data = {
        "年柱": f"{bazi.getYearGan()}{bazi.getYearZhi()} ({bazi.getYearNaYin()})",
        "月柱": f"{bazi.getMonthGan()}{bazi.getMonthZhi()} ({bazi.getMonthNaYin()})",
        "日柱": f"{bazi.getDayGan()}{bazi.getDayZhi()} ({bazi.getDayNaYin()}) - [日主]",
        "时柱": f"{bazi.getTimeGan()}{bazi.getTimeZhi()} ({bazi.getTimeNaYin()})",
        "大运": f"{bazi.getYun(1 if gender_input == '男' else 0).getStartYear()}年起运",
        "当前状态": f"节气: {lunar.getPrevJieQi().getName()} -> {lunar.getNextJieQi().getName()}"
    }

    # 2. 紫微斗数数据 (简化提取核心)
    ming_gong = ziwei.getDestinyPalace()
    shen_gong = ziwei.getBodyPalace()
    
    ziwei_data = {
        "命宫": f"{ming_gong.getName()} ({ming_gong.getGan()}{ming_gong.getZhi()})",
        "命宫主星": "、".join([f"{s.getName()}({s.getBrightness()})" for s in ming_gong.getMajorStars()]),
        "身宫主星": "、".join([f"{s.getName()}({s.getBrightness()})" for s in shen_gong.getMajorStars()]),
        "三方四正": "AI将根据全盘数据自动推导", # 这里只做展示，Prompt会包含更细数据
        "局数": f"{ziwei.getFiveElementBureau()}"
    }

    # 3. 奇门遁甲 (基础定局参数)
    # lunar-python 暂无完整时家奇门排盘，但可以通过节气和日干支推导 "局数"
    # 这里我们提取辅助 AI 判断时空能量的参数
    qimen_data = {
        "旬首": bazi.getTimeXun() + bazi.getTimeXunKong(), 
        "值符值使": "需根据局数推导", # 留给 AI 也就是 Gemini 凭借其知识库去推演
        "备注": "提供时空干支结构，供奇门意象分析"
    }

    return {
        "meta": {
            "solar_time": solar.toFullString(),
            "lunar_time": lunar.toString(),
            "gender": gender_input
        },
        "bazi": bazi_data,
        "ziwei": ziwei_data,
        "qimen_hint": qimen_data
    }

# --- 3. 侧边栏：用户输入 ---
with st.sidebar:
    st.header("⚙️ 测算设置")
    
    # API Key 输入 (安全起见，让用户自己填，或者你在部署时通过 Secrets 填)
    api_key = st.text_input("请输入 Google API Key", type="password", help="在 Google AI Studio 获取")
    
    st.divider()
    
    st.subheader("1. 个人信息")
    gender = st.radio("性别", ["男", "女"], horizontal=True)
    birth_date = st.date_input("出生日期", min_value=datetime(1900, 1, 1), value=datetime(1996, 1, 25))
    birth_time = st.time_input("出生时间", value=datetime.strptime("10:30", "%H:%M").time())
    
    st.subheader("2. 出生地 (校正真太阳时)")
    city = st.selectbox("选择最近的城市", list(CITY_LONGITUDE.keys()))
    
    if city == "其他":
        longitude = st.number_input("请输入经度", value=116.40, format="%.2f")
    else:
        longitude = CITY_LONGITUDE[city]
        st.caption(f"已自动校准经度: {longitude}")

    st.subheader("3. 测算方向")
    query_type = st.selectbox("你想问什么？", ["综合运势", "事业财运", "婚姻感情", "流年分析", "性格深挖"])
    user_question = st.text_area("具体问题 (可选)", placeholder="例如：我适合创业吗？明年能不能结婚？")
    
    start_btn = st.button("🚀 开始 AI 批命", type="primary")

# --- 4. 主界面：显示与逻辑 ---
st.title("🔮 AI 命理咨询室")
st.markdown("##### 基于 Google Gemini Pro 与 天文历法算法的专业测算")

if start_btn:
    if not api_key:
        st.error("请先在左侧填入 Google API Key！")
    else:
        try:
            with st.spinner("正在排盘并连接宇宙能量 (AI 计算中)..."):
                # A. 计算数据
                solar_obj = get_true_solar_time(
                    birth_date.year, birth_date.month, birth_date.day,
                    birth_time.hour, birth_time.minute, longitude
                )
                chart_data = get_chart_data(solar_obj, gender)
                
                # B. 展示排盘结果 (JSON/表格)
                with st.expander("📜 查看您的命盘数据 (点击展开)", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("八字乾坤")
                        st.json(chart_data['bazi'])
                    with col2:
                        st.subheader("紫微斗数")
                        st.json(chart_data['ziwei'])
                
                # C. 组装 AI Prompt
                prompt = f"""
                你是一位精通《三命通会》、《紫微斗数全书》与《奇门遁甲》的资深命理大师。
                请根据以下精准的排盘数据，为用户进行【{query_type}】方面的深度分析。
                
                【用户数据】
                - 性别: {gender}
                - 真太阳时: {chart_data['meta']['solar_time']}
                - 八字: {chart_data['bazi']}
                - 紫微核心: {chart_data['ziwei']}
                
                【用户问题】
                {user_question if user_question else "请进行综合详批。"}
                
                【分析要求】
                1. **结论先行**：直接给出吉凶或建议。
                2. **多维验证**：用八字定格局高低，用紫微看细节象义，如果可以，结合奇门的时间能量给出行动建议。
                3. **拒绝巴纳姆效应**：不要说模棱两可的话，要基于盘面说具体的断语。
                4. **语气风格**：专业、客观、富有同理心，像一位智者在对话。
                5. **格式**：使用 Markdown 排版，重点加粗。
                """

                # D. 调用 Gemini
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                
                # E. 显示结果
                st.divider()
                st.subheader("💡 大师解读")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"测算过程中发生错误: {str(e)}")
            st.warning("请检查网络连接或 API Key 是否有效。")

# --- 底部版权 ---
st.markdown("---")
st.markdown("Designed by PM & AI Copilot | Powered by `lunar-python` & `Google Gemini`")
