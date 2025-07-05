import socket
import threading
from protocol import NapsterProtocol

class NapsterServer:
    def __init__(self, host='localhost', port=1234):
        self.host = host
        self.port = port
        self.clients = {}  
        self.all_files = {}  
        self.running = True
        
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        print(f"Servidor iniciado em {self.host}:{self.port}")
        print("Aguardando conexões...")
        
        try:
            while self.running:
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
            self.running = False
            server_socket.close()
    
    def handle_client(self, client_socket, address):
        ip_address = address[0]
        try:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break
                
                response = self.process_command(client_socket, ip_address, data)
                if response:
                    client_socket.send(response.encode('utf-8'))
                    
        except Exception as e:
            print(f"Erro ao lidar com cliente {address}: {e}")
        finally:
            self.user_leave(ip_address)
            client_socket.close()
            print(f"Cliente {address} desconectado")
    
    def process_command(self, client_socket, ip_address, command):
        parts = command.split()
        if not parts:
            return "ERROR Invalid command"
        
        cmd = parts[0]
        
        if cmd == 'JOIN':
            return self.handle_join(client_socket, ip_address, parts)
        elif cmd == 'CREATEFILE':
            return self.handle_create_file(ip_address, parts)
        elif cmd == 'DELETEFILE':
            return self.handle_delete_file(ip_address, parts)
        elif cmd == 'SEARCH':
            return self.handle_search(parts)
        elif cmd == 'LEAVE':
            return self.handle_leave(ip_address)
        else:
            return "ERROR Unknown command"
    
    def handle_join(self, client_socket, ip_address, parts):
        if len(parts) < 2:
            return "ERROR Username required"
        
        username = parts[1]
        self.clients[client_socket] = {'ip_address': ip_address, 'username': username}
        
        if ip_address not in self.all_files:
            self.all_files[ip_address] = []
        
        return "CONFIRMJOIN"
    
    def handle_create_file(self, ip_address, parts):
        if len(parts) < 3:
            return "ERROR Invalid CREATEFILE format"
        
        filename = parts[1]
        size = int(parts[2])
        
        if ip_address not in self.all_files:
            self.all_files[ip_address] = []
        
        self.all_files[ip_address] = [f for f in self.all_files[ip_address] if f['filename'] != filename]
        
        self.all_files[ip_address].append({
            'filename': filename,
            'size': size
        })
        
        return f"CONFIRMCREATEFILE {filename}"
    
    def handle_delete_file(self, ip_address, parts):
        if len(parts) < 2:
            return "ERROR Invalid DELETEFILE format"
        
        filename = parts[1]
        
        if ip_address in self.all_files:
            self.all_files[ip_address] = [f for f in self.all_files[ip_address] if f['filename'] != filename]
        
        return f"CONFIRMDELETEFILE {filename}"
    
    def handle_search(self, parts):
        pattern = parts[1].lower() if len(parts) > 1 else ""
        results = []
        
        for ip_address in self.all_files.keys():
            for file in self.all_files[ip_address]:
                if pattern in file['filename'].lower():
                    results.append(f"FILE {file['filename']} {ip_address} {file['size']}")
        
        return '\n'.join(results) if results else ""
    
    def handle_leave(self, ip_address):
        self.user_leave(ip_address)
        return "CONFIRMLEAVE"
    
    def user_leave(self, ip_address):
        if ip_address in self.all_files:
            del self.all_files[ip_address]
            print(f"Arquivos do IP {ip_address} removidos da memória")
        
        client_to_remove = None
        for client_socket, client_info in self.clients.items():
            if client_info['ip_address'] == ip_address:
                client_to_remove = client_socket
                break
        
        if client_to_remove and client_to_remove in self.clients:
            del self.clients[client_to_remove]
