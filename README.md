# Daneel Platform

<div align="center">

<img src="logo.png" alt="Daneel Logo" width="160" height="160" style="border-radius: 24px; margin: 30px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.3);" />

**Complete Multimodal AI & Intelligent Agents Platform**

[![Status](https://img.shields.io/badge/Status-System_Operational-green?style=for-the-badge&logo=checkmarx&logoColor=white)](https://github.com/emcie-co/Daneel)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-667eea.svg?style=for-the-badge&logo=apache&logoColor=white&labelColor=1a202c)](https://opensource.org/licenses/Apache-2.0)
[![DeepSeek](https://img.shields.io/badge/DeepSeek_R1-Local-orange?style=for-the-badge&logo=ai&logoColor=white)](https://deepseek.com)
[![Ollama](https://img.shields.io/badge/Ollama-Supported-purple?style=for-the-badge&logo=llama&logoColor=white)](https://ollama.ai)

<div style="margin: 25px 0;">

[![Web Interface](https://img.shields.io/badge/🌐_Web_Interface-667eea?style=for-the-badge&logoColor=white)](#-web-interface)
[![Agnostic RAG](https://img.shields.io/badge/🔍_Agnostic_RAG-764ba2?style=for-the-badge&logoColor=white)](#-agnostic-rag-system)
[![Multimodal](https://img.shields.io/badge/🎨_Multimodal-f093fb?style=for-the-badge&logoColor=white)](#-multimodal-features)
[![Voicebot](https://img.shields.io/badge/🎤_Voicebot-5865f2?style=for-the-badge&logoColor=white)](#-real-time-voicebot)

</div>

<div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); padding: 25px; border-radius: 12px; border: 1px solid rgba(102, 126, 234, 0.2); max-width: 85%; margin: 30px auto;">
  <p style="font-size: 1.2em; color: #4a5568; margin: 0;">
    <strong style="color: #667eea;">Daneel</strong> is a comprehensive AI platform that combines intelligent agents, multimodal processing, Agnostic RAG, and local models within a modern, intuitive web interface. Full support for DeepSeek R1, Llama 3.2, OCR, voice, and more.
  </p>
</div>

</div>

## 📋 Quick Navigation

| [🚀 Features](#-key-features) | [📦 Installation](#-installation-and-execution) | [🤖 Agents & RAG](#-agents-and-rag) | [🗣️ Voice & Multimodal](#-voice-and-multimodal) |
| :--- | :--- | :--- | :--- |

---

## 🚀 Key Features

**Daneel** is built around the concept of **Conversational Modeling (MC)**, a powerful approach to controlling how AI agents interact with users.

*   **🤖 Intelligent Agents**: Create and manage autonomous agents with specific behaviors and tools.
*   **🔍 Agnostic RAG System**: Seamlessly integrate retrieval-augmented generation with support for various document formats.
*   **🎨 Multimodal Capabilities**: Process images, text, and structured data. Includes OCR functionality.
*   **🎤 Real-Time Voicebot**: Full duplex voice interaction for natural conversations.
*   **💻 Modern Web UI**: A sleek, responsive interface built for productivity.
*   **🔒 Local First**: Optimized for local model execution (DeepSeek R1, Ollama) ensuring privacy and speed.

---

## 📦 Installation and Execution

### Prerequisites

*   Python 3.8+
*   (Optional) Ollama installed locally for local models.
*   (Optional) GPU support for accelerated inference.

### 1. Clone the Repository

bash
git clone https://github.com/emcie-co/Daneel.git
cd Daneel


### 2. Set up the Environment

It is recommended to use a virtual environment:

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


### 3. Install Dependencies

bash
pip install -r requirements.txt


### 4. Configuration

Copy the example environment file and configure your settings (API keys, model paths):

bash
cp .env.example .env
# Edit .env with your keys and preferences


### 5. Run the Application

Start the backend server:

bash
python main.py


Access the Web Interface at: `http://localhost:8000` (or the port specified in your logs).

---

## 🤖 Agents and RAG

### Conversational Modeling

Daneel utilizes **Conversational Modeling (MC)** to define agent logic. This allows for deterministic control over flows while maintaining the flexibility of LLMs.

### Setting up RAG

1.  Place your documents (PDF, TXT, MD) in the `/data/knowledge_base` directory.
2.  Run the ingestion script:
    bash
    python scripts/ingest.py
    
3.  Agents will automatically query the vector store when relevant information is needed.

---

## 🗣️ Voice and Multimodal

### Voicebot

The voice module uses a pipeline of STT -> LLM -> TTS for real-time interaction.

*   **Input**: Microphone stream.
*   **Processing**: Local or Cloud LLM.
*   **Output**: Audio stream generation.

### Multimodal / OCR

Upload images via the web interface to extract text (OCR) or analyze image content using vision-capable models.

---

## 🏗️ Architecture

*   **Frontend**: React / TypeScript
*   **Backend**: Python (FastAPI / asyncio)
*   **AI Engine**: Integration with Ollama, DeepSeek, and custom wrappers.
*   **Storage**: SQLite (Metadata), ChromaDB (Vectors).

---

## 📜 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.