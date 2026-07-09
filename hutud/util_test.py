import uuid

from hutud.primission.permission import PERMISSION_RULES, RISK_LIST

print(uuid.uuid4())

fun = lambda args: any(kw in args.get("command", "") for kw in RISK_LIST)

args = {'command': 'Remove-Item -Path "D:\\hutud\\python_test_demo\\hutud_agent\\hutud\\1.txt" -Force'}

command = args["command"].lower()

for item in RISK_LIST:
    if item in command:
        print(True)
        break
    else:
        print(item)