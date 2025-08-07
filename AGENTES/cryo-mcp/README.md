# Cryo MCP 🧊

Um servidor Model Completion Protocol (MCP) para a ferramenta de extração de dados blockchain [Cryo](https://github.com/paradigmxyz/cryo).

O Cryo MCP permite acessar os poderosos recursos de extração de dados blockchain do Cryo via um servidor API que implementa o protocolo MCP, facilitando a consulta de dados blockchain a partir de qualquer cliente compatível com MCP.

## Funcionalidades

- **Acesso Completo ao Dataset Cryo**: Consulte qualquer conjunto de dados do Cryo via API
- **Integração MCP**: Funciona perfeitamente com clientes MCP
- **Opções de Consulta Flexíveis**: Suporte para todos os principais filtros e opções do Cryo
- **Consulta por Intervalo de Blocos**: Consulte blocos específicos, o bloco mais recente ou intervalos relativos
- **Filtro por Contrato**: Filtre dados por endereço de contrato
- **Acesso ao Bloco Mais Recente**: Acesse facilmente o último bloco da Ethereum
- **Múltiplos Formatos de Saída**: Suporte para JSON e CSV
- **Informação de Esquema**: Obtenha detalhes dos esquemas dos datasets e dados de exemplo

## Instalação (Opcional)

Não é necessário se você pretende rodar a ferramenta diretamente com `uvx`.

```bash
# instalar com UV (recomendado)
uv tool install cryo-mcp
```

## Requisitos

- Python 3.8 ou superior
- uv
- Uma instalação funcional do [Cryo](https://github.com/paradigmxyz/cryo)
- Acesso a um endpoint Ethereum RPC

## Guia Rápido

### Uso com Claude Code

1. Execute `claude mcp add` para um prompt interativo.
2. Insira `uvx` como o comando a ser executado.
3. Insira `cryo-mcp -r <ETH_RPC_URL>` como os argumentos.
4. Alternativamente, forneça `ETH_RPC_URL` como uma variável de ambiente.

Novas instâncias do `claude` terão acesso ao Cryo configurado para seu endpoint RPC.

## Ferramentas Disponíveis

O Cryo MCP expõe as seguintes ferramentas MCP:

### `list_datasets()`

Retorna uma lista de todos os datasets disponíveis no Cryo.

Exemplo:
```python
client.list_datasets()
```

### `query_dataset()`

Consulta um dataset do Cryo com diversas opções de filtro.

Parâmetros:
- `dataset` (str): Nome do dataset (ex: 'blocks', 'transactions', 'logs')
- `blocks` (str, opcional): Especificação do intervalo de blocos (ex: '1000:1010')
- `start_block` (int, opcional): Bloco inicial (alternativa a `blocks`)
- `end_block` (int, opcional): Bloco final (alternativa a `blocks`)
- `use_latest` (bool, opcional): Se verdadeiro, consulta o bloco mais recente
- `blocks_from_latest` (int, opcional): Número de blocos a partir do mais recente
- `contract` (str, opcional): Endereço do contrato para filtrar
- `output_format` (str, opcional): Formato da saída ('json', 'csv')
- `include_columns` (list, opcional): Colunas adicionais a incluir
- `exclude_columns` (list, opcional): Colunas a excluir

Exemplo:
```python
# Transações dos blocos 15M a 15.01M
client.query_dataset('transactions', blocks='15M:15.01M')

# Logs de um contrato específico nos últimos 100 blocos
client.query_dataset('logs', blocks_from_latest=100, contract='0x1234...')

# Apenas o bloco mais recente
client.query_dataset('blocks', use_latest=True)
```

### `lookup_dataset()`

Obtém informações detalhadas sobre um dataset, incluindo esquema e dados de exemplo.

Parâmetros:
- `name` (str): Nome do dataset
- `sample_start_block` (int, opcional): Bloco inicial para amostra
- `sample_end_block` (int, opcional): Bloco final para amostra
- `use_latest_sample` (bool, opcional): Usar o bloco mais recente como amostra
- `sample_blocks_from_latest` (int, opcional): Número de blocos a partir do mais recente para amostra

Exemplo:
```python
client.lookup_dataset('logs')
```

### `get_latest_ethereum_block()`

Retorna informações sobre o bloco mais recente da Ethereum.

Exemplo:
```python
client.get_latest_ethereum_block()
```

## Opções de Configuração

Ao iniciar o servidor Cryo MCP, você pode usar as seguintes opções na linha de comando:

- `--rpc-url URL`: URL do endpoint Ethereum RPC (sobrescreve a variável de ambiente ETH_RPC_URL)

## Variáveis de Ambiente

- `ETH_RPC_URL`: URL padrão do endpoint Ethereum RPC, usada se não for especificada na linha de comando

## Uso Avançado

### Consultas com Intervalos de Blocos

O Cryo MCP suporta toda a sintaxe de especificação de blocos do Cryo:

```python
# Usando números de bloco
client.query_dataset('transactions', blocks='15000000:15001000')

# Usando notação K/M
client.query_dataset('logs', blocks='15M:15.01M')

# Usando deslocamento a partir do mais recente
client.query_dataset('blocks', blocks_from_latest=100)
```

### Filtro por Contrato

Filtre logs e outros dados por endereço de contrato:

```python
# Todos os logs do contrato USDC
client.query_dataset('logs',
                     blocks='16M:16.1M',
                     contract='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
```

### Seleção de Colunas

Inclua apenas as colunas necessárias:

```python
# Apenas número do bloco e timestamp
client.query_dataset('blocks',
                     blocks='16M:16.1M',
                     include_columns=['number', 'timestamp'])
```

## Desenvolvimento

### Estrutura do Projeto

```
cryo-mcp/
├── cryo_mcp/           # Diretório principal do pacote
│   ├── __init__.py     # Inicialização do pacote
│   ├── server.py       # Implementação principal do servidor MCP
├── tests/              # Testes
│   ├── test_*.py       # Arquivos de teste
├── pyproject.toml      # Configuração do projeto
├── README.md           # Documentação
```

### Rodar Testes

```bash
uv run pytest
```

## Licença

MIT

## Créditos

- Baseado na incrível ferramenta [Cryo](https://github.com/paradigmxyz/cryo) da Paradigm
- Utiliza o [protocolo MCP](https://github.com/mcp-team/mcp) para comunicação via API
