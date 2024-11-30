import socket
import os

# Чтение fboot файла
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
file_path = os.path.join(parent_dir, 'testProject_FORTE_PC.fboot')
print("Путь к файлу:", file_path)

file = open(file_path, 'r')

# Создание сокета
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Подключение к серверу
server_address = ('localhost', 61499)
client_socket.connect(server_address)

# Отправка данных
# while True:
#     message = file.readline()
#     if not message:
#         break
#     client_socket.sendall(message.encode())
#     # Получение ответа
#     try:
#         client_socket.settimeout(10.0)
#         response = client_socket.recv(2)
#         print(f'Received: {response.decode()}')
#
#     except socket.timeout:
#         print("Таймаут: ожидание данных...")
#         continue

for i in range(1):
    message = '<Request ID="0" Action="QUERY"><FB NAME="*" Type="*"/></Request>'
    if not message:
        break
    client_socket.sendall(message.encode())
    # Получение ответа
    try:
        client_socket.settimeout(10.0)
        response = client_socket.recv(2)
        print(f'Received: {response.decode()}')

    except socket.timeout:
        print("Таймаут: ожидание данных...")
        continue


# Закрытие сокета
client_socket.close()
