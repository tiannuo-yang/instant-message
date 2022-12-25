from ui_client import Ui_Client, Ui_Login
from PyQt5 import QtWidgets, QtCore
import sys
import json
import time
import socket
import random
import threading

# 创建一个子线程
class SendKeepAliveThread(QtCore.QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = QtCore.pyqtSignal()

    def run(self):
        global server_time
        global alive_list
        while(True):
            send_info = json.dumps({'type':'keep_alive', 'id': user_id, 'udp_addr': UDP_ADDR}).encode()
            tcp_client_alive.send(send_info)
            recv_data = json.loads(tcp_client_alive.recv(1024).decode())
            # ui_client.textBrowser.clear()
            # ui_client.textBrowser.setText("服务器时钟{}\n在线用户{}".format(recv_data['server_time'], '\n'.join(recv_data['alive_list'])))
            server_time, alive_list =  recv_data['server_time'], recv_data['alive_list']
            self.update_data.emit()
            time.sleep(1)

class RecvUDPMessageThread(QtCore.QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = QtCore.pyqtSignal()

    def run(self):
        global udp_message
        while True:
            recv_data, addr = udpSerSock.recvfrom(4096)
            
            if recv_data:
                udp_message = json.loads(recv_data.decode())
                self.update_data.emit()

def button_login():
    if ui_login.lineEdit.text()=="":
        QtWidgets.QMessageBox.warning(MainWindow, '警告', '用户名不能为空，请输入！')
        return None
    if ui_login.lineEdit_2.text()=="":
        QtWidgets.QMessageBox.warning(MainWindow, '警告', '密码不能为空，请输入！')
        return None
    
    send_info = json.dumps({'type':'validate_passwd', 'id': ui_login.lineEdit.text(), 'passwd':ui_login.lineEdit_2.text()}).encode()
    tcp_client_1, recv_data = send_client_request(send_info)
    
    if recv_data == '1':
        global user_id
        global tcp_client_alive
        global alive_thd
        user_id = ui_login.lineEdit.text()
        tcp_client_alive = tcp_client_1
        
        ui_client.setupUi(MainWindow)
        MainWindow.show()
        ui_client.change_title(MainWindow, user_id)
        
        alive_thd = SendKeepAliveThread()
        alive_thd.update_data.connect(update_online_user)
        alive_thd.start()
        
        ui_client.pushButton.clicked.connect(monitor_send_message)
        
    else:
        QtWidgets.QMessageBox.critical(MainWindow, '错误', '密码错误！')
        ui_login.lineEdit_2.clear()

def update_online_user():
    print(server_time, alive_list)
    ui_client.textBrowser.clear()
    ui_client.textBrowser.setText("服务器时钟: \n{}\n\n在线用户: \n{}".format(server_time, '\n'.join([user[0] for user in alive_list])))

def update_message_box():
    sendfrom = udp_message['sendfrom']
    if sendfrom == user_id:
        sendfrom = f'{user_id} (我)'
    ui_client.textBrowser_2.append(f"{sendfrom} [{udp_message['time']}] \n {udp_message['text']}\n")

def send_client_request(send_info, sendto=("127.0.0.1",61234)):
    tcp_client_1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcp_client_1.connect(sendto)

    tcp_client_1.send(send_info)
    recv_data = tcp_client_1.recv(1024).decode()
    
    return tcp_client_1, recv_data
     
def monitor_send_message():
    send_to = ui_client.lineEdit.text().split(',')
    send_info = ui_client.textEdit.toPlainText()
    send_to_addr = []
    
    if len(send_to) == 1 and send_to[0] == '':
        QtWidgets.QMessageBox.warning(MainWindow, '警告', '请输入要发送的用户名称！')
        return
    for user in send_to:
        if user not in [alive[0] for alive in alive_list]:
            QtWidgets.QMessageBox.warning(MainWindow, '警告', f'用户 [{user}] 不存在或不在线，请重新输入！')
            return 
        for alive in alive_list:
            if alive[0] == user:
                send_to_addr.append(alive[1])
    if send_info == '' or send_info is None:
        QtWidgets.QMessageBox.warning(MainWindow, '警告', '不能发送空白消息！')
        return
    
    if user_id not in send_to_addr:
        send_to_addr.append(UDP_ADDR)
        
    message_data = json.dumps({'sendfrom': user_id, 'time':server_time, 'text':send_info}).encode()
    for addr in send_to_addr:
        udp_client_1 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        udp_client_1.connect((addr[0],addr[1]))
        udp_client_1.send(message_data)
      
def run():
    global UDP_ADDR
    global udpSerSock
    global recv_thd
    
    HOST = '127.0.0.1'
    PORT = random.randint(20000,65535)
    UDP_ADDR = (HOST, PORT)

    udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    udpSerSock.bind(UDP_ADDR)

    recv_thd = RecvUDPMessageThread()
    recv_thd.update_data.connect(update_message_box)
    recv_thd.start()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    
    ui_login = Ui_Login()
    ui_client = Ui_Client()
    
    ui_login.setupUi(MainWindow)
    ui_login.pushButton.clicked.connect(button_login)
    
    run()
    MainWindow.show()
    sys.exit(app.exec_())
    