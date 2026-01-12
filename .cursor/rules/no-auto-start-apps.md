# DO NOT AUTO-START APPLICATIONS

## Rule: Never start applications in background terminals

When the user asks to test or run applications:
1. **DO NOT** use `is_background: true` in run_terminal_cmd
2. **DO NOT** start servers/apps automatically
3. **PROVIDE** the command for the user to run themselves

## Instead, always:
```
# Provide the command like this:
To start the server, run:
cd C:\GitHub\TheseApps\openWakeWord
.\.venv312\Scripts\python.exe examples/web/streaming_server.py
```

## Why:
- User needs to test locally in their own terminal
- Background terminals waste tokens when user has to ask to kill them
- User prefers to control when apps start/stop

## Examples:
❌ WRONG:
```python
run_terminal_cmd(
    command="python server.py",
    is_background=true  # NEVER DO THIS
)
```

✅ CORRECT:
```
To start the server:
\`\`\`powershell
cd C:\GitHub\TheseApps\openWakeWord
python examples/web/streaming_server.py
\`\`\`
```