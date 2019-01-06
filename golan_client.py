#===========================================================================
#==================   H A G A I ' S    C L I E N T    ======================
#===========================================================================
# Name of program: Mini PC Control Center.
# Description: This program is made for golan's challenge.
#              The purpose of the program is written in the PDF files.
# Programmer: Hagai Vinik .
# Date: 6/1/2019 .
# CopyRight (c) 2019 Hagai Vinik . All rights reserved.
#===========================================================================
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
import os


# Define values.
PORT = 5003
HOST = '127.0.0.1'
ADDR = (HOST, PORT)  # Address - host, port.
PORT_KEEP_ALIVE = 5002
HOST_KEEP_ALIVE = '127.0.0.1'
ADDR_KEEP_ALIVE = (HOST_KEEP_ALIVE, PORT_KEEP_ALIVE) #Adress for keep alive msgs.
BUF_SIZE = 2048


class GolanClient():
    def __init__(self):
        # Initialize connection.
        # Variables: my_socket, keep_ alive socket.
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.connect(ADDR)
        self.my_keep_alive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_keep_alive_socket.connect(ADDR_KEEP_ALIVE)
        self.flag = True

        # Code:
        if self.my_socket and self.my_keep_alive_socket:
            my_thread = threading.Thread(target=self.keep_alive_msgs)
            my_thread2 = threading.Thread(target= self.sign_client())
            my_thread2.start()
            my_thread.start()
        else:
            print("couldn't connect to server, please try again later")
            return

    def sign_client(self):
        # Sign in/up client.
        # Options - Register , Connect.
        list_of_options  =   [None, "Connect:", "Register:"]
        flag             =    True

        # Code:
        while flag:
            print("hello user, please choose one of the options( '1' or '2') bellow:")
            print("1. sign in, connect.")
            print("2. sign up, register.")
            user_choice = input("waiting for input: ")
            # Input verification.
            if user_choice == '1' or user_choice == '2':
                flag = False
            else:
                print("please enter a valid number(1 / 2)")
        # Convert input str to int.
        user_choice = int(user_choice)

        # Input user details.
        print("please enter your user name:")
        user_name = input("user name: ")  # Input user name.
        print("please enter your password:")
        user_password = input("password: ")   # Input user password.

        # Build message and Send to server: request + user details.
        message = list_of_options[user_choice] + user_name + ' ' + user_password
        try:
            self.my_socket.send(message.encode("utf-8"))
        except:
            return
        # Server response + handle disconnection.
        try:
            server_msg = (self.my_socket.recv(BUF_SIZE)).decode("utf-8")
        except socket.error:
            print("Error: Connection failed")
            return
        # Handle response.
        print("server response: " + server_msg)
        if server_msg == 'OK:success':
            print("OK: action succeed")
            self.handle_client(user_name)  # GO TO: handle client requests, parameter (user name ).
        elif server_msg == 'FAIL:error':
            print("ERROR: user action failed")
            self.my_socket.close()
            self.my_keep_alive_socket.close()
            return
        else:
            print("ERROR: server returned corrupted message, program being aborted.")
            self.my_socket.close()
            return

    def handle_client(self, user_name):
        # Handle client requests with menu for user.
        list_of_options = [None, 'Time', 'Name', 'Screenshot', 'Word',
                           'Excel', None, 'Exit', 'stop_keep_alive']
        Name_of_server = 'server'  #default
        # Code:
        print("handle client")
        list_of_options = [None, 'Time', None, 'Screenshot', 'Word',
                           'Excel', None, 'Exit','stop_keep_alive']
        # user menu.
        while True:
            print("Hello " + user_name + " and welcome to Golans PC control.")
            print("please choose one option from bellow:")
            print("1. TIME.")
            print("2. NAME.")
            print("3. SCREENSHOT.")
            print("4. OPEN Microsoft Word 2013 program at the server's system.")
            print("5. OPEN Microsoft Excel 2013 program at the server's system.")
            print("6.OPEN DIRECTORY. (Format: 'DIR!NameOfDirectory.) ('Example: 'DIR!D:\Hagai')")
            print("7. EXIT.")
            print("8. STOP KEEP ALIVE.")
            user_input = input("enter your choice(1-7):")
            # input verification + convert input str to int.
            try:
                user_input = int(user_input)
            except ValueError:
                print("please enter a number not a letter! (1-7)")
            if user_input > 8 or user_input < 1:
                print("please enter a valid number! (1-7)")

            # handle user request:
            else:
                if user_input == 6:  #OPEN DIRECTORY.
                    msg = 'DIR!'
                    msg = msg + input("enter path: ")
                    self.my_socket.send(msg.encode("utf-8"))
                    server_msg = self.my_socket.recv(BUF_SIZE).decode("utf-8")
                    print("server answer: " + server_msg)

                elif user_input == 3:   #SCREENSHOT.
                    print("receiving picture from server.....")
                    if not os.path.exists(Name_of_server):
                        os.mkdir(str(Name_of_server))
                    file = open(os.path.join(Name_of_server, "scrnshot_server.png"), "wb")
                    self.my_socket.send("Screenshot".encode("utf-8"))
                    server_msg = self.my_socket.recv(40960000)
                    file.write(server_msg)
                    file.close()
                    print("picture received successfully.")

                elif user_input == 2:
                    self.my_socket.send("Name".encode("utf-8"))
                    Name_of_server = self.my_socket.recv(BUF_SIZE).decode("utf-8")
                    print("server Name: " + Name_of_server)

                else:
                    try:
                        self.my_socket.send(list_of_options[user_input].encode("utf-8"))
                    except:
                        return
                    # server response.
                    try:
                        server_msg = self.my_socket.recv(BUF_SIZE).decode("utf-8")
                        print("server answer: " + server_msg)
                    except ConnectionAbortedError:
                        return

                    # handle Exit request - server response 'ByeBye'
                    if server_msg == "ByeBye":
                        self.my_socket.close()
                        return

    def keep_alive_msgs(self):
        while True:
            self.my_keep_alive_socket.settimeout(10.0)
            try:
                data = self.my_keep_alive_socket.recv(BUF_SIZE).decode("utf-8")
                #print("connection status: " + data)
            except :
                print("connection timed out, closing program.")
                self.my_keep_alive_socket.close()
                self.my_socket.close()
                break
            if not data:
                print("no data, closing program.")
                self.my_keep_alive_socket.close()
                self.my_socket.close()
                break

        print("exit.")
        return


if __name__ == '__main__':  # start program.
    GolanClient()
