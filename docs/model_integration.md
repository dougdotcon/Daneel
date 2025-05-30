# Integração de Modelos

Este documento descreve a integração de modelos locais e em nuvem no framework Parlant.

## Visão Geral

O Parlant agora suporta uma variedade de modelos de linguagem, tanto locais quanto baseados em nuvem, através de uma interface unificada. A integração de modelos inclui:

1. Suporte para modelos locais como Llama e DeepSeek
2. Capacidades de alternância de modelos para selecionar dinamicamente o melhor modelo para uma tarefa
3. Mecanismos de fallback de modelos para confiabilidade
4. Monitoramento de desempenho para uso de modelos

## Componentes

### LocalModelManager

A classe `LocalModelManager` lida com o download, listagem e gerenciamento de modelos locais. Ela suporta:

- Modelos do Hugging Face
- Modelos no formato GGUF
- Modelos Ollama
- Modelos personalizados

Exemplo de uso:

```python
from parlant.adapters.nlp.local.model_manager import LocalModelManager, ModelType
from parlant.core.loggers import ConsoleLogger

# Create a model manager
manager = LocalModelManager(logger=ConsoleLogger())

# Initialize the manager
await manager.initialize()

# List available models
llama_models = manager.list_models(ModelType.LLAMA)
deepseek_models = manager.list_models(ModelType.DEEPSEEK)

# Download a model
model = await manager.download_model(
    model_name="llama-7b",
    model_type=ModelType.LLAMA,
    source="ollama"
)

# Get a model by ID
model = manager.get_model("local/llama/llama-7b")
```

### LlamaService

A classe `LlamaService` fornece capacidades de NLP usando modelos Llama. Ela suporta:

- Geração de texto
- Embeddings
- Moderação

Exemplo de uso:

```python
from parlant.adapters.nlp.local.llama import LlamaService
from parlant.adapters.nlp.local.model_manager import LocalModelManager
from parlant.core.loggers import ConsoleLogger

# Create a model manager
manager = LocalModelManager(logger=ConsoleLogger())
await manager.initialize()

# Create a Llama service
service = LlamaService(
    model_manager=manager,
    model_id="local/llama/llama-7b",
    logger=ConsoleLogger()
)

# Generate text
generator = await service.get_schematic_generator(Dict)
result = await generator.generate("What is the capital of France?")

# Generate embeddings
embedder = await service.get_embedder()
embeddings = await embedder.embed(["What is the capital of France?"])
```

### DeepSeekService

A classe `DeepSeekService` fornece capacidades de NLP usando modelos DeepSeek. Ela tem a mesma interface que a `LlamaService`.

### ModelSwitcher

A classe `ModelSwitcher` permite alternar entre diferentes modelos com base em requisitos. Ela pode:

- Usar modelos locais quando possível
- Recorrer a modelos em nuvem quando necessário
- Selecionar modelos com base em capacidades
- Monitorar o desempenho do modelo

Exemplo de uso:

```python
from parlant.adapters.nlp.model_switcher import ModelSwitcher
from parlant.adapters.nlp.local.model_manager import LocalModelManager
from parlant.core.loggers import ConsoleLogger

# Create a model manager
manager = LocalModelManager(logger=ConsoleLogger())
await manager.initialize()

# Create a model switcher
switcher = ModelSwitcher(
    logger=ConsoleLogger(),
    model_manager=manager,
    default_model_id="local/llama/llama-7b",
    fallback_model_id="openai/gpt-4o"
)

# Initialize the switcher
await switcher.initialize()

# Switch to a different model
switcher.set_model("local/deepseek/deepseek-coder-7b")

# List available models
models = switcher.list_available_models()

# Use the current model
generator = await switcher.get_schematic_generator(Dict)
result = await generator.generate("What is the capital of France?")
```

### NLPServiceFactory

A classe `NLPServiceFactory` fornece uma fábrica para criar serviços NLP. Ela pode:

- Criar serviços para diferentes tipos de modelo
- Criar um serviço padrão baseado nos modelos disponíveis
- Inicializar serviços com configuração apropriada

Exemplo de uso:

```python
from parlant.adapters.nlp.factory import NLPServiceFactory
from parlant.core.loggers import ConsoleLogger

# Create a factory
factory = NLPServiceFactory(logger=ConsoleLogger())

# Initialize the factory
await factory.initialize()

# Create a specific service
llama_service = await factory.create_service("llama")
deepseek_service = await factory.create_service("deepseek")
switcher = await factory.create_service("model_switcher")

# Create a default service
service = await factory.create_default_service()
```

## Integração com Parlant

A integração de modelos foi projetada para funcionar perfeitamente com a arquitetura existente do Parlant:

1. **Camada de Adaptadores**: As implementações dos modelos residem na camada de adaptadores, permitindo que sejam usadas pelos componentes principais.
2. **Serviços NLP**: Os modelos implementam a interface de serviço NLP, tornando-os compatíveis com o código existente.
3. **Configuração**: Os modelos podem ser configurados através do sistema de configuração do Parlant.
4. **Registro**: O uso do modelo é registrado através do sistema de registro do Parlant.

## Melhorias Futuras

Melhorias futuras para a integração de modelos podem incluir:

1. **Fine-tuning de Modelos**: Suporte para ajuste fino de modelos para tarefas específicas.
2. **Quantização de Modelos**: Suporte para quantização de modelos para reduzir o uso de memória.
3. **Cache de Modelos**: Cache de saídas do modelo para melhor desempenho.
4. **Métricas de Modelos**: Coleta de métricas sobre desempenho e uso do modelo.
5. **Modelos Multimodais**: Suporte para modelos que podem lidar com múltiplas modalidades (texto, imagens, áudio, etc.).

## Referências

- [Llama](https://github.com/facebookresearch/llama)
- [DeepSeek](https://github.com/deepseek-ai/DeepSeek-Coder)
- [Ollama](https://github.com/ollama/ollama)
- [GGUF Format](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
