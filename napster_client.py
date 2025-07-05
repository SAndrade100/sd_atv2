import socket
import threading
from pathlib import Path
from protocol import NapsterProtocol, FileTransferProtocol
from file_handler import FileManager

class NapsterClient:
    def __init__(self, server_host='localhost', server_port=1234, file_port=1235):
        self.server_host = server_host
        self.server_port = server_port
        self.file_port = file_port
        self.socket = None
        self.username = None
        self.file_manager = FileManager()
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
            try:
                response = NapsterProtocol.send_command(self.socket, "LEAVE")
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
        try:
            self.socket.send(f"{command}\n".encode('utf-8'))
            response = self.socket.recv(4096).decode('utf-8').strip()
            return response
        except Exception as e:
            print(f"Erro na comunicação: {e}")
            return None
    
    def join_server(self, username):
        response = NapsterProtocol.send_command(self.socket, f"JOIN {username}")
        if response == "CONFIRMJOIN":
            self.username = username
            print(f"Usuário {username} registrado com sucesso!")
            self.auto_share_files()
            return True
        else:
            print(f"Erro ao registrar: {response}")
            return False
    
    def create_file(self, filename, size):
        response = NapsterProtocol.send_command(self.socket, f"CREATEFILE {filename} {size}")
        if response and response.startswith("CONFIRMCREATEFILE"):
            return True
        return False
    
    def delete_file(self, filename):
        response = NapsterProtocol.send_command(self.socket, f"DELETEFILE {filename}")
        if response and response.startswith("CONFIRMDELETEFILE"):
            print(f"Arquivo {filename} removido do servidor")
            return True
        return False
    
    def auto_share_files(self):
        files = self.file_manager.scan_files()
        if files:
            success_count = 0
            for file_info in files:
                if self.create_file(file_info['name'], file_info['size']):
                    success_count += 1
            print(f"Compartilhados {success_count}/{len(files)} arquivos da pasta /public")
        else:
            print("Nenhum arquivo encontrado na pasta /public")
    
    def search_files(self, query):
        response = NapsterProtocol.send_command(self.socket, f"SEARCH {query}")
        files = NapsterProtocol.parse_file_response(response)
        
        if files:
            print(f"\n=== RESULTADOS PARA '{query}' ===")
            for i, file_info in enumerate(files, 1):
                print(f"{i}. {file_info['filename']}")
                print(f"   IP: {file_info['ip_address']}")
                print(f"   Tamanho: {file_info['size']} bytes")
                print("-" * 40)
            
            choice = input("\nDeseja baixar algum arquivo? (digite o número ou 'n' para não): ").strip()
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(files):
                    file_to_download = files[index]
                    self._handle_download_options(file_to_download)
        else:
            print(f"Nenhum arquivo encontrado para '{query}'")
    
    def _handle_download_options(self, file_info):
        print("\nOpções de download:")
        print("1. Arquivo completo")
        print("2. Download com offset")
        
        download_choice = input("Escolha uma opção: ").strip()
        
        if download_choice == "1":
            self.download_file(file_info['ip_address'], file_info['filename'])
        elif download_choice == "2":
            try:
                offset_start = int(input("Digite o offset inicial: "))
                offset_end_input = input("Digite o offset final (ou Enter para até o fim): ").strip()
                offset_end = int(offset_end_input) if offset_end_input else None
                
                self.download_file(
                    file_info['ip_address'], 
                    file_info['filename'],
                    offset_start,
                    offset_end
                )
            except ValueError:
                print("Valores de offset inválidos")
    
    def download_file(self, ip_address, filename, offset_start=0, offset_end=None):
        try:
            download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            download_socket.connect((ip_address, self.file_port))
            
            FileTransferProtocol.send_get_command(download_socket, filename, offset_start, offset_end)
            
            response = download_socket.recv(1024).decode('utf-8')
            if response.startswith("OK"):
                bytes_to_receive = int(response.split()[1])
                
                if offset_start > 0 or offset_end is not None:
                    save_filename = f"{filename}.part_{offset_start}_{offset_end or 'end'}"
                else:
                    save_filename = filename
                
                with self.file_manager.write_file_incrementally(save_filename) as f:
                    received = 0
                    while received < bytes_to_receive:
                        data = download_socket.recv(min(1024, bytes_to_receive - received))
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                
                print(f"Arquivo {filename} baixado com sucesso como {save_filename}")
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
    
    def start_file_server(self):
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
        try:
            command = client_socket.recv(1024).decode('utf-8').strip()
            
            if command.startswith("GET"):
                filename, offset_start, offset_end = FileTransferProtocol.parse_get_command(command)
                
                if filename is None:
                    FileTransferProtocol.send_response(client_socket, "ERROR Invalid command format")
                    return
                
                if self.file_manager.file_exists(filename):
                    file_size = self.file_manager.get_file_size(filename)
                    
                    if offset_start < 0 or offset_start >= file_size:
                        FileTransferProtocol.send_response(client_socket, "ERROR Invalid offset start")
                        return
                    
                    if offset_end is None:
                        offset_end = file_size
                    elif offset_end > file_size or offset_end <= offset_start:
                        FileTransferProtocol.send_response(client_socket, "ERROR Invalid offset end")
                        return
                    
                    bytes_to_send = offset_end - offset_start
                    
                    FileTransferProtocol.send_response(client_socket, f"OK {bytes_to_send}")
                    
                    data = self.file_manager.read_file_chunk(filename, offset_start, bytes_to_send)
                    client_socket.send(data)
                    
                    print(f"Arquivo {filename} enviado para {address} (bytes {offset_start}-{offset_end})")
                else:
                    FileTransferProtocol.send_response(client_socket, "ERROR File not found")
            else:
                FileTransferProtocol.send_response(client_socket, "ERROR Unknown command")
                
        except Exception as e:
            print(f"Erro ao enviar arquivo: {e}")
            try:
                FileTransferProtocol.send_response(client_socket, "ERROR Internal server error")
            except:
                pass
        finally:
            client_socket.close()
    
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