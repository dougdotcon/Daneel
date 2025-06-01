import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  status: 'sending' | 'sent' | 'delivered' | 'error';
  attachments?: File[];
  metadata?: Record<string, any>;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  lastActivity: Date;
  agentId: string;
  customerId: string;
}

interface UseEnhancedChatOptions {
  sessionId?: string;
  onMessageSent?: (message: ChatMessage) => void;
  onMessageReceived?: (message: ChatMessage) => void;
  onError?: (error: Error) => void;
  autoSave?: boolean;
  maxRetries?: number;
}

export function useEnhancedChat(options: UseEnhancedChatOptions = {}) {
  const {
    sessionId,
    onMessageSent,
    onMessageReceived,
    onError,
    autoSave = true,
    maxRetries = 3
  } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('connected');
  const [inputValue, setInputValue] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  
  const retryCountRef = useRef<Map<string, number>>(new Map());
  const abortControllerRef = useRef<AbortController | null>(null);

  // Generate unique message ID
  const generateMessageId = useCallback(() => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Send message with retry logic
  const sendMessage = useCallback(async (
    content: string, 
    attachments: File[] = [],
    retryCount = 0
  ): Promise<void> => {
    if (!content.trim() && attachments.length === 0) {
      toast.error('Please enter a message or attach a file');
      return;
    }

    const messageId = generateMessageId();
    const userMessage: ChatMessage = {
      id: messageId,
      content: content.trim(),
      role: 'user',
      timestamp: new Date(),
      status: 'sending',
      attachments: attachments.length > 0 ? attachments : undefined
    };

    // Add user message to chat
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setAttachments([]);
    setIsLoading(true);

    try {
      // Cancel any previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      // Simulate API call - replace with actual API integration
      const formData = new FormData();
      formData.append('message', content);
      formData.append('sessionId', sessionId || 'default');
      
      attachments.forEach((file, index) => {
        formData.append(`attachment_${index}`, file);
      });

      const response = await fetch('/api/chat/send', {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Update message status to sent
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, status: 'sent' as const }
          : msg
      ));

      onMessageSent?.(userMessage);

      // Simulate assistant response
      setIsTyping(true);
      
      const assistantResponse = await response.json();
      
      setTimeout(() => {
        const assistantMessage: ChatMessage = {
          id: generateMessageId(),
          content: assistantResponse.message || 'I received your message!',
          role: 'assistant',
          timestamp: new Date(),
          status: 'delivered'
        };

        setMessages(prev => [...prev, assistantMessage]);
        setIsTyping(false);
        onMessageReceived?.(assistantMessage);
      }, 1000 + Math.random() * 2000); // Simulate typing delay

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return; // Request was cancelled
      }

      console.error('Failed to send message:', error);

      // Update message status to error
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, status: 'error' as const }
          : msg
      ));

      // Retry logic
      const currentRetryCount = retryCountRef.current.get(messageId) || 0;
      if (currentRetryCount < maxRetries) {
        retryCountRef.current.set(messageId, currentRetryCount + 1);
        toast.error(`Failed to send message. Retrying... (${currentRetryCount + 1}/${maxRetries})`);
        
        setTimeout(() => {
          sendMessage(content, attachments, currentRetryCount + 1);
        }, Math.pow(2, currentRetryCount) * 1000); // Exponential backoff
      } else {
        toast.error('Failed to send message after multiple attempts');
        onError?.(error instanceof Error ? error : new Error('Unknown error'));
      }
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, onMessageSent, onMessageReceived, onError, maxRetries, generateMessageId]);

  // Retry failed message
  const retryMessage = useCallback((messageId: string) => {
    const message = messages.find(msg => msg.id === messageId);
    if (message && message.status === 'error') {
      sendMessage(message.content, message.attachments || []);
    }
  }, [messages, sendMessage]);

  // Edit message
  const editMessage = useCallback((messageId: string, newContent: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, content: newContent, timestamp: new Date() }
        : msg
    ));
    toast.success('Message updated');
  }, []);

  // Delete message
  const deleteMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
    toast.success('Message deleted');
  }, []);

  // Clear chat
  const clearChat = useCallback(() => {
    setMessages([]);
    setInputValue('');
    setAttachments([]);
    toast.success('Chat cleared');
  }, []);

  // Export chat
  const exportChat = useCallback((format: 'json' | 'txt' | 'md' = 'txt') => {
    let content = '';
    
    switch (format) {
      case 'json':
        content = JSON.stringify(messages, null, 2);
        break;
      case 'md':
        content = messages.map(msg => 
          `**${msg.role === 'user' ? 'You' : 'Assistant'}** (${msg.timestamp.toLocaleString()})\n\n${msg.content}\n\n---\n`
        ).join('\n');
        break;
      default: // txt
        content = messages.map(msg => 
          `[${msg.timestamp.toLocaleString()}] ${msg.role === 'user' ? 'You' : 'Assistant'}: ${msg.content}`
        ).join('\n\n');
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success(`Chat exported as ${format.toUpperCase()}`);
  }, [messages]);

  // Auto-save functionality
  useEffect(() => {
    if (autoSave && sessionId && messages.length > 0) {
      const saveTimeout = setTimeout(() => {
        localStorage.setItem(`chat_${sessionId}`, JSON.stringify(messages));
      }, 1000);

      return () => clearTimeout(saveTimeout);
    }
  }, [messages, sessionId, autoSave]);

  // Load saved messages on mount
  useEffect(() => {
    if (sessionId) {
      const saved = localStorage.getItem(`chat_${sessionId}`);
      if (saved) {
        try {
          const savedMessages = JSON.parse(saved);
          setMessages(savedMessages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          })));
        } catch (error) {
          console.error('Failed to load saved messages:', error);
        }
      }
    }
  }, [sessionId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    // State
    messages,
    isLoading,
    isTyping,
    connectionStatus,
    inputValue,
    attachments,
    
    // Actions
    sendMessage,
    retryMessage,
    editMessage,
    deleteMessage,
    clearChat,
    exportChat,
    setInputValue,
    setAttachments,
    
    // Utilities
    messageCount: messages.length,
    lastMessage: messages[messages.length - 1],
    hasUnsavedChanges: messages.some(msg => msg.status === 'sending' || msg.status === 'error')
  };
}
