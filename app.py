import streamlit as st
from openai import OpenAI
from lunar_python import Solar, Lunar
from kinqimen import Qimen
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="DeepSeek 命理大师",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 工具函数定义 ---

# 城市经度字典 (简易版)
CITY_LONGITUDE = {
    "北京": 116.40, "上海": 121.47, "广州": 113.26, "深圳": 114.05,
    "成都": 104.06, "杭州": 120.15, "武汉": 114.30, "西安": 108.93,
    "重庆": 106.55, "南京": 118.79, "天津": 117.20, "沈阳": 123.43,
    "香港": 114.17, "台北": 121.50
}

def get_bazi_ziwei(year, month, day, hour, minute, longitude, gender):
    """
    使用 lunar-python 获取八字和紫微数据
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
        "四柱": f"{bazi.getYearGan()}{bazi.getYearZhi()}  {bazi.getMonthGan()}{bazi.getMonthZhi()}  {bazi.getDayGan()}{bazi.getDayZhi()}  {bazi.getTimeGan()}{bazi.getTimeZhi()}",
        "空亡": f"年空:{bazi.getYearXunKong()}  日空:{bazi.getDayXunKong()}",
        "起运": f"{bazi.getYun(1 if gender == '男' else 0).getStartYear()}年",
        "命宫": bazi.getMingGong()
    }

    # 紫微数据 (Python环境下 lunar-python 是最佳选择)
    destiny = ziwei.getDestinyPalace()
    body = ziwei.getBodyPalace()
    
    ziwei_data = {
        "局数": f"{ziwei.getFiveElementBureau()}",
        "命宫主星": "、".join([s.getName() + ("(庙)" if s.isMiao() else "(陷)" if s.isXian() else "") for s in destiny.getMajorStars()]),
        "身宫主星": "、".join([s.getName() for s in body.getMajorStars()]),
        "迁移宫": "、".join([s.getName() for s in ziwei.getPalace(6).getMajorStars()]),
        "财帛宫": "、".join([s.getName() for s in ziwei.getPalace(4).getMajorStars()]),
        "官禄宫": "、".join([s.getName() for s in ziwei.getPalace(8).getMajorStars()])
    }
    
    return bazi_data, ziwei_data, solar

def get_kinqimen_data(year, month, day, hour):
    """
    使用 kinqimen 获取时家奇门排盘
    """
    try:
        # kinqimen 的调用方式，这里做容错处理
        # 注意：kinqimen 库的具体API可能随版本变动，这里使用基础排盘逻辑
        qm = Qimen(year, month, day, hour)
        info = qm.get_info() # 获取排盘信息
        return {
            "类型": "时家奇门",
            "局数": f"{info.get('jieqi')} {info.get('dun')} {info.get('ju')}局",
            "值符": info.get('zhifu'),
            "值使": info.get('zhishi'),
            "旬首": info.get('xunshou'),
            "格局": "需结合九宫分析 (AI将基于局数推演)"
        }
    except Exception as e:
        return {"错误": f"奇门排盘失败: {str(e)}", "提示": "可能时间超出范围"}

# --- 3. 侧边栏：输入区 ---
with st.sidebar:
    st.title("⚙️ 测算设置")
    
    # DeepSeek API 设置
    api_key = st.text_input("DeepSeek API Key", type="password", help="在此填入 api.deepseek.com 的 Key")
    
    st.divider()
    
    # 基础信息
    gender = st.radio("性别", ["男", "女"], horizontal=True)
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("出生日期", value=datetime(1996, 1, 25))
    with col2:
        birth_time = st.time_input("出生时间", value=datetime.strptime("10:30", "%H:%M").time())
    
    # 经度校正
    city = st.selectbox("出生城市 (校正真太阳时)", list(CITY_LONGITUDE.keys()) + ["其他"])
    if city == "其他":
        longitude = st.number_input("输入经度", value=116.40)
    else:
        longitude = CITY_LONGITUDE[city]
    
    # 测算意图
    st.divider()
    query = st.text_area("你想问什么？", placeholder="例如：我适合去互联网行业发展吗？今年的财运如何？", height=100)
    
    run_btn = st.button("🚀 启动 DeepSeek 推演", type="primary")

# --- 4. 主界面 ---
st.title("🌌 AI 全息命理咨询")
st.caption("内核：DeepSeek V3 | 引擎：Lunar + KinQimen")

if run_btn:
    if not api_key:
        st.error("请先在左侧填入 DeepSeek API Key！")
    else:
        # 1. 计算排盘
        with st.status("正在进行多维排盘...", expanded=True) as status:
            st.write("🔄 正在校正真太阳时...")
            bazi, ziwei, solar_obj = get_bazi_ziwei(
                birth_date.year, birth_date.month, birth_date.day, 
                birth_time.hour, birth_time.minute, longitude, gender
            )
            st.write("✅ 八字/紫微排盘完成")
            
            st.write("🔄 正在起奇门局...")
            qimen = get_kinqimen_data(
                birth_date.year, birth_date.month, birth_date.day, birth_time.hour
            )
            st.write("✅ 奇门遁甲起局完成")
            status.update(label="排盘完成，准备提交给 DeepSeek", state="complete", expanded=False)

        # 2. 展示数据 (JSON 调试视图)
        with st.expander("📊 查看详细盘面数据 (专业版)"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("### 四柱八字")
                st.json(bazi)
            with c2:
                st.markdown("### 紫微斗数")
                st.json(ziwei)
            with c3:
                st.markdown("### 奇门遁甲")
                st.json(qimen)

        # 3. 组装 Prompt
        full_prompt = f"""
        你是一位精通"三式"（八字、紫微、奇门）的资深命理学家。请基于以下排盘数据，回答用户问题。

        【用户档案】
        - 性别: {gender}
        - 真太阳时: {solar_obj.toFullString()}
        - 咨询问题: {query}

        【盘面数据】
        1. **八字 (体)**: {bazi}
           - 请分析日主旺衰、喜用神、大运走势。
        2. **紫微 (相)**: {ziwei}
           - 请结合命宫、身宫、三方四正的星情进行性格和运势细节补充。
        3. **奇门 (用)**: {qimen}
           - 请利用奇门局的时空能量，分析当下的环境利弊和行动建议。

        【回复要求】
        - **风格**: 半文半白，专业且有深度，像一位得道高人。
        - **逻辑**: 必须进行"交叉验证"。如果八字显示财运好，但紫微财帛宫化忌，请说明这种矛盾的具体表现。
        - **结构**: 
           1. 🎯 **核心断语** (直接回答问题)
           2. 🧬 **命局深析** (八字与紫微的合参)
           3. 🛡️ **决策建议** (奇门遁甲的行动指南)
        """

        # 4. 调用 DeepSeek API
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        st.divider()
        st.subheader("💡 DeepSeek 深度解析")
        message_placeholder = st.empty()
        full_response = ""

        try:
            response = client.chat.completions.create(
                model="deepseek-chat", # 或 deepseek-reasoner
                messages=[
                    {"role": "system", "content": "你是专业的命理分析师。"},
                    {"role": "user", "content": full_prompt}
                ],
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"DeepSeek 接口调用失败: {str(e)}")
