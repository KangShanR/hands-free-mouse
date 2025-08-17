import asyncio
import json
import websockets
import subprocess
import shlex
import os
import logging
import traceback

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

# ydotool uses Linux kernel event codes.
# This mapping converts common key names to their corresponding codes.
KEY_MAPPING = {
    # Alphanumeric Keys
    'a': '30', 'b': '48', 'c': '46', 'd': '32', 'e': '18',
    'f': '33', 'g': '34', 'h': '35', 'i': '23', 'j': '36',
    'k': '37', 'l': '38', 'm': '50', 'n': '49', 'o': '24',
    'p': '25', 'q': '16', 'r': '19', 's': '31', 't': '20',
    'u': '22', 'v': '47', 'w': '17', 'x': '45', 'y': '21',
    'z': '44',

    # Number Keys (top row)
    '1': '2', '2': '3', '3': '4', '4': '5', '5': '6',
    '6': '7', '7': '8', '8': '9', '9': '10', '0': '11',

    # Function Keys
    'f1': '59', 'f2': '60', 'f3': '61', 'f4': '62', 'f5': '63',
    'f6': '64', 'f7': '65', 'f8': '66', 'f9': '67', 'f10': '68',
    'f11': '87', 'f12': '88',

    # Modifier Keys (Note: use these for hotkeys, not simple presses)
    'shift': '42', 'ctrl': '29', 'alt': '56', 'win': '125', 
    'meta': '125', # Alias for 'win' or 'super' key

    # Navigation and Special Keys
    'enter': '28', 'return': '28',
    'esc': '1', 'escape': '1',
    'backspace': '14',
    'tab': '15',
    'space': '57',
    'capslock': '58',
    'delete': '111',
    'insert': '110',
    'home': '102',
    'end': '107',
    'pageup': '104',
    'pagedown': '109',
    'printscreen': '99',
    'pause': '119',

    # Arrow Keys
    'up': '103',
    'down': '108',
    'left': '105',
    'right': '106',

    # Punctuation and Symbols (Common QWERTY layout)
    # ydotool also needs a mapping for the shift versions.
    # We will handle these with the YDOTool_CHAR_MAP for 'type' command.
    'minus': '12',
    'equal': '13',
    'bracketleft': '26',
    'bracketright': '27',
    'backslash': '43',
    '\\': '43',
    'semicolon': '39',
    'apostrophe': '40',
    'grave': '41',
    'comma': '51',
    'period': '52',
    'slash': '53',
    '/': '53',

    # Numpad Keys
    'numpad0': '82', 'numpad1': '79', 'numpad2': '80', 'numpad3': '81',
    'numpad4': '75', 'numpad5': '76', 'numpad6': '77', 'numpad7': '71',
    'numpad8': '72', 'numpad9': '73',
    'numlock': '69',
    'numpad_slash': '98', 'numpad_star': '55', 'numpad_minus': '74',
    'numpad_plus': '78', 'numpad_enter': '96', 'numpad_dot': '83',

    # Media Keys
    'volumemute': '113', 'volumeup': '115', 'volumedown': '114',
    'playpause': '164', 'stop': '166',
    'prevtrack': '165', 'nexttrack': '163',
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

async def handle_message(websocket):
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
                            execute_ydotool_command(['type', char])
                        else:
                            # Use key command for single characters
                            execute_ydotool_command(['type', char])
                    response["message"] = f"Typed text: '{text_to_type}'"
                elif command == 'press':
                    key = args.get('key')
                    if key and key in YDOTool_CHAR_MAP:
                        execute_ydotool_command(['type', key])
                        response["message"] = f"Pressed key: {key}"
                    elif key and key in KEY_MAPPING:
                        code = KEY_MAPPING[key]
                        # ydotool uses different key names, map common ones if needed
                        # For simplicity, we'll assume the front-end sends ydotool-compatible names
                        execute_ydotool_command(['key', f'{code}:1', f'{code}:0'])
                        response["message"] = f"Pressed key: {key}, code: {code}"
                    else:
                        response["status"] = "error"
                        response["message"] = "Key not specified for 'press' command."
                elif command == 'hotkey':
                    keys = args.get('keys', [])
                    codes = [KEY_MAPPING.get(key.lower()) for key in keys] 
                    if codes and all(codes):
                        # Build the keydown/keyup sequence for the hotkey
                        keydown_commands = [f'{k}:1' for k in codes]
                        keyup_commands = [f'{k}:0' for k in reversed(codes)] # Release in reverse order
                        execute_ydotool_command(['key'] + keydown_commands + keyup_commands)
                        response["message"] = f"Pressed hotkey combination: {keys}"
                    else:
                        response["status"] = "error"
                        response["message"] = "Keys not specified for 'hotkey' command."
                elif command == 'keydown':
                    key = args.get('key')
                    code = KEY_MAPPING.get(key)
                    if key and code:
                        execute_ydotool_command(['key', f'{code}:1'])
                        response["message"] = f"Key down: {key}, code:{code}"
                        response["key"] = key
                    else:
                        response["status"] = "error"
                        response["message"] = "Key not specified for 'keydown' command."
                elif command == 'keyup':
                    key = args.get('key')
                    code = KEY_MAPPING.get(key)
                    if key and code:
                        execute_ydotool_command(['key', f'{code}:0'])
                        response["message"] = f"Key up: {key}, code:{code}"
                        response["key"] = key
                    else:
                        response["status"] = "error"
                        response["message"] = "Key not specified for 'keyup' command."
                elif command == 'move':
                    x = args.get('x', 0)
                    y = args.get('y', 0)
                    # ydotool mousemove takes absolute or relative coordinates.
                    # We are using relative moves, so add --relative flag
                    execute_ydotool_command(['mousemove', '-x', str(x), '-y', str(y)])
                    response["message"] = f"Moved mouse by ({x}, {y})"
                elif command == 'click':
                    # ydotool click takes button number (1 for left, 2 for right, 3 for middle)
                    button_map = {'left': 'C0', 'right': 'C1', 'middle': 'C2'}
                    button = button_map.get(args.get('button', 'left'), 'C0')
                    execute_ydotool_command(['click', button])
                    response["message"] = f"Clicked with button '{args.get('button', 'left')}'"
                elif command == 'scroll':
                    clicks = args.get('clicks', 0)
                    # For scroll, we can map to mouse wheel commands
                    # Scroll up
                    if clicks > 0:
                        code = KEY_MAPPING.get('up')
                        codes = [f'{code}:1', f'{code}:0']
                        execute_ydotool_command(['key'] + [item for _ in range(clicks) for item in codes])
                        response["message"] = f"Scrolled by {clicks} clicks"
                    # Scroll down
                    elif clicks < 0:
                        code = KEY_MAPPING.get('down')
                        codes = [f'{code}:1', f'{code}:0']
                        execute_ydotool_command(['key'] + [item for _ in range(-clicks) for item in codes])
                        response["message"] = f"Scrolled by {clicks} clicks"
                    else:
                        button = 'C0'
                        execute_ydotool_command(['click', button])
                        response["message"] = "It's a click, not a scroll."
                elif command == 'hscroll':
                    clicks = args.get('clicks', 0)
                    # For scroll, we can map to mouse wheel commands
                    # Scroll right
                    if clicks > 0:
                        code = KEY_MAPPING.get('right')
                        codes = [f'{code}:1', f'{code}:0']
                        execute_ydotool_command(['key'] + [item for _ in range(clicks) for item in codes])
                        response["message"] = f"Scrolled by {clicks} clicks"
                    # Scroll left
                    elif clicks < 0:
                        code = KEY_MAPPING.get('left')
                        codes = [f'{code}:1', f'{code}:0']
                        execute_ydotool_command(['key'] + [item for _ in range(-clicks) for item in codes])
                        response["message"] = f"Scrolled by {clicks} clicks"
                    else:
                        button = 'C0'
                        execute_ydotool_command(['click', button])
                        response["message"] = "It's a click, not a scroll."
                elif command == 'exec':
                    # This command is system-specific and doesn't change with ydotool
                    cmd_to_exec = args.get('command')
                    print(f"command:{cmd_to_exec}")
                    if cmd_to_exec:
                        if os.name == 'posix':  # macOS/Linux
                            display_env = os.environ.copy()
                            display_env['DISPLAY'] = ':0'
                            subprocess.run(cmd_to_exec, check=True, shell=True, env=display_env)
                            # subprocess.run([shlex.quote(cmd_to_exec)])
                        else:
                            response["status"] = "error"
                            response["message"] = "This command is only supported on Linux/macOS."
                        response["message"] = f"Executed: {cmd_to_exec}"
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
                traceback.print_exc()
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")
    finally:
        print("Handler finished.")



async def start_websocket_server():
    """启动 WebSocket 服务器，监听并处理连接"""
    logging.warning("WARNING: This server allows network control of your mouse and keyboard.")
    logging.warning("Ensure you understand the security implications before proceeding.")

    # start_server = websockets.serve(handle_message, "192.168.8.129", 9999)
    # print("Starting WebSocket server on ws://192.168.8.129:9999")
    # asyncio.get_event_loop().run_until_complete(start_server)
    # asyncio.get_event_loop().run_forever()
    # 启动 WebSocket 服务器，绑定到指定 IP 和端口
    async with websockets.serve(handle_message, "192.168.8.129", 9999):
        # logging.info(f"PyAutoGUI WebSocket server listening on ws://{HOST}:{PORT}")
        logging.info(f"PyAutoGUI WebSocket server listening on ws://192.168:8888")
        # 保持服务器运行，直到程序被外部中断 (例如 Ctrl+C)
        await asyncio.Future() 

if __name__ == "__main__":
    # 使用 asyncio 运行 WebSocket 服务器
    asyncio.run(start_websocket_server())