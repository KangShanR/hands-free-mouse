import asyncio
import json
import websockets
import subprocess
import shlex
import os

# Set a variable for the ydotool command prefix.
# This makes the code cleaner and easier to read.
YDOTool_CMD_PREFIX = ["ydotool"]

# NEW: Character mapping for ydotool, since it uses a different syntax.
YDOTool_CHAR_MAP = {
    '<': ['shift', 'comma'],
    '>': ['shift', 'period'],
    '\'': ["'"],
    '"': ['shift', "'"],
    '!': ['shift', '1'],
    '@': ['shift', '2'],
    '#': ['shift', '3'],
    '$': ['shift', '4'],
    '%': ['shift', '5'],
    '^': ['shift', '6'],
    '&': ['shift', '7'],
    '*': ['shift', '8'],
    '(': ['shift', '9'],
    ')': ['shift', '0'],
    '_': ['shift', 'minus'],
    '+': ['shift', 'equal'],
    '{': ['shift', 'bracketleft'],
    '}': ['shift', 'bracketright'],
    '|': ['shift', 'backslash'],
    ':': ['shift', 'semicolon'],
    '?': ['shift', 'slash'],
    '~': ['shift', 'grave'],
}

def execute_ydotool_command(args):
    """
    Executes a ydotool command using subprocess.
    """
    try:
        command = YDOTool_CMD_PREFIX + args
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: ydotool is not installed or not in PATH.")
        raise
    except subprocess.CalledProcessError as e:
        print(f"Error executing ydotool command: {e.stderr.decode()}")
        raise

async def handle_message(websocket, path):
    print(f"Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            try:
                command_data = json.loads(message)
                command = command_data.get('command')
                args = command_data.get('args', {})

                response = {"status": "success", "message": "Command executed successfully.", "command": command}

                if command == 'type':
                    text_to_type = args.get('text', '')
                    # Ydotool type command handles special characters directly, but hotkey mapping is more reliable for some
                    # Let's use a hybrid approach to be safe
                    for char in text_to_type:
                        if char in YDOTool_CHAR_MAP:
                            hotkey_args = YDOTool_CHAR_MAP[char]
                            execute_ydotool_command(['key'] + [f'{k}+' for k in hotkey_args] + [f'{k}-' for k in hotkey_args])
                        else:
                            # Use key command for single characters
                            execute_ydotool_command(['key', char])
                    response["message"] = f"Typed text: '{text_to_type}'"
                elif command == 'press':
                    key = args.get('key')
                    if key:
                        # ydotool uses different key names, map common ones if needed
                        # For simplicity, we'll assume the front-end sends ydotool-compatible names
                        execute_ydotool_command(['key', f'{key}:1', f'{key}:0'])
                        response["message"] = f"Pressed key: {key}"
                    else:
                        response["status"] = "error"
                        response["message"] = "Key not specified for 'press' command."
                elif command == 'hotkey':
                    keys = args.get('keys', [])
                    if keys:
                        # Build the keydown/keyup sequence for the hotkey
                        keydown_commands = [f'{k}:1' for k in keys]
                        keyup_commands = [f'{k}:0' for k in reversed(keys)] # Release in reverse order
                        execute_ydotool_command(['key'] + keydown_commands + keyup_commands)
                        response["message"] = f"Pressed hotkey combination: {keys}"
                    else:
                        response["status"] = "error"
                        response["message"] = "Keys not specified for 'hotkey' command."
                elif command == 'keydown':
                    key = args.get('key')
                    if key:
                        execute_ydotool_command(['key', f'{key}:1'])
                        response["message"] = f"Key down: {key}"
                        response["key"] = key
                    else:
                        response["status"] = "error"
                        response["message"] = "Key not specified for 'keydown' command."
                elif command == 'keyup':
                    key = args.get('key')
                    if key:
                        execute_ydotool_command(['key', f'{key}:0'])
                        response["message"] = f"Key up: {key}"
                        response["key"] = key
                    else:
                        response["status"] = "error"
                        response["message"] = "Key not specified for 'keyup' command."
                elif command == 'move':
                    x = args.get('x', 0)
                    y = args.get('y', 0)
                    # ydotool mousemove takes absolute or relative coordinates.
                    # We are using relative moves, so add --relative flag
                    execute_ydotool_command(['mousemove', '--relative', str(x), str(y)])
                    response["message"] = f"Moved mouse by ({x}, {y})"
                elif command == 'click':
                    # ydotool click takes button number (1 for left, 2 for right, 3 for middle)
                    button_map = {'left': '1', 'right': '2', 'middle': '3'}
                    button = button_map.get(args.get('button', 'left'), '1')
                    execute_ydotool_command(['click', button])
                    response["message"] = f"Clicked with button '{args.get('button', 'left')}'"
                elif command == 'scroll':
                    clicks = args.get('clicks', 0)
                    # For scroll, we can map to mouse wheel commands
                    if clicks > 0:
                        execute_ydotool_command(['click', '4']) # Scroll up
                    elif clicks < 0:
                        execute_ydotool_command(['click', '5']) # Scroll down
                    response["message"] = f"Scrolled by {clicks} clicks"
                elif command == 'open_terminal_and_exec':
                    # This command is system-specific and doesn't change with ydotool
                    cmd_to_exec = args.get('command')
                    if cmd_to_exec:
                        if os.name == 'posix':  # macOS/Linux
                            subprocess.Popen(['xterm', '-e', shlex.quote(cmd_to_exec)])
                        else:
                            response["status"] = "error"
                            response["message"] = "This command is only supported on Linux/macOS."
                        response["message"] = f"Opened terminal and executed: {cmd_to_exec}"
                    else:
                        response["status"] = "error"
                        response["message"] = "Command not specified."
                else:
                    response["status"] = "error"
                    response["message"] = f"Unknown command: {command}"

                await websocket.send(json.dumps(response))

            except json.JSONDecodeError:
                print(f"Invalid JSON received: {message}")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON format."}))
            except Exception as e:
                print(f"An error occurred: {e}")
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")
    finally:
        print("Handler finished.")

start_server = websockets.serve(handle_message, "0.0.0.0", 8765)

print("Starting WebSocket server on ws://0.0.0.0:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
