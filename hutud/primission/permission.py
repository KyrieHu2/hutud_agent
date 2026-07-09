import dataclasses
from enum import Enum
from pathlib import Path

WORKDIR = Path.cwd()
# 状态
class PermissionStatus(Enum):
    DENY = ("deny", "直接拒绝")
    ASK = ("ask", "询问")
    ALLOW = ("allow", "允许")

RISK_LIST = [
# 删除文件/目录
    "remove-item",
    "rm ",
    "del ",
    "erase ",
    "rmdir ",
    "rd ",
    "Set-Content",
    "Add-Content"
]

DENY_LIST = [

    # 强制/递归删除常见参数
    "-recurse",
    "-force",

    # 格式化/清盘/磁盘操作
    "format-volume",
    "clear-disk",
    "initialize-disk",
    "new-partition",
    "remove-partition",
    "diskpart",

    # 关机/重启
    "stop-computer",
    "restart-computer",
    "shutdown",
    "reboot",

    # 注册表危险操作
    "reg delete",
    "remove-itemproperty",
    "set-itemproperty",

    # 权限/执行策略
    "set-executionpolicy",
    "takeown",
    "icacls",

    # 管理员提权
    "start-process",
    "-verb runas",
    "runas",

    # 可疑脚本执行
    "invoke-expression",
    "iex ",
    "encodedcommand",
    "-encodedcommand",

    # 下载后执行，比较危险
    "invoke-webrequest",
    "iwr ",
    "curl ",
    "wget ",
]

PERMISSION_RULES = [
    {"tools": ["write_file", "edit_file"],
     # 判断写和改的工具命令是否超出项目地址
     "check": lambda args: not (WORKDIR / args.get("path", "")).resolve().is_relative_to(WORKDIR),
     "message": "Writing outside workspace"},
    {"tools": ["run_powershell"],
     # 判断是否有危险命令
     "check": lambda args: (
    isinstance(cmd := args.get("command", ""), str)
    and any(kw.lower() in cmd.lower() for kw in RISK_LIST)
    ),
     "message": "Potentially destructive command"},
]


# 查看是否拒绝命令
def check_deny_list(command: str) -> str | None:
    for pattern in DENY_LIST:
        if pattern in command:
            return f"Blocked: '{pattern}' is on the deny list"
    return None

def check_rules(tool_name: str, args: dict) -> str | None:
    for rule in PERMISSION_RULES:
        if tool_name in rule["tools"] and rule["check"](args):
            return rule["message"]
    return None

# 询问用户
def ask_user(tool_name: str, args: dict, reason: str) -> str:
    print(f"\n⚠  {reason}")
    print(f"   Tool: {tool_name}({args})")
    choice = input("   Allow? [y/N] ").strip().lower()
    return PermissionStatus.ALLOW.value[0] if choice in ("y", "yes") else PermissionStatus.DENY.value[0]

def check_permission(call) -> bool:
    tool_name = call["name"]
    tool_args = call["args"]
    # 闸门 1: 硬拒绝
    if tool_name == "run_powershell":
        reason = check_deny_list(tool_args["command"])
        if reason:
            print(f"\n⛔ {reason}")
            return False

    # 闸门 2 + 3: 规则匹配 → 用户审批
    reason = check_rules(tool_name, tool_args)
    if reason:
        decision = ask_user(tool_name, tool_args, reason)
        if decision == "deny":
            return False

    return True