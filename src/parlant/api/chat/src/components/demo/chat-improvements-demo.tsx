import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import AdvancedChatInput from '../chat-input/advanced-chat-input';
import EnhancedMessage from '../message/enhanced-message';
import EnhancedSessionList from '../session-list/enhanced-session-list';
import { MessageStatus, TypingIndicator, ConnectionStatus } from '../status/message-status';
import EnhancedChatInterface from '../enhanced-chat/enhanced-chat-interface';

export default function ChatImprovementsDemo() {
  const [inputValue, setInputValue] = useState('');
  const [showEnhancedInterface, setShowEnhancedInterface] = useState(false);

  // Mock data for demonstrations
  const mockMessages = [
    {
      id: '1',
      content: 'Hello! Can you help me understand how to implement a REST API?',
      role: 'user' as const,
      timestamp: new Date(Date.now() - 1000 * 60 * 5)
    },
    {
      id: '2',
      content: `I'd be happy to help you implement a REST API! Here's a comprehensive guide:

## REST API Basics

REST (Representational State Transfer) is an architectural style for designing networked applications. Here are the key principles:

### HTTP Methods
- **GET**: Retrieve data
- **POST**: Create new resources
- **PUT**: Update existing resources
- **DELETE**: Remove resources

### Example Implementation

\`\`\`javascript
// Express.js example
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {
  res.json({ users: [] });
});

app.post('/api/users', (req, res) => {
  // Create user logic
  res.status(201).json({ message: 'User created' });
});
\`\`\`

Would you like me to explain any specific part in more detail?`,
      role: 'assistant' as const,
      timestamp: new Date(Date.now() - 1000 * 60 * 4)
    }
  ];

  const mockSessions = [
    {
      id: '1',
      title: 'REST API Implementation',
      lastMessage: 'Would you like me to explain any specific part in more detail?',
      timestamp: new Date(Date.now() - 1000 * 60 * 4),
      messageCount: 8,
      agentName: 'Daneel',
      isPinned: true,
      status: 'active' as const
    },
    {
      id: '2',
      title: 'Database Design Discussion',
      lastMessage: 'Let me show you how to normalize your database schema...',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
      messageCount: 15,
      agentName: 'Daneel',
      isFavorite: true,
      status: 'idle' as const
    },
    {
      id: '3',
      title: 'React Component Optimization',
      lastMessage: 'Here are some performance optimization techniques...',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
      messageCount: 23,
      agentName: 'Daneel',
      status: 'active' as const
    }
  ];

  const handleSendMessage = (message: string, attachments?: File[]) => {
    console.log('Sending message:', message, attachments);
    setInputValue('');
  };

  if (showEnhancedInterface) {
    return (
      <div className="h-screen">
        <EnhancedChatInterface
          sessionId="demo"
          agentName="Daneel"
          onNavigateToAdmin={() => setShowEnhancedInterface(false)}
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🚀 Enhanced Chat UI Components
        </h1>
        <p className="text-gray-600 mb-4">
          Demonstração das melhorias implementadas na interface do chat
        </p>
        <Button 
          onClick={() => setShowEnhancedInterface(true)}
          className="mb-6"
        >
          Ver Interface Completa
        </Button>
      </div>

      <Tabs defaultValue="input" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="input">Input Avançado</TabsTrigger>
          <TabsTrigger value="messages">Mensagens</TabsTrigger>
          <TabsTrigger value="sessions">Lista de Sessões</TabsTrigger>
          <TabsTrigger value="status">Indicadores</TabsTrigger>
          <TabsTrigger value="features">Recursos</TabsTrigger>
        </TabsList>

        <TabsContent value="input" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Input Avançado com Funcionalidades</CardTitle>
              <CardDescription>
                Novo componente de input com suporte a anexos, comandos slash, histórico e atalhos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <AdvancedChatInput
                  value={inputValue}
                  onChange={setInputValue}
                  onSend={handleSendMessage}
                  placeholder="Digite sua mensagem... (tente /help)"
                  agentName="Daneel"
                  showTyping={false}
                />
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-semibold mb-2">Funcionalidades:</h4>
                    <ul className="space-y-1 text-gray-600">
                      <li>• Redimensionamento automático</li>
                      <li>• Suporte a anexos (drag & drop)</li>
                      <li>• Comandos slash (/help, /clear, etc.)</li>
                      <li>• Histórico de mensagens (↑/↓)</li>
                      <li>• Contador de caracteres</li>
                      <li>• Gravação de voz</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Atalhos:</h4>
                    <ul className="space-y-1 text-gray-600">
                      <li>• <Badge variant="outline">Enter</Badge> Enviar</li>
                      <li>• <Badge variant="outline">Shift+Enter</Badge> Nova linha</li>
                      <li>• <Badge variant="outline">Ctrl+Enter</Badge> Enviar forçado</li>
                      <li>• <Badge variant="outline">↑/↓</Badge> Histórico</li>
                      <li>• <Badge variant="outline">Esc</Badge> Fechar comandos</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="messages" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Mensagens Melhoradas</CardTitle>
              <CardDescription>
                Componentes de mensagem com ações rápidas, edição e feedback
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {mockMessages.map((message) => (
                  <EnhancedMessage
                    key={message.id}
                    id={message.id}
                    content={message.content}
                    role={message.role}
                    timestamp={message.timestamp}
                    onEdit={(id, content) => console.log('Edit:', id, content)}
                    onRegenerate={message.role === 'assistant' ? (id) => console.log('Regenerate:', id) : undefined}
                    onCopy={(content) => console.log('Copy:', content)}
                    onShare={(id) => console.log('Share:', id)}
                    onFeedback={(id, type) => console.log('Feedback:', id, type)}
                  />
                ))}
              </div>
              
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">Ações Disponíveis:</h4>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                  <div>• Copiar mensagem</div>
                  <div>• Editar (usuário)</div>
                  <div>• Regenerar (assistente)</div>
                  <div>• Feedback positivo/negativo</div>
                  <div>• Compartilhar</div>
                  <div>• Menu de ações</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sessions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Lista de Sessões Avançada</CardTitle>
              <CardDescription>
                Lista com busca, filtros, prévia e organização
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-96 border rounded-lg overflow-hidden">
                <EnhancedSessionList
                  sessions={mockSessions}
                  selectedSessionId="1"
                  onSessionSelect={(id) => console.log('Select session:', id)}
                  onSessionDelete={(id) => console.log('Delete session:', id)}
                  onSessionEdit={(id, title) => console.log('Edit session:', id, title)}
                  onSessionPin={(id, pinned) => console.log('Pin session:', id, pinned)}
                  onSessionArchive={(id, archived) => console.log('Archive session:', id, archived)}
                  onSessionFavorite={(id, favorite) => console.log('Favorite session:', id, favorite)}
                />
              </div>
              
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">Funcionalidades:</h4>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                  <div>• Busca em tempo real</div>
                  <div>• Filtros por categoria</div>
                  <div>• Ordenação múltipla</div>
                  <div>• Prévia da última mensagem</div>
                  <div>• Fixar/favoritar sessões</div>
                  <div>• Arquivar conversas</div>
                  <div>• Edição inline de títulos</div>
                  <div>• Indicadores de status</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="status" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Indicadores de Status</CardTitle>
              <CardDescription>
                Componentes para mostrar status de mensagens e conexão
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-semibold mb-3">Status de Mensagens:</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <MessageStatus status="sending" showText />
                    <MessageStatus status="sent" showText />
                    <MessageStatus status="delivered" showText />
                    <MessageStatus status="read" showText />
                  </div>
                  <div className="space-y-2">
                    <MessageStatus status="error" showText error="Falha na conexão" />
                    <MessageStatus status="processing" showText />
                    <MessageStatus status="typing" showText />
                    <MessageStatus status="thinking" showText />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-3">Indicadores Especiais:</h4>
                <div className="space-y-3">
                  <TypingIndicator agentName="Daneel" />
                  <div className="flex gap-4">
                    <ConnectionStatus isConnected={true} />
                    <ConnectionStatus isConnected={false} />
                    <ConnectionStatus isConnected={false} isReconnecting={true} />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="features" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recursos Implementados</CardTitle>
              <CardDescription>
                Resumo completo das melhorias na UI do chat
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3 text-green-600">✅ Implementado</h4>
                  <ul className="space-y-2 text-sm">
                    <li>• Input avançado com anexos</li>
                    <li>• Comandos slash (/help, /clear, etc.)</li>
                    <li>• Histórico de mensagens</li>
                    <li>• Ações rápidas nas mensagens</li>
                    <li>• Lista de sessões melhorada</li>
                    <li>• Busca e filtros avançados</li>
                    <li>• Indicadores de status</li>
                    <li>• Modo escuro/claro</li>
                    <li>• Atalhos de teclado</li>
                    <li>• Exportar conversas</li>
                    <li>• Notificações sonoras</li>
                    <li>• Interface responsiva</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-3 text-blue-600">🔄 Próximos Passos</h4>
                  <ul className="space-y-2 text-sm">
                    <li>• Integração com API real</li>
                    <li>• Gravação de voz funcional</li>
                    <li>• Compartilhamento de conversas</li>
                    <li>• Busca global nas mensagens</li>
                    <li>• Templates de mensagens</li>
                    <li>• Colaboração em tempo real</li>
                    <li>• Plugins e extensões</li>
                    <li>• Analytics de uso</li>
                    <li>• Backup automático</li>
                    <li>• Sincronização cloud</li>
                    <li>• Acessibilidade completa</li>
                    <li>• Testes automatizados</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
