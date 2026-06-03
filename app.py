import streamlit as st
from Agent import init_agent
from langchain_core.runnables import RunnableConfig
from langchain.messages import HumanMessage, AIMessage
import re
from pathlib import Path

def get_current_time_str():
    import datetime
    """
    获取当前时间
    :return: 当前时间
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(
    page_title="蓝蓝智能客服",  # 浏览器标签页标题
    page_icon="👗",            # 浏览器标签页图标
    layout="centered"          # 页面内容居中
)

st.title("蓝蓝智能客服")

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    welcome_msg = "你好呀！我是蓝蓝👗，有什么可以帮您的吗？"
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

if "thread_id" not in st.session_state:
    st.session_state.thread_id = get_current_time_str()

if "agent" not in st.session_state:
    st.session_state.agent = init_agent()

# 遍历历史会话列表，并展示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("请输入内容：")
if prompt := user_input:
    with st.chat_message("user"):
       st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("正在输入中..."):
            try:
                agent = st.session_state.agent
                config = RunnableConfig(configurable={"thread_id": st.session_state.thread_id})

                # 构建要发给 Agent 的消息列表
                messages_to_send = []

                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        messages_to_send.append(HumanMessage(content=msg["content"]))
                    else:
                        messages_to_send.append(AIMessage(content=msg["content"]))

                response = agent.invoke(
                    {"messages": messages_to_send},
                    config=config
                )
                reply = response["messages"][-1].content
                img_pattern = r'source/picture/[A-Za-z0-9_]+\.png'
                matches = re.findall(img_pattern, reply)
                clean_reply = reply  # 默认值：没有图片时直接用原文
                if matches:
                    # 把路径从文字里删掉（避免重复显示）
                    clean_reply = re.sub(img_pattern, '', reply).strip()
                    if clean_reply:
                        st.markdown(clean_reply)

                    # 显示图片
                    for img_path in matches:
                        full_path = Path(__file__).parent / img_path
                        if full_path.exists():
                            st.image(str(full_path), width=300)
                        else:
                            st.warning(f"图片不存在: {img_path}")
                else:
                    # 没有图片路径，正常显示文字
                    st.markdown(reply)
            except Exception as e:
                st.error(f"出错了：{str(e)}")
                clean_reply = "系统出错了，请稍后再试"
                st.markdown(clean_reply)
    # 存 session 必须用 clean_reply，否则图片路径会污染对话历史
    st.session_state.messages.append({"role":"assistant", "content":clean_reply})

with st.sidebar:
    st.markdown("### 🕐 营业时间")
    st.info("每天 9:00 - 22:00")  # info显示蓝色信息框

    st.markdown("### 📞 联系人工")
    if st.button("转接人工客服"):
        st.session_state.messages.append({
            "role": "assistant",
            "content": "人工客服已接入，请稍等..."
        })
        st.rerun()

    st.markdown("### 🗑️ 清空对话")
    if st.button("清空聊天记录"):
        st.session_state.messages = []
        st.session_state.thread_id = get_current_time_str()
        st.rerun()



# st.title("🤓蓝蓝智能客服")
#
# # 创建历史会话列表
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# # 遍历历史会话列表，并展示
# for msg in st.session_state.messages:
#     st.write(f"{msg['role']}:{msg['content']}")
#
# # 输入框和按钮
# user_input = st.text_input("请输入内容：")
# if st.button("发送"):
#     st.session_state.messages.append({"role": "用户", "content": user_input})
#     ai_reply = f"我收到了：{user_input}"
#     st.session_state.messages.append({"role":"AI", "content": ai_reply})


# st.title("我的第一个页面") 大标题
# st.write("hello world!") 显示内容
#
# st.title("测试输入框")
# user_input = st.text_input("请输入内容：")
# st.write("你输入的内容是：", user_input)

# user_input = st.text_input("请输入内容：")
# if st.button("提交"):
#     st.write("你提交了：", user_input)
# else:
#     st.write("等待输入……")

# st.title("理解session_state")
#
# if "remember_var" not in st.session_state:
#     st.session_state.remember_var = 0
#
# normal_var = 0
#
# st.write(f"普通变量：{normal_var}")
# st.write(f"记住的变量：{st.session_state.remember_var}")
# st.divider()  # 分割线
#
# clo1, col2 = st.columns(2)
# with (clo1):
#     if st.button("+1"):
#         normal_var += 1
#         st.write(f"普通变量变成了：{normal_var}")
#         st.info("但这个值在下次点击时会消失！") # 蓝色提示信息
#
# with col2:
#     if st.button("💾 记住的变量 +1"):
#         st.session_state.remember_var += 1
#         st.write(f"记住的变量变成了：{st.session_state.remember_var}")
#         st.success("这个值会一直保留！") # 绿色成功提示
#
# st.divider()
# st.caption("💡 提示：点击按钮后，观察两个变量的区别")  # 灰色tips

# st.title("button vs columns 对比")
#
# st.subheader("1️⃣ 单独用 button")
# if st.button("这是一个按钮"):
#     st.write("按钮被点击了！")
#
# st.divider()
#
# st.subheader("2️⃣ 单独用 columns（里面不放东西）")
# col1, col2 = st.columns(2)
# st.write("上面有两列，但里面是空的，所以什么都看不到")
#
# st.divider()
#
# st.subheader("3️⃣ columns + button 配合使用")
# col_a, col_b = st.columns(2)
#
# with col_a:
#     st.write("左边列")
#     if st.button("左边的按钮"):
#         st.write("左边被点了")
#
# with col_b:
#     st.write("右边列")
#     if st.button("右边的按钮"):
#         st.write("右边被点了")