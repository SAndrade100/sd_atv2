import socket

class NapsterProtocol:
    
    @staticmethod
    def send_command(sock, command):
        try:
            sock.send(f"{command}\n".encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            return response
        except Exception as e:
            print(f"Erro na comunicação: {e}")
            return None
    
    @staticmethod
    def parse_file_response(response):
        files = []
        if not response:
            return files
            
        lines = response.split('\n')
        for line in lines:
            if line.startswith("FILE"):
                parts = line.split()
                if len(parts) >= 4:
                    filename = parts[1]
                    ip_address = parts[2]
                    size = parts[3]
                    files.append({
                        'filename': filename,
                        'ip_address': ip_address,
                        'size': int(size)
                    })
        return files

class FileTransferProtocol:
    
    @staticmethod
    def send_get_command(sock, filename, offset_start=0, offset_end=None):
        if offset_end is not None:
            command = f"GET {filename} {offset_start} {offset_end}"
        else:
            command = f"GET {filename} {offset_start}"
        
        sock.send(command.encode('utf-8'))
    
    @staticmethod
    def parse_get_command(command):
        parts = command.split()
        if len(parts) < 3:
            return None, None, None
        
        filename = parts[1]
        offset_start = int(parts[2])
        offset_end = int(parts[3]) if len(parts) >= 4 else None
        
        return filename, offset_start, offset_end
    
    @staticmethod
    def send_response(sock, message):
        sock.send(message.encode('utf-8'))
    
    @staticmethod
    def receive_data(sock, size):
        data = b''
        while len(data) < size:
            chunk = sock.recv(min(size - len(data), 1024))
            if not chunk:
                break
            data += chunk
        return data
