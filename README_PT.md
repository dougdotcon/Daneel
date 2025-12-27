# Plataforma Daneel

<div align="center">

<img src="logo.png" alt="Logo Daneel" width="160" height="160" style="border-radius: 24px; margin: 30px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.3);" />

**Plataforma Completa de IA Multimodal e Agentes Inteligentes**

[![Status](https://img.shields.io/badge/Status-Sistema_Funcional-green?style=for-the-badge&logo=checkmarx&logoColor=white)](https://github.com/emcie-co/Daneel)
[![Versão Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Licença](https://img.shields.io/badge/license-Apache%202.0-667eea.svg?style=for-the-badge&logo=apache&logoColor=white&labelColor=1a202c)](https://opensource.org/licenses/Apache-2.0)
[![DeepSeek](https://img.shields.io/badge/DeepSeek_R1-Local-orange?style=for-the-badge&logo=ai&logoColor=white)](https://deepseek.com)
[![Ollama](https://img.shields.io/badge/Ollama-Suportado-purple?style=for-the-badge&logo=llama&logoColor=white)](https://ollama.ai)

<div style="margin: 25px 0;">

[![Interface Web](https://img.shields.io/badge/🌐_Interface_Web-667eea?style=for-the-badge&logoColor=white)](#-interface-web)
[![RAG Agnético](https://img.shields.io/badge/🔍_RAG_Agnético-764ba2?style=for-the-badge&logoColor=white)](#-sistema-rag-agnético)
[![Multimodal](https://img.shields.io/badge/🎨_Multimodal-f093fb?style=for-the-badge&logoColor=white)](#-funcionalidades-multimodais)
[![Voicebot](https://img.shields.io/badge/🎤_Voicebot-5865f2?style=for-the-badge&logoColor=white)](#-voicebot-tempo-real)

</div>

<div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); padding: 25px; border-radius: 12px; border: 1px solid rgba(102, 126, 234, 0.2); max-width: 85%; margin: 30px auto;">
  <p style="font-size: 1.2em; color: #4a5568; margin: 0;">
    <strong style="color: #667eea;">Daneel</strong> é uma plataforma completa de IA que combina agentes inteligentes, processamento multimodal, RAG agnético e modelos locais em uma interface web moderna e intuitiva. Suporte completo para DeepSeek R1, Llama 3.2, OCR, voz e muito mais.
  </p>
</div>

</div>

## 📋 Navegação Rápida

| [🚀 Funcionalidades](#-funcionalidades-principais) | [📦 Instalação](#-instalação-e-execução) | [🤖 Agentes e RAG](#-agentes-e-rag) | [🗣️ Voz e Multimodal](#-voz-e-multimodal) |
| :--- | :--- | :--- | :--- |

---

## 🚀 Funcionalidades Principais

O **Daneel** é construído em torno do conceito de **Modelagem de Conversas (MC)**, uma abordagem poderosa para controlar como seus agentes de IA interagem com os usuários.

*   **🤖 Agentes Inteligentes**: Crie e gerencie agentes autônomos com comportamentos e ferramentas específicos.
*   **🔍 Sistema RAG Agnético**: Integre perfeitamente geração aumentada por recuperação com suporte a vários formatos de documento.
*   **🎨 Capacidades Multimodais**: Processe imagens, texto e dados estruturados. Inclui funcionalidade de OCR.
*   **🎤 Voicebot em Tempo Real**: Interação de voz full-duplex para conversas naturais.
*   **💻 Interface Web Moderna**: Uma interface elegante e responsiva construída para produtividade.
*   **🔒 Local First**: Otimizado para execução de modelos locais (DeepSeek R1, Ollama) garantindo privacidade e velocidade.

---

## 📦 Instalação e Execução

### Pré-requisitos

*   Python 3.8+
*   (Opcional) Ollama instalado localmente para modelos locais.
*   (Opcional) Suporte a GPU para inferência acelerada.

### 1. Clone o Repositório

bash
git clone https://github.com/emcie-co/Daneel.git
cd Daneel


### 2. Configure o Ambiente

É recomendável usar um ambiente virtual:

bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate


### 3. Instale as Dependências

bash
pip install -r requirements.txt


### 4. Configuração

Copie o arquivo de ambiente exemplo e configure suas preferências (API keys, caminhos de modelos):

bash
cp .env.example .env
# Edite .env com suas chaves e preferências


### 5. Execute a Aplicação

Inicie o servidor backend:

bash
python main.py


Acesse a Interface Web em: `http://localhost:8000` (ou a porta especificada nos logs).

---

## 🤖 Agentes e RAG

### Modelagem de Conversas

O Daneel utiliza a **Modelagem de Conversas (MC)** para definir a lógica dos agentes. Isso permite controle determinístico sobre os fluxos mantendo a flexibilidade dos LLMs.

### Configurando o RAG

1.  Coloque seus documentos (PDF, TXT, MD) no diretório `/data/knowledge_base`.
2.  Execute o script de ingestão:
    bash
    python scripts/ingest.py
    
3.  Os agentes consultarão automaticamente o vetor de busca quando informações relevantes forem necessárias.

---

## 🗣️ Voz e Multimodal

### Voicebot

O módulo de voz utiliza um pipeline de STT -> LLM -> TTS para interação em tempo real.

*   **Entrada**: Fluxo de microfone.
*   **Processamento**: LLM local ou na nuvem.
*   **Saída**: Geração de fluxo de áudio.

### Multimodal / OCR

Faça upload de imagens via interface web para extrair texto (OCR) ou analisar o conteúdo da imagem usando modelos com visão.

---

## 🏗️ Arquitetura

*   **Frontend**: React / TypeScript
*   **Backend**: Python (FastAPI / asyncio)
*   **Motor de IA**: Integração com Ollama, DeepSeek e wrappers customizados.
*   **Armazenamento**: SQLite (Metadados), ChromaDB (Vetores).

---

## 📜 Licença

Este projeto está licenciado sob a Licença Apache 2.0 - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor, leia nosso [Guia de Contribuição](CONTRIBUTING.md) para começar.