
#===========================================================================
#=================    H A G A I ' S    S E R V E R     =====================
#===========================================================================
# Name of program: Mini PC Control Center.
# Description: This program is made for golan's challenge.
# The purpose of the program is written in the PDF files.
# Programmer: Hagai Vinik .
# Date: 6/1/2019 .
# CopyRight (c) 2019 Hagai Vinik . All rights reserved.
#===========================================================================
#
#
#---------------------    Description Of Protocol:    ----------------------#
# 1.1. client Connect = 'Connect:<user name> <user password>.  example: Connect:hagai 1234
# 1.2. client Register = 'Register:<user name> <user password>. example: Register:hagai 1234
# 1.1 + 1.2. server answers: 'OK:success' or 'FAIL:error'.
# 2.0. client request: 1. 'Time'.  server answer: computer time.
# 2.1. client requests:  4. 'word' . 5. 'Excel'. server answers: 'OK:success' or 'FAIL,error'.
# 2.3. client request: 3. 'Screenshot'  server answer: send picture.
# 2.4. client request: 2. 'Name'.   server answer: computer name.
# 2.5. client request: 6. 'dir!<directory name>' . server answer: string of dir if exists else: 'FAIL:error'.
# 2.6. client request: 'exit'. server answer: 'ByeBye'.
# 2.7. client request: 'stop_keep alive'. server answer: 'OK:success'
# 3.0. server send: 'is_connected' .  (by another thread.)
#
#----------------------------------------------------------------------------#


# Import modules.
import socket
import threading
import time
import os
from mss import mss


# Define values.
PORT = 5003
HOST = '127.0.0.1'
ADDR = (HOST, PORT)
PORT_KEEP_ALIVE = 5002
HOST_KEEP_ALIVE = '127.0.0.1'
ADDR_KEEP_ALIVE = (HOST_KEEP_ALIVE, PORT_KEEP_ALIVE) #Adress for keep alive msgs.
BUF_SIZE = 2048
LOCK = False   # Lock of True or False, couldnwt install suitable API.


class GolanServer:
    def __init__(self):
        # Function Initialize file if not exists.
        # Code:
        if not os.path.exists("users&passwords.txt"):
            print("making file...")
            self.file = open("users&passwords.txt", "w")
            if self.file:
                print("file of users and passwords made successfully.")
            else:
                print("creating file failed.")
            self.file.close()
        self.start_socket()  # GO TO: start_socket - initialize socket. variables(None).

    def start_socket(self):
        # Function Initialize socket - starting server and wait for connection.
        # variables:
        global ADDR
        global ADDR_KEEP_ALIVE
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(ADDR)
        server_socket.listen(5)
        k_alive_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k_alive_server_socket.bind(ADDR_KEEP_ALIVE)
        k_alive_server_socket.listen(5)

        # Code:
        print("Server is runnnig on host = " + HOST + ", port = " + str(PORT))
        print("Server(Alive) is runnnig on host = " + HOST_KEEP_ALIVE + ", port = " + str(PORT_KEEP_ALIVE))
        while True:  # Keep waiting for new connection.
            (client_socket, ADDR) = server_socket.accept()
            (self.k_alive_client_socket, ADDR_KEEP_ALIVE) = k_alive_server_socket.accept()
            print("client =" + str(server_socket.getsockname()) + ',' + str(k_alive_server_socket.getsockname()) + " is connected")
            my_thread = threading.Thread(target=self.verify_client, args=(client_socket,ADDR))
            my_k_alive_thread = threading.Thread(target= self.k_alive_func)
            my_thread.start()  # Start thread verify_client - verify client details. variables(None)
            my_k_alive_thread.start()

    def verify_client(self, client_socket,ADDR):
        # Function receive data from client and act correspondingly.
        # Options: Register / Connect .
        # parameters: client_socket .
        # Local variables:
        error_message     =   'FAIL:error'.encode("utf-8")   # Success message for client.
        success_message   =   'OK:success'.encode("utf-8") # Error message for client.
        flag              =   False
        data              =   ''

        # Code:

        try:
            data = (client_socket.recv(BUF_SIZE)).decode("utf-8")  # Receive Data.
        except ConnectionResetError:
            print("ERROR exit1: connection with client failed")
            client_socket.close()
            return

        if not data:
            print("ERROR2 exit1: connection with client failed")
            client_socket.close()
            return

        print("data is- " + str(data))
        # handle user details.
        user_request    =   data.split(':')[0]
        user_details   =   data.split(':')[1]
        user_name      =   user_details.split(' ')[0]   # user name.
        user_password  =   user_details.split(' ')[1]   # user password.

        # =======  Handle Client Request (connect, register).  ======== #
        if   user_request == 'Connect':
            flag = self.connect(user_name,user_password)
        elif user_request == 'Register':
            flag = self.register(user_name,user_password)

        if flag:
            # Send to client success message.
            client_socket.send(success_message)
            self.answer_requests(client_socket)  # GO TO: answer_requests - of client. variables(client_socket).
        elif not flag:
            client_socket.send(error_message)
            client_socket.close()
            return

    def register(self, user_name, user_password):
        # function open file and write parameter details, return true if success.
        global LOCK
        while LOCK:
            pass
        LOCK = True  # using file.
        file = open("users&passwords.txt", "a")
        if not file:
            print("ERROR register: failed opening file users&passwords.")
            return False
        file.write(user_name + ":" + user_password + "\n")
        file.close()
        LOCK = False   #release file.
        print('added to system user:' + user_name + ', password:' + user_password)
        return True

    def connect(self, user_name, user_password):
        # function open file and compare parameters to details in file.
        global LOCK
        while LOCK:
            pass
        LOCK = True
        file = open("users&passwords.txt", "r")
        for line in file.readlines():
            line = line.split()[0]
            if user_name == line.split(':')[0]:
                if user_password == line.split(":")[1]:
                    print("CONNECT: " + user_name + " user found.")
                    file.close()
                    return True
        print("ERROR Connect: user not found!")
        file.close()
        LOCK = False
        return False

    def answer_requests(self, client_socket):
        # Function receive data from client and act correspondingly.
        # Options: Time / Name / Exit / Word / Excel / Dir / screenshot.
        # parameters: client_socket .
        # Local variables:
        dict_of_options = {'Time': self.time, 'Name': self.name ,
                           'Word': self.word, 'Excel': self.excel , 'stop_keep_alive': self.stop_keep_alive}
        error_message   =  'FAIL:error'.encode("utf-8")
        success_message =  'OK:success'.encode("utf-8")
        flag            =  True
        data            =  ''
        #Code:
        print("starting: answer client requests.")
        while flag:
            try:
                data = client_socket.recv(BUF_SIZE).decode("utf-8")
            except ConnectionResetError:
                print("Exception exit1: ConnectionResetError: client disconnected")
                client_socket.close()
                return
            if not data:
                print("exit1: connection with client failed")
                client_socket.close()
                return

            print("data is- " + data)
            if data == 'Exit':
                client_socket.send('ByeBye'.encode("utf-8"))
                client_socket.close()
                print("exit1 :client disconnected")
                self.stop_keep_alive()
                return

            elif data == "Screenshot":
                print('taking screenshot')
                with mss() as sct:
                    filename = sct.shot()
                    print(filename + " created.")
                file = open("monitor-1.png", "rb")
                buffer = file.read()
                file.close()
                client_socket.send(buffer)
                print("screenshot sended to client.")

            elif data.split('!')[0] == 'DIR':
                path1 = data.split('!')[1]
                if os.path.exists(path1):
                    l1 = os.listdir(path1)
                    print("path found. sending to client: " + str(l1))
                    client_socket.send(str(l1).encode("utf-8"))
                else:
                    print("Error:Dir not found")
                    client_socket.send(error_message)

            else:
                message = dict_of_options[data]()
                client_socket.send(message.encode("utf-8"))

    def stop_keep_alive(self):
        self.k_alive_client_socket.close()
        return 'OK:success'

    def time(self):
        my_time = time.strftime('%X')
        print("sending to client my time: " + my_time)
        return my_time

    def name(self):
        my_name = os.environ['COMPUTERNAME']
        print("sending client my name - " + my_name)
        return my_name

    def word(self):
        success_message = 'OK:success'
        error_message = 'FAIL:error'
        path = 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Microsoft Office 2013\Word 2013.lnk'
        try:
            os.startfile(path)
        except FileNotFoundError:
            print('opening word failed')
            return error_message
        else:
            return success_message

    def excel(self):
        success_message = 'OK:success'
        error_message = 'FAIL:error'
        path = 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Microsoft Office 2013\excel 2013.lnk'
        try:
            os.startfile(path)
        except FileNotFoundError:
            print('opening word failed')
            return error_message
        return success_message

    def k_alive_func(self):
        while True:
            try:
                self.k_alive_client_socket.send("is_connected".encode("utf-8"))
                time.sleep(5)
            except:
                print("exit2: keep alive has being closed.")
                return


if __name__ == '__main__':
    GolanServer()