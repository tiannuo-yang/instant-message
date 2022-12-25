from ui_server import Ui_Server
from PyQt5 import QtWidgets
import sys
import socket
import time
import json
import threading

from data_get_set import get_logger,get_user_info,add_logger,set_user_info,delete_user
alive_list = []

def table_show():
    user_info = get_user_info()
    ui_server.tableWidget.clearContents()
    i_ = 0
    for i in range(len(user_info)):
        for j in range(len(user_info[i])-1):
            ui_server.tableWidget.setItem(i_,j,QtWidgets.QTableWidgetItem(str(user_info[i][j])))
        i_ += 1

def table_update():
    update_item = ui_server.tableWidget.selectedItems()
    if len(update_item) > 0:
        r, c, t = update_item[0].row(),update_item[0].column(),update_item[0].text()
        if c == 0 and t == '':
            reply = QtWidgets.QMessageBox.question(MainWindow, 'Warning', f'确认删除用户{get_user_info()[r][0]}？', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                logger_append(f'服务端删除用户 [{get_user_info()[r][0]}]')
                delete_user(r)
                table_show()
            else:
                ui_server.tableWidget.setItem(r,c,QtWidgets.QTableWidgetItem(str(get_user_info()[r][0])))
        else:
            set_user_info(r,c,t)
            if c in [0,1]:
                logger_append(f'服务端修改用户信息 [{get_user_info()[r][0]} {get_user_info()[r][1]}]')

def logger_append(text):
    time_str = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    add_logger(time_str, text)
    ui_server.textBrowser.append(f'{time_str} {text}')

def validate_passwd(data, tcp_client_1, tcp_client_address):
    id, passwd = data['id'], data['passwd']
    ip = tcp_client_address
    
    user_info = get_user_info()
    for i in range(len(user_info)):
        if user_info[i][0] == id and user_info[i][1] == passwd:
            set_user_info(i,2,f'{ip[0]}:{ip[1]}')
            table_show()
            logger_append(f"用户 [{data['id']}] 成功登录，IP地址 [{tcp_client_address[0]}:{tcp_client_address[1]}]")
            send_info = "1".encode()
            tcp_client_1.send(send_info)
            return 
    send_info = "0".encode()
    tcp_client_1.send(send_info)
    return

def keep_alive(recv_data, tcp_client_1, tcp_client_address):
    global alive_list
    
    id = recv_data['id']
    udp_addr = recv_data['udp_addr']
    
    user_info = get_user_info()
    for i in range(len(user_info)):
        if user_info[i][0] == id:
            set_user_info(i,3,udp_addr)
            break

    send_info = json.dumps({'server_time':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),
                           'alive_list':[[user[0], user[3]] for user in get_user_info() if user[2] != '0'],})
    send_info = send_info.encode()
    tcp_client_1.send(send_info)
    
    alive_list.append(id)
      
def dispose_client_request(tcp_client_1, tcp_client_address):
    # 5 循环接收和发送数据
    while True:
        recv_data = tcp_client_1.recv(4096)

        if recv_data:
            data = json.loads(recv_data.decode())
            if data['type'] == 'validate_passwd':
                validate_passwd(data, tcp_client_1, tcp_client_address)
            elif data['type'] == 'keep_alive':
                keep_alive(data, tcp_client_1, tcp_client_address)
        else:
            # tcp_client_1.close()
            break
        
def run():
    tcp_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
    tcp_server.bind(("127.0.0.1",61234))
    tcp_server.listen(128)

    while True:
        tcp_client_1 , tcp_client_address = tcp_server.accept()
        thd = threading.Thread(target = dispose_client_request, args = (tcp_client_1,tcp_client_address))
        
        # 设置守护主线程  即如果主线程结束了 那子线程中也都销毁了  防止主线程无法退出
        thd.setDaemon(True)
        
        # 启动子线程对象
        thd.start()

def test_alive():
    global alive_list # 如果接收到KeepAlive数据包，相应的alive_list会存入该用户
    while(True):
        time.sleep(1)
        print(f'当前在线用户 {set(alive_list)}')
        user_info = get_user_info()
        for i in range(len(user_info)):
            if user_info[i][0] in alive_list:
                pass
            elif user_info[i][2] != '0':
                set_user_info(i,2,'0')
                table_show()
                logger_append(f"用户 [{user_info[i][0]}] 退出登录")
        alive_list = []
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    
    ui_server = Ui_Server()
    ui_server.setupUi(MainWindow)
    table_show()
    ui_server.tableWidget.itemChanged.connect(table_update)
    
    MainWindow.show()
    
    start_thd = threading.Thread(target=run)
    start_thd.setDaemon(True)
    start_thd.start()

    test_alive_thd = threading.Thread(target=test_alive)
    test_alive_thd.setDaemon(True)
    test_alive_thd.start()
    
    sys.exit(app.exec_())
    