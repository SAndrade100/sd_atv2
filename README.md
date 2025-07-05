# Sistema de Compartilhamento de Arquivos - Napster (Modular)

Este projeto implementa um sistema de compartilhamento de arquivos baseado no protocolo Napster usando sockets Python, com arquitetura modular.

## Estrutura do Projeto

```
sd_atv2/
├── server.py              # Ponto de entrada do servidor
├── client.py              # Ponto de entrada do cliente
├── napster_server.py      # Implementação do servidor
├── napster_client.py      # Implementação do cliente
├── protocol.py            # Protocolo de comunicação
├── file_handler.py        # Gerenciamento de arquivos
├── public/                # Pasta de arquivos compartilhados (criada automaticamente)
├── downloads/             # Pasta de downloads (criada automaticamente)
└── README.md              # Este arquivo
```

## Como Executar

### 1. Executar o Servidor

```bash
cd "/home/samuel/Área de trabalho/Projetos/sd_atv2"
python server.py
```

O servidor:
- Perguntará o host (padrão: localhost)
- Perguntará a porta (padrão: 1234)
- Ficará aguardando conexões de clientes
- Use `Ctrl+C` para encerrar

### 2. Executar Cliente(s)

Em um novo terminal:

```bash
cd "/home/samuel/Área de trabalho/Projetos/sd_atv2"
python client.py
```

Cada cliente:
- Se conectará ao servidor na porta 1234
- Pedirá um nome de usuário
- Automaticamente compartilhará arquivos da pasta `./public`
- Iniciará servidor de arquivos na porta 1235
- Mostrará menu interativo

### 3. Exemplo de Uso Completo

**Terminal 1 - Servidor:**
```bash
python server.py
```

**Terminal 2 - Cliente 1:**
```bash
python client.py
```

**Terminal 3 - Cliente 2:**
```bash
python client.py
```

## Exemplo de Teste

1. **Prepare arquivos de teste:**
```bash
mkdir -p public
echo "Hello World" > public/test.txt
echo "Sample data" > public/sample.dat
```

2. **Execute servidor:**
```bash
python server.py
```

3. **Execute cliente 1:**
```bash
python client.py
# Você terá de escolher um nome
```

4. **Execute cliente 2:**
```bash
python client.py  
# Use um nome diferente do primeiro pra identificação
```

5. **Verifique downloads:**
```bash
ls downloads/
```

## Troubleshooting

- **Erro "Address already in use"**: Aguarde alguns segundos e tente novamente
- **Erro de conexão**: Verifique se o servidor está rodando
- **Arquivos não aparecem**: Verifique se estão na pasta `./public`
- **Download falha**: Verifique se o cliente que tem o arquivo ainda está conectado
- **AttributeError métodos não encontrados**: Certifique-se de que todos os módulos foram criados corretamente
- **Erro de import**: Verifique se todos os arquivos estão no mesmo diretório
