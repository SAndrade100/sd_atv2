import socket
import threading
import json
import os
from datetime import datetime

class NapsterServer:
    def __init__(self, host='localhost', port=1234):
        self.host = host
        self.port = port
        self.clients = {}  # {client_socket: {'ip_address': str, 'username': str}}
        self.all_files = {}  # {ip_address: [file_info]}
        
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        print(f"Servidor iniciado em {self.host}:{self.port}")
        print("Aguardando conexões...")
        
        try:
            while True:
                client_socket, address = server_socket.accept()
                print(f"Nova conexão de {address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\nServidor sendo encerrado...")
        finally:
            server_socket.close()
    
    def handle_client(self, client_socket, address):
        ip_address = address[0]
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    message = json.loads(data)
                    response = self.process_message(client_socket, ip_address, message)
                    client_socket.send(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    error_response = {"status": "error", "message": "Formato de mensagem inválido"}
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except Exception as e:
            print(f"Erro ao lidar com cliente {address}: {e}")
        finally:
            self.user_leave(ip_address)
            client_socket.close()
            print(f"Cliente {address} desconectado")
    
    def process_message(self, client_socket, ip_address, message):
        command = message.get('command')
        
        if command == 'REGISTER':
            return self.register_user(client_socket, ip_address, message)
        elif command == 'SHARE_FILES':
            return self.share_files(ip_address, message)
        elif command == 'LIST_FILES':
            return self.list_files()
        elif command == 'SEARCH_FILES':
            return self.search_files(message)
        elif command == 'GET_USER_INFO':
            return self.get_user_info(message)
        else:
            return {"status": "error", "message": "Comando não reconhecido"}
    
    def register_user(self, client_socket, ip_address, message):
        username = message.get('username')
        if not username:
            return {"status": "error", "message": "Nome de usuário obrigatório"}
        
        self.clients[client_socket] = {'ip_address': ip_address, 'username': username}
        
        # Initialize empty file list for this IP if not exists
        if ip_address not in self.all_files:
            self.all_files[ip_address] = []
        
        return {"status": "success", "message": f"Usuário {username} registrado com sucesso"}
    
    def add_file(self, ip_address: str, file: dict):
        """Adiciona um arquivo para o IP especificado"""
        # Testar se esse IP ja possui algum arquivo
        if ip_address not in self.all_files:
            self.all_files[ip_address] = []
        
        # Adicionar o arquivo na lista
        self.all_files[ip_address].append(file)
    
    def share_files(self, ip_address, message):
        files = message.get('files', [])
        
        # Clear existing files for this IP
        self.all_files[ip_address] = []
        
        # Add each file using the specified structure
        for file_info in files:
            file_entry = {
                "filename": file_info.get('name'),
                "size": file_info.get('size')
            }
            self.add_file(ip_address, file_entry)
        
        return {"status": "success", "message": f"{len(files)} arquivos compartilhados"}
    
    def list_files(self):
        """Lista todos os arquivos de todos os usuários"""
        all_files_list = []
        for ip_address in self.all_files.keys():
            for file in self.all_files[ip_address]:
                file_entry = {
                    "ip_address": ip_address,
                    "filename": file["filename"],
                    "size": file["size"]
                }
                all_files_list.append(file_entry)
        
        return {"status": "success", "files": all_files_list}
    
    def search(self, pattern: str):
        """Busca arquivos que contenham o padrão especificado"""
        result = []
        for ip_address in self.all_files.keys():
            for file in self.all_files[ip_address]:
                if pattern in file["filename"]:
                    result.append({
                        "ip_address": ip_address,
                        "filename": file["filename"],
                        "size": file["size"]
                    })
        
        return result
    
    def search_files(self, message):
        query = message.get('query', '').lower()
        results = self.search(query)
        
        return {"status": "success", "files": results}
    
    def get_user_info(self, message):
        ip_address = message.get('ip_address')
        if ip_address and ip_address in self.all_files:
            return {
                "status": "success", 
                "ip_address": ip_address,
                "files": self.all_files[ip_address]
            }
        else:
            return {"status": "error", "message": "IP não encontrado"}
    
    def user_leave(self, ip_address: str):
        """Remove todos os arquivos quando usuário se desconecta"""
        if ip_address in self.all_files:
            del self.all_files[ip_address]
            print(f"Arquivos do IP {ip_address} removidos da memória")
        
        # Remove from clients dict
        client_to_remove = None
        for client_socket, client_info in self.clients.items():
            if client_info['ip_address'] == ip_address:
                client_to_remove = client_socket
                break
        
        if client_to_remove:
            del self.clients[client_to_remove]

if __name__ == "__main__":
    server = NapsterServer()
    server.start()
