import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { twMerge } from 'tailwind-merge';
import { 
  Send, 
  Paperclip, 
  Mic, 
  Square, 
  ArrowUp, 
  ArrowDown,
  Command,
  Loader2,
  FileText,
  X
} from 'lucide-react';
import { toast } from 'sonner';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (message: string, attachments?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
  showTyping?: boolean;
  agentName?: string;
  className?: string;
}

interface CommandSuggestion {
  command: string;
  description: string;
  category: string;
}

const SLASH_COMMANDS: CommandSuggestion[] = [
  { command: '/clear', description: 'Clear current conversation', category: 'Session' },
  { command: '/new', description: 'Start new conversation', category: 'Session' },
  { command: '/export', description: 'Export conversation', category: 'Data' },
  { command: '/help', description: 'Show available commands', category: 'Help' },
  { command: '/settings', description: 'Open settings', category: 'Config' },
];

export default function AdvancedChatInput({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = 'Type your message...',
  maxLength = 4000,
  showTyping = false,
  agentName = 'Assistant',
  className
}: ChatInputProps) {
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [commandFilter, setCommandFilter] = useState('');
  const [messageHistory, setMessageHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isDragOver, setIsDragOver] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const commandsRef = useRef<HTMLDivElement>(null);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 120); // Max 120px
      textarea.style.height = `${newHeight}px`;
    }
  }, []);

  useEffect(() => {
    adjustTextareaHeight();
  }, [value, adjustTextareaHeight]);

  // Handle slash commands
  useEffect(() => {
    const shouldShowCommands = value.startsWith('/') && value.length > 1;
    setShowCommands(shouldShowCommands);
    
    if (shouldShowCommands) {
      const filter = value.slice(1).toLowerCase();
      setCommandFilter(filter);
    }
  }, [value]);

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send message with Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSend();
      return;
    }

    // Send message with Enter (if not shift+enter)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
      return;
    }

    // Navigate command suggestions
    if (showCommands) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        // Handle command navigation
        return;
      }
      if (e.key === 'Escape') {
        setShowCommands(false);
        return;
      }
    }

    // Navigate message history
    if (e.key === 'ArrowUp' && value === '' && messageHistory.length > 0) {
      e.preventDefault();
      const newIndex = historyIndex === -1 ? messageHistory.length - 1 : Math.max(0, historyIndex - 1);
      setHistoryIndex(newIndex);
      onChange(messageHistory[newIndex]);
      return;
    }

    if (e.key === 'ArrowDown' && historyIndex !== -1) {
      e.preventDefault();
      const newIndex = historyIndex + 1;
      if (newIndex >= messageHistory.length) {
        setHistoryIndex(-1);
        onChange('');
      } else {
        setHistoryIndex(newIndex);
        onChange(messageHistory[newIndex]);
      }
      return;
    }
  };

  const handleSend = () => {
    if (!value.trim() && attachments.length === 0) return;
    if (disabled) return;

    // Handle slash commands
    if (value.startsWith('/')) {
      handleSlashCommand(value);
      return;
    }

    // Add to history
    if (value.trim()) {
      setMessageHistory(prev => [...prev.slice(-19), value.trim()]); // Keep last 20
      setHistoryIndex(-1);
    }

    onSend(value, attachments);
    onChange('');
    setAttachments([]);
    setShowCommands(false);
  };

  const handleSlashCommand = (command: string) => {
    const cmd = command.toLowerCase().trim();
    
    switch (cmd) {
      case '/clear':
        // Emit clear conversation event
        toast.info('Conversation cleared');
        break;
      case '/new':
        // Emit new conversation event
        toast.info('Starting new conversation');
        break;
      case '/export':
        // Emit export event
        toast.info('Exporting conversation...');
        break;
      case '/help':
        // Show help
        const helpText = SLASH_COMMANDS.map(c => `${c.command} - ${c.description}`).join('\n');
        toast.info('Available commands:\n' + helpText);
        break;
      default:
        toast.error('Unknown command. Type /help for available commands.');
    }
    
    onChange('');
    setShowCommands(false);
  };

  // File handling
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(file => {
      // Basic validation - can be expanded
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        toast.error(`File ${file.name} is too large (max 10MB)`);
        return false;
      }
      return true;
    });
    
    setAttachments(prev => [...prev, ...validFiles]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  // Drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(file => {
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        toast.error(`File ${file.name} is too large (max 10MB)`);
        return false;
      }
      return true;
    });
    
    setAttachments(prev => [...prev, ...validFiles]);
  };

  const filteredCommands = SLASH_COMMANDS.filter(cmd =>
    cmd.command.toLowerCase().includes(commandFilter) ||
    cmd.description.toLowerCase().includes(commandFilter)
  );

  const characterCount = value.length;
  const isNearLimit = characterCount > maxLength * 0.8;
  const isOverLimit = characterCount > maxLength;

  return (
    <div className={twMerge('relative', className)}>
      {/* Command Suggestions */}
      {showCommands && filteredCommands.length > 0 && (
        <div 
          ref={commandsRef}
          className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto z-50"
        >
          {filteredCommands.map((cmd, index) => (
            <div
              key={cmd.command}
              className="px-4 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
              onClick={() => {
                onChange(cmd.command + ' ');
                setShowCommands(false);
                textareaRef.current?.focus();
              }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-blue-600">{cmd.command}</span>
                  <span className="text-gray-600 ml-2">{cmd.description}</span>
                </div>
                <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                  {cmd.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Attachments */}
      {attachments.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {attachments.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2"
            >
              <FileText className="h-4 w-4 text-blue-600" />
              <span className="text-sm text-blue-800 truncate max-w-32">
                {file.name}
              </span>
              <button
                onClick={() => removeAttachment(index)}
                className="text-blue-600 hover:text-blue-800"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Main Input Area */}
      <div
        className={twMerge(
          'relative border border-gray-200 rounded-xl bg-white transition-all duration-200',
          'focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100',
          isDragOver && 'border-blue-400 ring-2 ring-blue-100 bg-blue-50',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          maxLength={maxLength}
          className={twMerge(
            'resize-none border-none bg-transparent min-h-[44px] max-h-[120px]',
            'focus-visible:ring-0 focus-visible:ring-offset-0 pr-20',
            'placeholder:text-gray-400'
          )}
          style={{ height: 'auto' }}
        />

        {/* Input Actions */}
        <div className="absolute right-2 bottom-2 flex items-center gap-1">
          {/* Attachment Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-gray-500 hover:text-gray-700"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          {/* Voice Recording Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={twMerge(
              'h-8 w-8',
              isRecording ? 'text-red-500 hover:text-red-700' : 'text-gray-500 hover:text-gray-700'
            )}
            onClick={() => setIsRecording(!isRecording)}
            disabled={disabled}
          >
            {isRecording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </Button>

          {/* Send Button */}
          <Button
            type="button"
            size="icon"
            className="h-8 w-8"
            onClick={handleSend}
            disabled={disabled || (!value.trim() && attachments.length === 0) || isOverLimit}
          >
            {disabled ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileSelect}
          accept=".txt,.pdf,.doc,.docx,.png,.jpg,.jpeg,.gif"
        />
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between mt-2 px-1">
        <div className="flex items-center gap-4 text-xs text-gray-500">
          {/* Typing Indicator */}
          {showTyping && (
            <div className="flex items-center gap-1">
              <div className="flex gap-1">
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span>{agentName} is typing...</span>
            </div>
          )}

          {/* Keyboard Shortcuts */}
          {!showTyping && (
            <div className="flex items-center gap-1">
              <Command className="h-3 w-3" />
              <span>Enter to send • ⇧Enter for new line</span>
            </div>
          )}
        </div>

        {/* Character Count */}
        <div className={twMerge(
          'text-xs',
          isOverLimit ? 'text-red-500' : isNearLimit ? 'text-yellow-600' : 'text-gray-400'
        )}>
          {characterCount}/{maxLength}
        </div>
      </div>
    </div>
  );
}
