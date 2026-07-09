import os
import uuid

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, ToolMessage
import platform

from hutud.primission.permission import check_permission
from hutud.tools.bash_tool import run_powershell
from hutud.tools.ststem_tool import *

# 获取系统配置
load_dotenv(override=True)
model = os.getenv("HUTUD_MODEL")
base_url = os.getenv("HUTUD_BASE_URL")
api_key = os.getenv("HUTUD_API_KEY")
provider = os.getenv("HUTUD_PROVIDER")

print(model)
print(base_url)
print(api_key)
print(provider)
print(os.getcwd())
print(platform.system())

# 创建模型
messages: list[BaseMessage] = [
    SystemMessage(content="你所有的回复前面都必须加上对我的称呼: 主人"),
    SystemMessage(
        content=(
            f"You are a coding agent working at: {os.getcwd()}.\n"
            "Current OS: Windows.\n"
            "Shell: Windows PowerShell.\n"
            "You must generate Windows PowerShell commands only.\n"
            "Use Get-ChildItem instead of ls.\n"
            "Use Get-Content instead of cat.\n"
            "Use Select-String instead of grep.\n"
            "Use Get-Location instead of pwd.\n"
            "Use Get-Command instead of which.\n"
            "Do not use Linux/macOS/bash commands such as ls -la, cat, grep, rm, chmod, sudo.\n"
            "Use the run_powershell tool when you need to inspect files, run tests, or execute commands.\n"
            "Act, don't explain."
        )
    ),
    SystemMessage(content=f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain.")
]

agent_tools = [run_powershell, read_file, write_file, edit_file]

# 映射表
tool_map = {
    tool.name: tool
    for tool in agent_tools
}

llm = init_chat_model(model=model, model_provider=provider, api_base=base_url, api_key=api_key).bind_tools(agent_tools)

session_id = uuid.uuid4()

while True:
    try:
        input_message = input(f"\033[36m{session_id} >> \033[0m")
    except (EOFError, KeyboardInterrupt):
        print("程序异常退出!!")
        break

    if input_message.strip().lower() in ("q", "exit", ""):
        print("😊hutud_agent 退出, 再见宝贝~")
        break

    messages.append(HumanMessage(content=input_message))

    while True:
        llm_response = llm.invoke(messages)

        # 先把 AIMessage 加入历史
        messages.append(llm_response)

        # 如果没有工具调用，直接输出最终回答
        if not llm_response.tool_calls:
            print("\033[32m AI message >> \033[0m", llm_response.content)
            break

        for call in llm_response.tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            tool_call_id = call["id"]

            call_fun = tool_map.get(tool_name)

            if call_fun is None:
                tool_output = f"Error: Tool {tool_name} not found"
            else:
                try:
                    # 执行工具
                    # 执行工具前判断权限
                    if not check_permission(call):
                        tool_output = "Permission denied."
                        continue

                    tool_output = call_fun.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error while running tool {tool_name}: {e}"

            messages.append(ToolMessage(content=tool_output, tool_call_id=tool_call_id))






