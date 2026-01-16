import streamlit as st
from openai import OpenAI
from lunar_python import Solar, Lunar, I18n
from datetime import datetime

# --- 1. 页面配置 ---
# 注意：这里的逗号必须是英文的 ","
st.set_page_config(
    page_title="DeepSeek 命理大师"，
    page_icon="☯️"，
    layout="wide"，
    initial_sidebar_state="expanded"
)

# --- 2. 工具函数定义 ---

# 城市经度字典
CITY_LONGITUDE = {
    "北京": 116.40， "上海": 121.47， "广州": 113.26， "深圳": 114.05，
    "成都": 104.06， "杭州": 120.15， "武汉": 114.30， "西安": 108.93，
    "重庆": 106.55， "南京": 118.79， "天津": 117.20， "沈阳": 123.43，
    "香港": 114.17， "台北": 121.50
}

def get_bazi_ziwei(year, month, day, hour, minute, longitude, gender):
    """
    获取八字和紫微数据 (核心算法)
    """
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    if longitude:
        solar = solar.getSolarTimeByLongitude(longitude)
    
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()
    ziwei = bazi.getZiWei()
    
    # 八字数据
    bazi_data = {
        "乾造/坤造": gender,
        "四柱": f"{bazi.getYearGan()}{bazi.getYearZhi()}  {bazi.getMonthGan()}{bazi.getMonthZhi()}  {bazi.getDayGan()}{bazi.getDayZhi()}  {bazi.getTimeGan()}{bazi.getTimeZhi()}"，
        "日主": f"{bazi.getDayGan()} (五行:{bazi.getDayWuXing()})"，
        "格局": f"{bazi.getMonthZhi()}月令"， 
        "起运": f"{bazi.getYun(1 if gender == '男' else 0)。getStartYear()}年"
    }

    # 紫微数据
    destiny = ziwei.getDestinyPalace()
    body = ziwei.getBodyPalace()
    
    # 辅助函数：获取星曜亮度
    def get_stars_info(stars):
        return "、"。join([s.getName() + ("(庙)" if s.isMiao() else "(陷)" if s.isXian() else "") for s in stars])

    ziwei_data = {
        "命宫主星": get_stars_info(destiny.getMajorStars())，
        "身宫主星": get_stars_info(body.getMajorStars())，
        "迁移宫": get_stars_info(ziwei.getPalace(6)。getMajorStars())，
        "财帛宫": get_stars_info(ziwei.getPalace(4)。getMajorStars())，
        "官禄宫": get_stars_info(ziwei.getPalace(8)。getMajorStars())，
        "四化": f"禄:{ziwei.getHuaLuStar()。getName()} 权:{ziwei.getHuaQuanStar()。getName()} 科:{ziwei.getHuaKeStar()。getName()} 忌:{ziwei.getHuaJiStar()。getName()}"
    }
    
    return bazi_data, ziwei_data, solar, lunar

def get_strategy_data(lunar):
    """
    获取决策建议数据 (替代奇门，使用择吉逻辑)
    """
    return {
        "策略类型": "流日择吉决策"，
        "建除十二神": lunar.getZhiXing()，
        "二十八宿": f"{lunar.getXiu()}宿 ({lunar.getXiuLuck()})"，
        "今日宜": "、"。join(lunar.getYi())，
        "今日忌": "、"。join(lunar.getJi())，
        "吉神方位": f"喜神:{lunar.getPositionXi()} 财神:{lunar.getPositionCai()} 福神:{lunar.getPositionFu()}"，
        "彭祖百忌": f"{lunar.getPengZuGan()} {lunar.getPengZuZhi()}"
    }

# --- 3. 侧边栏：输入区 ---
with st.sidebar:
    st.title("⚙️ 测算设置")
    
    api_key = st.text_input("DeepSeek API Key", type="password", help="在此填入 api.deepseek.com 的 Key")
    st.divider()
    
    gender = st.radio("性别"， ["男"， "女"], horizontal=True)
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("出生日期", value=datetime(1996， 1， 25))
    with col2:
        birth_time = st.time_input("出生时间", value=datetime.strptime("10:30"， "%H:%M")。time())
    
    city = st.selectbox("出生城市 (校正真太阳时)"， list(CITY_LONGITUDE.keys()) + ["其他"])
    if city == "其他":
        longitude = st.number_input("输入经度", value=116.40)
    else:
        longitude = CITY_LONGITUDE[city]
    
    st.divider()
    query = st.text_area("你想问什么？", placeholder="例如：最近工作压力大，适合跳槽吗？", height=100)
    run_btn = st.button("🚀 启动 DeepSeek 推演", type="primary")

# --- 4. 主界面 ---
st.title("🌌 AI 全息命理咨询")
st.caption("内核：DeepSeek V3 | 引擎：Lunar-Python (Pro)")

if run_btn:
    if not api_key:
        st.error("请先在左侧填入 DeepSeek API Key！")
    else:
        # 1. 计算排盘
        with st.status("正在进行多维排盘...", expanded=True) as status:
            st.write("🔄 正在校正真太阳时...")
            bazi, ziwei, solar_obj, lunar_obj = get_bazi_ziwei(
                birth_date.year, birth_date.month, birth_date.day， 
                birth_time.hour, birth_time.minute, longitude, gender
            )
            st.write("✅ 八字/紫微排盘完成")
            
            st.write("🔄 正在分析时空能量...")
            strategy = get_strategy_data(lunar_obj)
            st.write("✅ 择吉决策模型加载完成")
            status.update(label="排盘完成，准备提交给 DeepSeek", state="complete", expanded=False)

        # 2. 展示数据
        with st.expander("📊 查看详细盘面数据"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("### 四柱八字")
                st.json(bazi)
            with c2:
                st.markdown("### 紫微斗数")
                st.json(ziwei)
            with c3:
                st.markdown("### 行动决策")
                st.json(strategy)

        # 3. 组装 Prompt
        full_prompt = f"""
        你是一位资深命理学家。请基于以下排盘数据，回答用户问题。

        【用户档案】
        - 性别: {gender}
        - 真太阳时: {solar_obj.toFullString()}
        - 咨询问题: {query}

        【盘面数据】
        1. **八字 (体)**: {bazi}
           - 分析日主强弱、格局层次。
        2. **紫微 (相)**: {ziwei}
           - 重点分析命宫、身宫及化忌星的影响。
        3. **决策 (用)**: {strategy}
           - "建除十二神"和"二十八宿"代表当下的时空能量状态。
           - 结合"宜忌"给出具体的行动建议。

        【回复要求】
        - **结论先行**：直接给出吉凶判断。
        - **逻辑严密**：八字定大方向，紫微看细节，择吉定行动时机。
        - **语气**：专业、客观、富有智慧。
        """

        # 4. 调用 API
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        st.divider()
        st.subheader("💡 DeepSeek 深度解析")
        message_placeholder = st.empty()
        full_response = ""

        try:
            response = client.chat。completions。create(
                model="deepseek-chat"，
                messages=[
                    {"role": "system"， "content": "你是专业的命理分析师。"}，
                    {"role": "user"， "content": full_prompt}
                ]，
                stream=True
            )
            for chunk in response:
                if chunk.choices[0]。delta。content:
                    full_response += chunk.choices[0]。delta。content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"接口调用失败: {str(e)}")
