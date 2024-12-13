import socket
import os
import struct


class TcpFileSender():
    def __init__(self, file_path):
        # Создание сокета
        self.file_path = file_path
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.set_connection()
        self.send_fboot()
        self.disconnect()

    def set_connection(self):
        # Подключение к серверу
        server_address = ('localhost', 61499)
        self.client_socket.connect(server_address)

    def disconnect(self):
        # Закрытие сокета
        self.client_socket.close()

    def send_fboot(self):
        # Чтение fboot файла
        # parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        # file_path = os.path.join(parent_dir, self.file_path)
        
        print("File path:", self.file_path)
        file = open(self.file_path, 'r')

        while True:
            message = file.readline()[:-1]
            if not message:
                break

            # Обработка строки с сообщением
            separator = message.find(';')
            res_name = message[:separator]
            xml_com = message[separator + 1:]
            res_name_length = struct.pack('h', separator)[::-1]
            xml_com_length = struct.pack('h', len(xml_com))[::-1]
            message = '\x50' + res_name_length.decode() + res_name + '\x50' + xml_com_length.decode() + xml_com
            # print(message)

            # Отправка данных
            self.client_socket.sendall(message.encode())

            # Получение ответа
            try:
                self.client_socket.settimeout(10.0)
                response = self.client_socket.recv(1024)
                print(f'Received: {response.decode()}\n')

            except socket.timeout:
                print("Таймаут: ожидание данных...")
                continue


if __name__ == '__main__':
    tcp_file_sender = TcpFileSender('../k.fboot')
    # tcp_file_sender.set_connection()
    # tcp_file_sender.send_fboot()
    # tcp_file_sender.disconnect()
