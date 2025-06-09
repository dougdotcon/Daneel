# Componentes de UI

Este documento descreve os componentes de UI no framework Daneel.

## Visão Geral

Os componentes de UI fornecem uma maneira de criar interfaces de usuário ricas e interativas para o Daneel. Eles suportam:

1. Realce de código e visualização de diferenças
2. Interfaces de terminal interativas
3. Ferramentas de depuração e inspeção
4. Feedback visual para ações dos agentes

## Componentes

### Componentes de Código

#### CodeBlock

O componente `CodeBlock` fornece realce de sintaxe para trechos de código. Ele suporta:

- Detecção automática de linguagem
- Números de linha
- Funcionalidade de copiar para a área de transferência
- Dobramento de código para blocos grandes
- Realce de linhas específicas
- Múltiplos temas

Exemplo de uso:

```python
from Daneel.ui.components.code import CodeBlock, CodeBlockOptions
from Daneel.core.loggers import ConsoleLogger

# Create a code block
code_block = CodeBlock(ConsoleLogger())

# Configure options
options = CodeBlockOptions(
    language="python",
    show_line_numbers=True,
    show_copy_button=True,
    show_collapse_button=True,
    max_height=500,
    file_name="example.py",
    highlight_lines=[3, 5],
    theme="default",
)

# Render the code block
code = """
def hello():
    print("Hello, world!")
    
if __name__ == "__main__":
    hello()
"""

html = code_block.render_html(code, options)
```

#### DiffViewer

O componente `DiffViewer` visualiza diferenças entre dois trechos de código. Ele suporta:

- Visualização dividida (lado a lado) e unificada
- Realce de sintaxe
- Números de linha
- Codificação por cores para adições, exclusões e modificações
- Múltiplos temas

Exemplo de uso:

```python
from Daneel.ui.components.code import DiffViewer, DiffViewerOptions, DiffMode
from Daneel.core.loggers import ConsoleLogger

# Create a diff viewer
diff_viewer = DiffViewer(ConsoleLogger())

# Configure options
options = DiffViewerOptions(
    language="python",
    show_line_numbers=True,
    show_copy_button=True,
    file_name="example.py",
    diff_mode=DiffMode.SPLIT,
    theme="default",
    context_lines=3,
)

# Render the diff
old_code = """
def hello():
    print("Hello, world!")
"""

new_code = """
def hello():
    print("Hello, universe!")
"""

html = diff_viewer.render_html(old_code, new_code, options)
```

### Componentes de Terminal

#### Terminal

O componente `Terminal` fornece uma interface de terminal interativa. Ele suporta:

- Execução de comandos
- Histórico de comandos
- Realce de sintaxe para saída do terminal
- Funcionalidade de copiar para a área de transferência
- Modo tela cheia
- Manipuladores de comando personalizados
- Múltiplos temas

Exemplo de uso:

```python
from Daneel.ui.components.terminal import Terminal, TerminalOptions, TerminalState
from Daneel.core.loggers import ConsoleLogger

# Create a terminal
terminal = Terminal(ConsoleLogger())

# Register a custom command handler
def handle_hello(command):
    return "Hello, world!"
    
terminal.register_command_handler("hello", handle_hello)

# Configure options
options = TerminalOptions(
    prompt="$ ",
    initial_content="Welcome to the terminal!",
    max_height=300,
    title="Example Terminal",
    read_only=False,
    auto_focus=True,
    theme="dark",
    show_copy_button=True,
    show_clear_button=True,
    show_fullscreen_button=True,
    history_size=100,
    working_directory="/path/to/workspace",
)

# Render the terminal
html = terminal.render_html(options)

# Execute a command
output = await terminal.execute_command("echo Hello, world!")
```

### Componentes de Depuração

#### Inspector

O componente `Inspector` fornece uma maneira de inspecionar variáveis e objetos. Ele suporta:

- Propriedades de objeto expansíveis
- Realce de sintaxe para valores
- Nível de expansão personalizável
- Múltiplos temas
- Filtragem de propriedades privadas e métodos

Exemplo de uso:

```python
from Daneel.ui.components.debug import Inspector, InspectorOptions
from Daneel.core.loggers import ConsoleLogger

# Create an inspector
inspector = Inspector(ConsoleLogger())

# Configure options
options = InspectorOptions(
    expand_level=1,
    max_depth=10,
    max_string_length=100,
    max_array_length=100,
    title="Example Inspector",
    theme="default",
    show_private=False,
    show_methods=False,
    show_dunder=False,
)

# Render the inspector
data = {
    "string": "hello",
    "number": 123,
    "boolean": True,
    "null": None,
    "array": [1, 2, 3],
    "object": {"a": 1, "b": 2},
}

html = inspector.render_html(data, options)
```

#### CallStack

O componente `CallStack` visualiza uma pilha de chamadas para depuração. Ele suporta:

- Visualização de quadros de pilha
- Exibição de código-fonte
- Inspeção de variáveis
- Múltiplos temas
- Filtragem de quadros de biblioteca

Exemplo de uso:

```python
from Daneel.ui.components.debug import CallStack, CallStackOptions, StackFrame
from Daneel.core.loggers import ConsoleLogger

# Create a call stack
call_stack = CallStack(ConsoleLogger())

# Configure options
options = CallStackOptions(
    title="Example Call Stack",
    theme="default",
    max_height=500,
    show_library_frames=False,
    show_variables=True,
    show_source=True,
    context_lines=3,
)

# Create stack frames
frames = [
    StackFrame(
        function_name="main",
        file_name="main.py",
        line_number=10,
        source="result = calculate(x, y)",
    ),
    StackFrame(
        function_name="calculate",
        file_name="math_utils.py",
        line_number=42,
        source="return x + y",
        variables={"x": 1, "y": 2},
    ),
]

# Render the call stack
html = call_stack.render_html(frames, options)
```

## Integração com Daneel

Os componentes de UI estão integrados com o framework Daneel:

1. **Sistema de Agente**: Os agentes podem usar os componentes para fornecer feedback visual
2. **Depuração**: Os componentes de depuração são usados para inspecionar o estado do agente
3. **Terminal**: O componente de terminal é usado para interação com o sistema
4. **Código**: Os componentes de código são usados para visualizar e editar código

## Detalhes de Implementação

### Renderização

Os componentes de UI usam:

- React para renderização do lado do cliente
- Tailwind CSS para estilização
- Monaco Editor para edição de código
- XTerm.js para emulação de terminal

### Temas

O sistema de temas suporta:

- Temas claros e escuros
- Temas personalizados
- Temas específicos de componente
- Transições suaves entre temas

### Acessibilidade

Os componentes seguem as diretrizes de acessibilidade:

- Suporte a leitor de tela
- Navegação por teclado
- Alto contraste
- Tamanhos de fonte ajustáveis

## Melhorias Futuras

Possíveis melhorias futuras para os componentes de UI:

1. **Componentes Responsivos**: Melhorar o suporte para diferentes tamanhos de tela
2. **Personalização Avançada**: Adicionar mais opções de personalização
3. **Integração de Gráficos**: Adicionar componentes para visualização de dados
4. **Suporte a Gestos**: Melhorar o suporte para dispositivos touch
5. **Modo Offline**: Permitir uso offline dos componentes
