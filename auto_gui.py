import asyncio
import time
import websockets
import pyautogui
import json
import logging

# 配置日志，方便调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# *** 重要：请将此处的 IP 地址替换为你的电脑在内网中的实际 IP 地址。***
# 如何查找：Windows 打开 CMD 输入 'ipconfig'，查找 IPv4 地址；macOS/Linux 打开终端输入 'ifconfig' 或 'ip a'。
HOST = '192.168.8.129' # 例如: '192.168.1.100' 或 '10.0.0.5'
PORT = 9999 # WebSocket 服务的默认端口通常是 80 或 443，但测试时使用其他端口更方便

async def handle_message(websocket):
    """
    处理来自客户端的 WebSocket 消息。
    接收 JSON 格式的命令，执行 PyAutoGUI 操作，并发送响应。
    """
    client_address = websocket.remote_address
    logging.info(f"Client connected: {client_address}")

    try:
        async for message in websocket:
            logging.info(f"Received from {client_address}: {message}")
            response_message = {"status": "error", "message": "Unknown error."}

            try:
                # 解析 JSON 消息，预期格式如: {"command": "click", "args": {"x": 100, "y": 200}}
                command_data = json.loads(message)
                command = command_data.get('command', '').lower()
                args = command_data.get('args', {}) # args 期望是一个字典

                if not command:
                    response_message = {"status": "error", "message": "Command not specified."}
                elif command == 'click':
                    x = args.get('x')
                    y = args.get('y')
                    if x is not None and y is not None:
                        pyautogui.click(x, y)
                        response_message = {"status": "success", "message": f"Clicked at ({x}, {y})."}
                    else:
                        pyautogui.click()
                        response_message = {"status": "success", "message": f"Clicked at current position."}
                elif command == 'rightclick':
                    x = args.get('x')
                    y = args.get('y')
                    if x is not None and y is not None:
                        pyautogui.rightClick(x, y)
                        response_message = {"status": "success", "message": f"RightClicked at ({x}, {y})."}
                    else:
                        pyautogui.rightClick()
                        response_message = {"status": "success", "message": f"RightClicked at current position."}
                elif command == 'moveto':
                    x = args.get('x')
                    y = args.get('y')
                    if x is not None and y is not None:
                        pyautogui.moveTo(x, y)
                        response_message = {"status": "success", "message": f"Mouse move to ({x}, {y})."}
                    else:
                        response_message = {"status": "error", "message": "Move_to command requires 'x' and 'y' arguments."}
                elif command == 'move':
                    x = args.get('x', 0)
                    y = args.get('y', 0)
                    duration = args.get('duration', 0.1)
                    if x is not None and y is not None:
                        pyautogui.move(x, y, duration=duration) 
                        response_message = {"status": "success", "message": f"Mouse move ({x}, {y})."}
                    else:
                        response_message = {"status": "error", "message": "Move command requires 'x' and 'y' arguments."}
                elif command == 'type':
                    text = args.get('text')
                    if text is not None:
                        pyautogui.write(text)
                        response_message = {"status": "success", "message": f"Typed '{text}'."}
                    else:
                        response_message = {"status": "error", "message": "Type command requires 'text' argument."}
                elif command == 'press':
                    key = args.get('key')
                    if key is not None:
                        pyautogui.press(key)
                        response_message = {"status": "success", "message": f"Pressed '{key}'."}
                    else:
                        response_message = {"status": "error", "message": "Press command requires 'key' argument."}
                elif command == 'hotkey':
                    keys = args.get('keys') # 期望是一个列表，例如 ["ctrl", "alt", "del"]
                    if isinstance(keys, list) and all(isinstance(k, str) for k in keys):
                        pyautogui.hotkey(*keys) 
                        response_message = {"status": "success", "message": f"Pressed hotkey {keys}."}
                    else:
                        response_message = {"status": "error", "message": "Hotkey command requires 'keys' argument as a list of strings."}
                elif command == 'screenshot':
                    filename = args.get('filename', 'screenshot.png')
                    pyautogui.screenshot(filename)
                    response_message = {"status": "success", "message": f"Screenshot saved to {filename}."}
                elif command == 'keydown':
                    key = args.get('key')
                    logging.info(f"Key down: key:{key}")
                    if key:
                        pyautogui.keyDown(key)
                        response_message = {"status": "success", "message": f"Key: {key} was pressed down."}
                    else:
                        response_message = {"status": "error", "message": "No specified 'key' in arguments to be pressed down."}
                elif command == 'keyup':
                    key = args.get('key')
                    logging.info(f"Key up: key:{key}")
                    if key:
                        pyautogui.keyUp(key)
                        response_message = {"status": "success", "message": f"Key: {key} was got up."}
                    else:
                        response_message = {"status": "error", "message": "No specified 'key' in arguments to be get up."}
                elif command == 'hold':
                    key = args.get('key')
                    logging.info(f"Key hold: key:{key}")
                    if key:
                        pyautogui.hold(key)
                        response_message = {"status": "success", "message": f"Key: {key} was hold on."}
                    else:
                        response_message = {"status": "error", "message": "No specified 'key' in arguments to be hold on."}
                elif command == 'open_terminal_and_exec':
                    target_command = args.get('command')
                    if target_command:                        
                        # Attempt to open common terminals (e.g., gnome-terminal, xterm, konsole)
                        # This is less reliable due to varied desktop environments
                        # For best results, use a hotkey you've set up for your terminal if available
                        try:
                            pyautogui.hotkey('ctrl', 'alt', 't') # Common shortcut for terminal in many Linux distros
                            time.sleep(1) # Give terminal time to open
                            pyautogui.write(target_command)
                            pyautogui.press('enter')
                            response_message = f"Linux terminal opened (via Ctrl+Alt+T) and executed: '{target_command}'."
                        except Exception:
                            # Fallback: Try to run command directly in background if terminal launch fails
                            # Note: This won't show output in a new terminal, just executes.
                            import subprocess
                            subprocess.Popen(target_command, shell=True) # Executes in background, no new terminal
                            response_message = f"Linux command executed directly: '{target_command}' (no new terminal window)."
                    else:
                        response_message = {"status": "error", "message": "Open terminal command requires a 'command' argument."}

                else:
                    response_message = {"status": "error", "message": f"Unknown command: '{command}'."}

            except json.JSONDecodeError:
                response_message = {"status": "error", "message": "Invalid JSON format received."}
            except Exception as e:
                response_message = {"status": "error", "message": f"Error executing command: {e}"}
            
            # 发送 JSON 格式的响应回客户端
            await websocket.send(json.dumps(response_message))

    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"Client disconnected gracefully: {client_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        logging.error(f"Client disconnected with error ({e.code}, {e.reason}): {client_address}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred with {client_address}")
    finally:
        logging.info(f"Connection with {client_address} closed.")

async def start_websocket_server():
    """启动 WebSocket 服务器，监听并处理连接"""
    logging.warning("WARNING: This server allows network control of your mouse and keyboard.")
    logging.warning("Ensure you understand the security implications before proceeding.")

    # 启动 WebSocket 服务器，绑定到指定 IP 和端口
    async with websockets.serve(handle_message, HOST, PORT):
        logging.info(f"PyAutoGUI WebSocket server listening on ws://{HOST}:{PORT}")
        # 保持服务器运行，直到程序被外部中断 (例如 Ctrl+C)
        await asyncio.Future() 

if __name__ == "__main__":
    # 使用 asyncio 运行 WebSocket 服务器
    asyncio.run(start_websocket_server())