# Sistema de Compartilhamento de Arquivos - Napster

Este projeto implementa um sistema de compartilhamento de arquivos baseado no protocolo Napster usando sockets Python.

## Estrutura do Projeto

- `server.py`: Servidor central que gerencia usuários e arquivos
- `client.py`: Cliente que se conecta ao servidor e compartilha arquivos

## Como Executar

### 1. Iniciar o Servidor

```bash
python server.py
```

O servidor iniciará na porta 8888 por padrão.

### 2. Conectar Clientes

```bash
python client.py
```

Cada cliente pode:
- Registrar um nome de usuário
- Definir pasta de arquivos compartilhados
- Listar arquivos de todos os usuários
- Buscar arquivos por nome
- Ver arquivos de usuários específicos

## Protocolo de Comunicação

O protocolo utiliza mensagens JSON com os seguintes comandos:

### Comandos do Cliente

- `REGISTER`: Registra usuário no servidor
- `SHARE_FILES`: Compartilha lista de arquivos
- `LIST_FILES`: Lista todos os arquivos disponíveis
- `SEARCH_FILES`: Busca arquivos por nome
- `GET_USER_INFO`: Obtém informações de usuário específico

### Formato das Mensagens

```json
{
  "command": "COMANDO",
  "username": "nome_usuario",
  "files": [...],
  "query": "termo_busca"
}
```

## Funcionalidades

- ✅ Registro de usuários
- ✅ Compartilhamento de informações de arquivos
- ✅ Listagem de arquivos disponíveis
- ✅ Busca por nome de arquivo
- ✅ Múltiplos clientes simultâneos
- ✅ Interface interativa

## Exemplo de Uso

1. Execute o servidor
2. Execute múltiplos clientes
3. Cada cliente registra um usuário único
4. Defina pastas para compartilhar
5. Compartilhe arquivos com o servidor
6. Liste e busque arquivos de outros usuários