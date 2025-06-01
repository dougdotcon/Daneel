import React, { useState, useRef, useEffect } from 'react';
import { twMerge } from 'tailwind-merge';
import { 
  Settings, 
  Download, 
  Trash2, 
  Moon, 
  Sun,
  Maximize2,
  Minimize2,
  Volume2,
  VolumeX
} from 'lucide-react';
import { Button } from '../ui/button';
import { useEnhancedChat } from '../../hooks/useEnhancedChat';
import AdvancedChatInput from '../chat-input/advanced-chat-input';
import EnhancedMessage from '../message/enhanced-message';
import EnhancedSessionList from '../session-list/enhanced-session-list';
import { ConnectionStatus, TypingIndicator } from '../status/message-status';
import { toast } from 'sonner';

interface EnhancedChatInterfaceProps {
  sessionId?: string;
  agentName?: string;
  onNavigateToAdmin?: () => void;
  className?: string;
}

export default function EnhancedChatInterface({
  sessionId,
  agentName = 'Daneel',
  onNavigateToAdmin,
  className
}: EnhancedChatInterfaceProps) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isSoundEnabled, setIsSoundEnabled] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState(sessionId);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    isLoading,
    isTyping,
    connectionStatus,
    inputValue,
    attachments,
    sendMessage,
    retryMessage,
    editMessage,
    deleteMessage,
    clearChat,
    exportChat,
    setInputValue,
    setAttachments,
    messageCount
  } = useEnhancedChat({
    sessionId: selectedSessionId,
    onMessageSent: (message) => {
      if (isSoundEnabled) {
        // Play send sound
        playNotificationSound('send');
      }
    },
    onMessageReceived: (message) => {
      if (isSoundEnabled) {
        // Play receive sound
        playNotificationSound('receive');
      }
      scrollToBottom();
    },
    onError: (error) => {
      toast.error(`Chat error: ${error.message}`);
    }
  });

  // Mock sessions data - replace with real data
  const mockSessions = [
    {
      id: '1',
      title: 'Project Planning Discussion',
      lastMessage: 'Let me help you create a comprehensive project plan...',
      timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
      messageCount: 15,
      agentName: 'Daneel',
      isPinned: true,
      status: 'active' as const
    },
    {
      id: '2',
      title: 'Code Review Session',
      lastMessage: 'The implementation looks good, but I have a few suggestions...',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
      messageCount: 8,
      agentName: 'Daneel',
      isFavorite: true,
      status: 'idle' as const
    },
    {
      id: '3',
      title: 'API Documentation',
      lastMessage: 'Here\'s the complete API documentation you requested...',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
      messageCount: 23,
      agentName: 'Daneel',
      status: 'active' as const
    }
  ];

  const playNotificationSound = (type: 'send' | 'receive') => {
    // Create audio context for notification sounds
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.setValueAtTime(type === 'send' ? 800 : 600, audioContext.currentTime);
    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.1);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (message: string, attachments?: File[]) => {
    await sendMessage(message, attachments || []);
  };

  const handleKeyboardShortcuts = (e: KeyboardEvent) => {
    // Ctrl/Cmd + K: Clear chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      clearChat();
    }
    
    // Ctrl/Cmd + E: Export chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
      e.preventDefault();
      exportChat('txt');
    }
    
    // Ctrl/Cmd + D: Toggle dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
      e.preventDefault();
      setIsDarkMode(!isDarkMode);
    }
    
    // F11: Toggle fullscreen
    if (e.key === 'F11') {
      e.preventDefault();
      setIsFullscreen(!isFullscreen);
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyboardShortcuts);
    return () => document.removeEventListener('keydown', handleKeyboardShortcuts);
  }, [isDarkMode, isFullscreen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className={twMerge(
      'flex h-screen bg-gradient-to-br from-blue-50 to-indigo-100',
      isDarkMode && 'dark bg-gradient-to-br from-gray-900 to-gray-800',
      isFullscreen && 'fixed inset-0 z-50',
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between bg-blue-primary h-20 px-6 shadow-lg">
        <div className="flex items-center space-x-3">
          <img src='/chat/logo.png' alt='Daneel Logo' className='h-12 w-12 object-contain' />
          <div className="flex flex-col">
            <h1 className="text-white text-xl font-bold">Daneel</h1>
            <p className="text-blue-100 text-sm">Enhanced AI Assistant</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Connection Status */}
          <ConnectionStatus 
            isConnected={connectionStatus === 'connected'}
            isReconnecting={connectionStatus === 'reconnecting'}
          />

          {/* Action Buttons */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsSoundEnabled(!isSoundEnabled)}
            className="text-white hover:bg-blue-600"
          >
            {isSoundEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="text-white hover:bg-blue-600"
          >
            {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="text-white hover:bg-blue-600"
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => exportChat('txt')}
            className="text-white hover:bg-blue-600"
          >
            <Download className="h-4 w-4" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={clearChat}
            className="text-white hover:bg-blue-600"
          >
            <Trash2 className="h-4 w-4" />
          </Button>

          {onNavigateToAdmin && (
            <Button
              onClick={onNavigateToAdmin}
              variant="outline"
              className="bg-white/10 border-white/20 text-white hover:bg-white/20"
            >
              <Settings className="h-4 w-4 mr-2" />
              Admin
            </Button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Session List */}
        <div className="w-80 border-r border-gray-200 bg-white/90 backdrop-blur-sm">
          <EnhancedSessionList
            sessions={mockSessions}
            selectedSessionId={selectedSessionId}
            onSessionSelect={setSelectedSessionId}
            onSessionDelete={(id) => {
              toast.success('Session deleted');
              if (id === selectedSessionId) {
                setSelectedSessionId(undefined);
              }
            }}
            onSessionEdit={(id, title) => {
              toast.success('Session renamed');
            }}
            onSessionPin={(id, pinned) => {
              toast.success(pinned ? 'Session pinned' : 'Session unpinned');
            }}
            onSessionArchive={(id, archived) => {
              toast.success(archived ? 'Session archived' : 'Session unarchived');
            }}
            onSessionFavorite={(id, favorite) => {
              toast.success(favorite ? 'Added to favorites' : 'Removed from favorites');
            }}
          />
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {selectedSessionId ? (
            <>
              {/* Messages */}
              <div 
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto p-4 space-y-4"
              >
                {messages.map((message) => (
                  <EnhancedMessage
                    key={message.id}
                    id={message.id}
                    content={message.content}
                    role={message.role}
                    timestamp={message.timestamp}
                    onEdit={editMessage}
                    onRegenerate={message.role === 'assistant' ? retryMessage : undefined}
                    onCopy={(content) => toast.success('Copied to clipboard')}
                    onShare={(id) => toast.info('Share functionality coming soon')}
                    onFeedback={(id, type) => toast.success(`Feedback: ${type}`)}
                    isStreaming={message.id === messages[messages.length - 1]?.id && isTyping}
                  />
                ))}
                
                {isTyping && (
                  <div className="flex justify-start">
                    <TypingIndicator agentName={agentName} />
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-4 bg-white/90 backdrop-blur-sm border-t border-gray-200">
                <AdvancedChatInput
                  value={inputValue}
                  onChange={setInputValue}
                  onSend={handleSendMessage}
                  disabled={isLoading}
                  placeholder={`Message ${agentName}...`}
                  showTyping={isTyping}
                  agentName={agentName}
                />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Settings className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Welcome to Enhanced Daneel</h3>
                <p className="text-gray-600 mb-4">Select a conversation to start chatting</p>
                <p className="text-sm text-gray-500">
                  Press <kbd className="px-2 py-1 bg-gray-100 rounded">Ctrl+K</kbd> to clear chat, 
                  <kbd className="px-2 py-1 bg-gray-100 rounded ml-1">Ctrl+E</kbd> to export
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
