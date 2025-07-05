import os
from pathlib import Path

class FileManager:
    
    def __init__(self, shared_folder="./public"):
        self.shared_folder = shared_folder
        self.setup_folders()
    
    def setup_folders(self):
        folders = [self.shared_folder, "./downloads"]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"Pasta {folder} criada")
    
    def scan_files(self):
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
    
    def get_file_path(self, filename):
        return Path(self.shared_folder) / filename
    
    def file_exists(self, filename):
        file_path = self.get_file_path(filename)
        return file_path.exists() and file_path.is_file()
    
    def get_file_size(self, filename):
        if self.file_exists(filename):
            return self.get_file_path(filename).stat().st_size
        return 0
    
    def read_file_chunk(self, filename, offset_start, bytes_to_read):
        file_path = self.get_file_path(filename)
        with open(file_path, 'rb') as f:
            f.seek(offset_start)
            return f.read(bytes_to_read)
    
    def write_file(self, filename, data, folder="./downloads"):
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_path = Path(folder) / filename
        with open(file_path, 'wb') as f:
            f.write(data)
        return file_path
    
    def write_file_incrementally(self, filename, folder="./downloads"):
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_path = Path(folder) / filename
        return open(file_path, 'wb')
