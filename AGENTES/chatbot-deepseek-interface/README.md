<div align="center">
  <img src="assets/img/LOGOSPNG/logo.png" alt="Nexlify" width="220"/>
# R1 Deepseek - Interface Web

Este projeto consiste em uma interface web para o modelo R1 Deepseek, oferecendo duas interfaces diferentes para interação com o modelo.

## Pré-requisitos

### Python
1. Python 3.8 ou superior
2. Pip (gerenciador de pacotes do Python)

### Node.js
1. Node.js 16.x ou superior
2. PNPM (você pode instalar com `npm install -g pnpm`)

## Instalação

### 1. Instalando Dependências Python

Abra o terminal e execute:

```bash
# Instalar PyTorch (versão CPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar outras dependências
pip install transformers python-bridge
```

### 2. Instalando Dependências Node.js

Na pasta do projeto, execute:

```bash
cd interface1
pnpm install
```

### 3. Construindo o Pacote do Modelo

```bash
cd interface1/packages/r1-model
pnpm build
```

## Executando o Projeto

1. Navegue até a pasta da aplicação web:
```bash
cd interface1/apps/web
```

2. Inicie o servidor de desenvolvimento:
```bash
pnpm dev
```

3. Acesse a aplicação em seu navegador:
```
http://localhost:3000
```

## Estrutura do Projeto

- `modeloR1/` - Contém o modelo R1 Deepseek
- `interface1/` - Projeto principal com as interfaces
  - `apps/web/` - Aplicação web principal
  - `packages/r1-model/` - Pacote que integra com o modelo Python

## Interfaces Disponíveis

### Interface 1
- Interface principal com design minimalista
- Foco em interações simples e diretas
- Acesse em: `http://localhost:3000/interface1`

### Interface 2
- Interface alternativa com histórico de conversas
- Layout em duas colunas
- Acesse em: `http://localhost:3000/interface2`

## Observações Importantes

1. O modelo é executado em CPU, então as respostas podem levar alguns segundos
2. A primeira requisição pode ser mais lenta devido ao carregamento inicial do modelo
3. Recomenda-se ter pelo menos 8GB de RAM disponível para melhor performance
4. O modelo é carregado e descarregado a cada requisição para economizar memória

## Solução de Problemas

### Erro de Memória
Se encontrar erros de memória, você pode:
1. Reduzir o número de tokens máximos nas configurações
2. Fechar outros programas que consumam muita memória
3. Reiniciar o servidor se necessário

### Erro de Python
Se encontrar erros relacionados ao Python:
1. Verifique se o Python está instalado e no PATH do sistema
2. Confirme se todas as dependências Python foram instaladas corretamente
3. Verifique se o caminho para o modelo está correto

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 