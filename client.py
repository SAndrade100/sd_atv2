import socket
import json
import os
import threading
from pathlib import Path

class NapsterClient:
    def __init__(self, server_host='localhost', server_port=1234, file_port=1235):
        self.server_host = server_host
        self.server_port = server_port
        self.file_port = file_port
        self.socket = None
        self.username = None
        self.shared_folder = "./public"
        self.file_server_socket = None
        self.running = True
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            print(f"Conectado ao servidor {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False
    
    def disconnect(self):
        self.running = False
        if self.socket:
            # Send LEAVE command before disconnecting
            try:
                self.socket.send("LEAVE\n".encode('utf-8'))
                response = self.socket.recv(1024).decode('utf-8').strip()
                if response == "CONFIRMLEAVE":
                    print("Desconexão confirmada pelo servidor")
            except:
                pass
            self.socket.close()
            print("Desconectado do servidor")
        if self.file_server_socket:
            self.file_server_socket.close()
            print("Servidor de arquivos encerrado")
    
    def send_command(self, command):
        """Envia comando de texto simples para o servidor"""
        try:
            self.socket.send(f"{command}\n".encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8').strip()
            return response
        except Exception as e:
            print(f"Erro na comunicação: {e}")
            return None
    
    def join_server(self, username):
        """Envia comando JOIN para registrar no servidor"""
        response = self.send_command(f"JOIN {username}")
        if response == "CONFIRMJOIN":
            self.username = username
            print(f"Usuário {username} registrado com sucesso!")
            # Automatically share files after joining
            self.auto_share_files()
            return True
        else:
            print(f"Erro ao registrar: {response}")
            return False
    
    def setup_public_folder(self):
        """Cria a pasta /public se não existir"""
        if not os.path.exists(self.shared_folder):
            os.makedirs(self.shared_folder)
            print(f"Pasta {self.shared_folder} criada")
        
    def scan_files(self):
        """Escaneia arquivos na pasta /public"""
        self.setup_public_folder()
        
        files = []
        try:
            for file_path in Path(self.shared_folder).rglob('*'):
                if file_path.is_file():
                    stat = file_path.stat()
                    file_info = {
                        "name": file_path.name,
                        "size": stat.st_size,
                        "path": str(file_path.relative_to(self.shared_folder)),
                        "extension": file_path.suffix
                    }
                    files.append(file_info)
        except Exception as e:
            print(f"Erro ao escanear arquivos: {e}")
        
        return files
    
    def create_file(self, filename, size):
        """Envia comando CREATEFILE para o servidor"""
        response = self.send_command(f"CREATEFILE {filename} {size}")
        if response.startswith("CONFIRMCREATEFILE"):
            print(f"Arquivo {filename} registrado no servidor")
            return True
        else:
            print(f"Erro ao registrar arquivo: {response}")
            return False
    
    def delete_file(self, filename):
        """Envia comando DELETEFILE para o servidor"""
        response = self.send_command(f"DELETEFILE {filename}")
        if response.startswith("CONFIRMDELETEFILE"):
            print(f"Arquivo {filename} removido do servidor")
            return True
        else:
            print(f"Erro ao remover arquivo: {response}")
            return False
    
    def auto_share_files(self):
        """Compartilha automaticamente arquivos da pasta /public"""
        files = self.scan_files()
        if files:
            success_count = 0
            for file_info in files:
                if self.create_file(file_info['name'], file_info['size']):
                    success_count += 1
            print(f"Compartilhados {success_count}/{len(files)} arquivos da pasta /public")
        else:
            print("Nenhum arquivo encontrado na pasta /public")
    
    def start_file_server(self):
        """Inicia servidor para envio de arquivos na porta 1235"""
        try:
            self.file_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.file_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.file_server_socket.bind(('', self.file_port))
            self.file_server_socket.listen(5)
            
            print(f"Servidor de arquivos iniciado na porta {self.file_port}")
            
            while self.running:
                try:
                    client_socket, address = self.file_server_socket.accept()
                    if not self.running:
                        break
                    print(f"Solicitação de arquivo de {address}")
                    
                    file_thread = threading.Thread(
                        target=self.handle_file_request,
                        args=(client_socket, address)
                    )
                    file_thread.start()
                except Exception as e:
                    if self.running:
                        print(f"Erro no servidor de arquivos: {e}")
                    break
                    
        except Exception as e:
            print(f"Erro ao iniciar servidor de arquivos: {e}")
    
    def handle_file_request(self, client_socket, address):
        """Lida com solicitações de download usando protocolo GET"""
        try:
            # Recebe comando GET
            command = client_socket.recv(1024).decode('utf-8').strip()
            print(f"Comando recebido: {command}")
            
            if command.startswith("GET"):
                parts = command.split()
                if len(parts) < 3:
                    client_socket.send("ERROR Invalid command format".encode('utf-8'))
                    return
                
                filename = parts[1]
                offset_start = int(parts[2])
                offset_end = None
                
                # Verifica se há OFFSET END
                if len(parts) >= 4:
                    offset_end = int(parts[3])
                
                file_path = Path(self.shared_folder) / filename
                
                if file_path.exists() and file_path.is_file():
                    file_size = file_path.stat().st_size
                    
                    # Validar offsets
                    if offset_start < 0 or offset_start >= file_size:
                        client_socket.send("ERROR Invalid offset start".encode('utf-8'))
                        return
                    
                    if offset_end is None:
                        offset_end = file_size
                    elif offset_end > file_size or offset_end <= offset_start:
                        client_socket.send("ERROR Invalid offset end".encode('utf-8'))
                        return
                    
                    # Calcula tamanho a ser enviado
                    bytes_to_send = offset_end - offset_start
                    
                    # Envia confirmação com tamanho
                    client_socket.send(f"OK {bytes_to_send}".encode('utf-8'))
                    
                    # Envia o arquivo com offset
                    with open(file_path, 'rb') as f:
                        f.seek(offset_start)
                        sent = 0
                        while sent < bytes_to_send:
                            chunk_size = min(1024, bytes_to_send - sent)
                            data = f.read(chunk_size)
                            if not data:
                                break
                            client_socket.send(data)
                            sent += len(data)
                    
                    print(f"Arquivo {filename} enviado para {address} (bytes {offset_start}-{offset_end})")
                else:
                    client_socket.send("ERROR File not found".encode('utf-8'))
                    print(f"Arquivo {filename} não encontrado")
            else:
                client_socket.send("ERROR Unknown command".encode('utf-8'))
                
        except Exception as e:
            print(f"Erro ao enviar arquivo: {e}")
            try:
                client_socket.send("ERROR Internal server error".encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()
    
    def download_file(self, ip_address, filename, offset_start=0, offset_end=None):
        """Baixa arquivo usando protocolo GET com offsets"""
        try:
            download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            download_socket.connect((ip_address, self.file_port))
            
            # Monta comando GET
            if offset_end is not None:
                command = f"GET {filename} {offset_start} {offset_end}"
            else:
                command = f"GET {filename} {offset_start}"
            
            # Envia comando
            download_socket.send(command.encode('utf-8'))
            
            # Recebe resposta
            response = download_socket.recv(1024).decode('utf-8')
            if response.startswith("OK"):
                bytes_to_receive = int(response.split()[1])
                
                # Cria pasta downloads se não existir
                downloads_folder = "./downloads"
                if not os.path.exists(downloads_folder):
                    os.makedirs(downloads_folder)
                
                # Nome do arquivo com sufixo se for download parcial
                if offset_start > 0 or offset_end is not None:
                    file_path = Path(downloads_folder) / f"{filename}.part_{offset_start}_{offset_end or 'end'}"
                else:
                    file_path = Path(downloads_folder) / filename
                
                # Recebe e salva o arquivo
                with open(file_path, 'wb') as f:
                    received = 0
                    while received < bytes_to_receive:
                        data = download_socket.recv(min(1024, bytes_to_receive - received))
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                
                print(f"Arquivo {filename} baixado com sucesso em {file_path}")
                print(f"Bytes baixados: {received} de {bytes_to_receive}")
                return True
            else:
                print(f"Erro ao baixar arquivo: {response}")
                return False
                
        except Exception as e:
            print(f"Erro no download: {e}")
            return False
        finally:
            download_socket.close()
    
    def get_user_info(self, ip_address):
        message = {
            "command": "GET_USER_INFO",
            "ip_address": ip_address
        }
        response = self.send_message(message)
        
        if response.get("status") == "success":
            files = response.get("files", [])
            print(f"\n=== ARQUIVOS DE {ip_address} ===")
            for i, file_info in enumerate(files, 1):
                print(f"{i}. {file_info['filename']}")
                print(f"   Tamanho: {file_info['size']} bytes")
                print("-" * 40)
        else:
            print(f"Erro: {response.get('message')}")
    
    def run_interactive(self):
        if not self.connect():
            return
        
        print("\n=== CLIENTE NAPSTER ===")
        username = input("Digite seu nome de usuário: ")
        
        if not self.join_server(username):
            self.disconnect()
            return
        
        # Inicia servidor de arquivos em thread separada
        file_server_thread = threading.Thread(target=self.start_file_server)
        file_server_thread.daemon = True
        file_server_thread.start()
        
        while True:
            print("\n=== MENU ===")
            print("1. Compartilhar arquivos da pasta /public")
            print("2. Listar todos os arquivos")
            print("3. Buscar arquivos")
            print("4. Remover arquivo do servidor")
            print("5. Sair")
            
            choice = input("Escolha uma opção: ").strip()
            
            if choice == '1':
                self.auto_share_files()
            
            elif choice == '2':
                self.list_all_files()
            
            elif choice == '3':
                query = input("Digite o termo de busca: ").strip()
                if query:
                    self.search_files(query)
            
            elif choice == '4':
                filename = input("Digite o nome do arquivo para remover: ").strip()
                if filename:
                    self.delete_file(filename)
            
            elif choice == '5':
                break
            
            else:
                print("Opção inválida!")
        
        self.disconnect()

if __name__ == "__main__":
    client = NapsterClient()
    client.run_interactive()
