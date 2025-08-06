# hands-free-mouse
Input without any traditional device, like keyboard\mouse etc. Just on your phone only one hand. So, it's not literily hands-free, but it's really helpful when you need hold your baby in your arms👨‍🍼.
It's baby caring!

## Requirements
### System
This project was tested on Ubuntu 24.04. If you are using the linux, it's almost working perfect.
### Python enviroment
The project needs run two server on your compurter: one for the pyautogui server, another for the h5 client. The wWhole prject was programed and tested by the python 3.12.3, but you can run the project by python 3.0+. Run the project in python venv was better than native system python envionment.

## Hands free on your compurter

> Run the client h5 page by python http.server module, if you prefer nginx or Apache, it's ok.
> Run the pyautogui websocket server in a python venv.

1. Download the repository(main branch is ok: `git clone git@github.com:KangShanR/hands-free-input.git`)
2. Enter the client dir: `cd your_project_path/client`
3. Export all the env variables: `export SERVER_HOST="..." SERVER_PORT=... CLIENT_SERVER_PORT=...`
4. Server the client page to the private network: `python -m http.server $CLIENT_SERVER_PORT`. Now you can see the client page on your phone brower in the private network, just access the url: host_ip:CLIENT_SERVER_PORT/remote_client.html.
    1. You can get your host_ip just run the command `ip addr` on the host.
5. Enter the main dir: `cd ..` 
6. Server the pyautogui: `nohup python auto_gui.py > log/server.log 2>&1 &`
    1. You can see the logs by `tail -f log/server.log`
