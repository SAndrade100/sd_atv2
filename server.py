from napster_server import NapsterServer

def main():
    print("=== SERVIDOR NAPSTER ===")
    print("Instruções:")
    print("1. O servidor escutará na porta especificada (padrão: 1234)")
    print("2. Aguardará conexões de clientes")
    print("3. Use Ctrl+C para encerrar o servidor")
    print("-" * 50)
    
    host = input("Digite o host (Enter para localhost): ").strip() or 'localhost'
    port_input = input("Digite a porta (Enter para 1234): ").strip()
    port = int(port_input) if port_input else 1234
    
    server = NapsterServer(host, port)
    server.start()

if __name__ == "__main__":
    main()
