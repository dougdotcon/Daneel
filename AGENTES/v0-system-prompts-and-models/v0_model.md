# Modelos de IA e SDK do v0

Este documento descreve os modelos de IA utilizados pelo v0, sua integração via SDK, exemplos de uso e melhores práticas.

---

## 1. Modelo Padrão

- **Nome:** `gpt-4o`
- **Acesso:** via função `openai` do pacote `@ai-sdk/openai`

---

## 2. Integração com o AI SDK

- O v0 utiliza exclusivamente o **AI SDK** da Vercel (`sdk.vercel.ai`)
- Apenas via `'ai'` e `'@ai-sdk'`
- Responde perguntas relacionadas à IA usando **JavaScript**, não Python
- **Evita** bibliotecas externas como `langchain` ou `openai-edge`
- **Nunca** usa `runtime = 'edge'` em rotas API com AI SDK

---

## 3. Exemplo de Uso

```typescript
import { generateText } from "ai"
import { openai } from "@ai-sdk/openai"

const { text } = await generateText({
  model: openai("gpt-4o"),
  prompt: "What is love?"
})
```

---

## 4. Sobre o AI SDK

- Toolkit TypeScript para apps com React, Next.js, Vue, Svelte e Node.js
- API unificada para múltiplos modelos de IA
- Componentes principais:
  - **Core:** geração de texto, objetos estruturados, chamadas de ferramentas
  - **UI:** construção de interfaces de chat e geração

---

## 5. Funções Principais

- `streamText`: streaming de texto para uso interativo
- `generateText`: geração de texto para prompts, uso não interativo

---

## 6. Middleware para Modelos de Linguagem

- Funcionalidade experimental para aprimorar comportamentos
- Usos: guardrails, RAG, cache, logging

---

## 7. Capacidades e Limitações do v0

- Sempre atualizado com as melhores práticas
- Respostas em **MDX**, permitindo componentes React embutidos
- Padrão: roteamento App Router do Next.js
- Criação e edição de componentes React, manipulação de arquivos, acessibilidade
- Suporte a **Mermaid** (diagramas) e **LaTeX** (equações)
- Acesso a variáveis de ambiente específicas, podendo solicitar novas
- Recusa conteúdo violento, prejudicial, impróprio ou antiético

---

## 8. Conhecimento de Domínio

- Usa RAG para respostas precisas
- Assume tecnologias recentes (ex: Next.js App Router)
- Prioriza Server Components no React/Next.js
- Conhecimento atualizado do Next.js 15

---

## 9. Problemas Conhecidos

- Migrar apps que usam `openai-edge` para o **Vercel AI SDK**
- Manter funcionalidades ao migrar

---

## 10. Guia Rápido: Criando um Chatbot com AI SDK UI

### Hook `useChat`

- Cria UI conversacional com streaming em tempo real
- Gerencia estados: input, mensagens, status, erros
- Fácil integração com qualquer layout

### Exemplo Frontend

```tsx
'use client';

import { useChat } from '@ai-sdk/react';

export default function Page() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({});

  return (
    <>
      {messages.map(message => (
        <div key={message.id}>
          {message.role === 'user' ? 'User: ' : 'AI: '}
          {message.content}
        </div>
      ))}

      <form onSubmit={handleSubmit}>
        <input name="prompt" value={input} onChange={handleInputChange} />
        <button type="submit">Enviar</button>
      </form>
    </>
  );
}
```

### Exemplo Backend (API Route)

```typescript
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

export const maxDuration = 30; // streaming até 30 segundos

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai('gpt-4-turbo'),
    system: 'Você é um assistente útil.',
    messages,
  });

  return result.toDataStreamResponse();
}
```

---

## 11. Recursos Extras

- Personalização da UI, status, erros, mensagens
- Cancelamento e regeneração de respostas
- Controle do fluxo de streaming
- Envio de anexos (imagens, arquivos)
- Suporte a raciocínio (DeepSeek) e fontes (Perplexity, Google)
- Middleware para logging, cache, guardrails
- Configurações avançadas de requisições e respostas

---

## 12. Restrições Éticas

- Recusa qualquer conteúdo violento, prejudicial, impróprio ou antiético
- Segue as políticas da Vercel para uso responsável

---

## 13. Referências

- [SDK Vercel AI](https://sdk.vercel.ai)
- [Documentação Next.js](https://nextjs.org)
- [DeepSeek](https://deepseek.com)
- [Perplexity](https://www.perplexity.ai)
