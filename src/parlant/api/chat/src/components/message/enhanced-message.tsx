import React, { useState, useRef } from 'react';
import { twMerge } from 'tailwind-merge';
import { 
  Copy, 
  RotateCcw, 
  Edit3, 
  ThumbsUp, 
  ThumbsDown, 
  Share, 
  MoreHorizontal,
  Check,
  X,
  Save
} from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import Markdown from '../markdown/markdown';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';

interface MessageProps {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  isEditing?: boolean;
  onEdit?: (id: string, newContent: string) => void;
  onRegenerate?: (id: string) => void;
  onCopy?: (content: string) => void;
  onShare?: (id: string) => void;
  onFeedback?: (id: string, type: 'positive' | 'negative') => void;
  className?: string;
  showActions?: boolean;
  isStreaming?: boolean;
}

export default function EnhancedMessage({
  id,
  content,
  role,
  timestamp,
  isEditing = false,
  onEdit,
  onRegenerate,
  onCopy,
  onShare,
  onFeedback,
  className,
  showActions = true,
  isStreaming = false
}: MessageProps) {
  const [isEditMode, setIsEditMode] = useState(isEditing);
  const [editContent, setEditContent] = useState(content);
  const [showFullActions, setShowFullActions] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
      onCopy?.(content);
      toast.success('Message copied to clipboard');
    } catch (error) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = content;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
      onCopy?.(content);
      toast.success('Message copied to clipboard');
    }
  };

  const handleEdit = () => {
    setIsEditMode(true);
    setEditContent(content);
    setTimeout(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(content.length, content.length);
    }, 100);
  };

  const handleSaveEdit = () => {
    if (editContent.trim() !== content) {
      onEdit?.(id, editContent.trim());
      toast.success('Message updated');
    }
    setIsEditMode(false);
  };

  const handleCancelEdit = () => {
    setEditContent(content);
    setIsEditMode(false);
  };

  const handleRegenerate = () => {
    onRegenerate?.(id);
    toast.info('Regenerating response...');
  };

  const handleFeedback = (type: 'positive' | 'negative') => {
    setFeedback(type);
    onFeedback?.(id, type);
    toast.success(`Feedback recorded: ${type === 'positive' ? 'Helpful' : 'Not helpful'}`);
  };

  const handleShare = () => {
    onShare?.(id);
    toast.info('Sharing options...');
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isUser = role === 'user';
  const isAssistant = role === 'assistant';

  return (
    <div 
      className={twMerge(
        'group relative flex gap-3 p-4 hover:bg-gray-50/50 transition-colors',
        isUser && 'flex-row-reverse',
        className
      )}
      onMouseEnter={() => setShowFullActions(true)}
      onMouseLeave={() => setShowFullActions(false)}
    >
      {/* Avatar */}
      <div className={twMerge(
        'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
        isUser ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
      )}>
        {isUser ? 'U' : 'A'}
      </div>

      {/* Message Content */}
      <div className={twMerge(
        'flex-1 min-w-0',
        isUser && 'flex flex-col items-end'
      )}>
        {/* Message Header */}
        <div className={twMerge(
          'flex items-center gap-2 mb-1',
          isUser && 'flex-row-reverse'
        )}>
          <span className="text-sm font-medium text-gray-900">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs text-gray-500">
            {formatTime(timestamp)}
          </span>
          {isStreaming && (
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
        </div>

        {/* Message Body */}
        <div className={twMerge(
          'relative max-w-3xl',
          isUser && 'ml-auto'
        )}>
          {isEditMode ? (
            <div className="space-y-3">
              <Textarea
                ref={textareaRef}
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="min-h-[100px] resize-none"
                placeholder="Edit your message..."
              />
              <div className="flex gap-2 justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancelEdit}
                >
                  <X className="h-3 w-3 mr-1" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveEdit}
                  disabled={!editContent.trim() || editContent.trim() === content}
                >
                  <Save className="h-3 w-3 mr-1" />
                  Save
                </Button>
              </div>
            </div>
          ) : (
            <div className={twMerge(
              'prose prose-sm max-w-none',
              'bg-white border border-gray-200 rounded-lg p-4 shadow-sm',
              isUser && 'bg-blue-50 border-blue-200'
            )}>
              {isAssistant ? (
                <Markdown>{content}</Markdown>
              ) : (
                <p className="whitespace-pre-wrap text-gray-900 m-0">{content}</p>
              )}
            </div>
          )}

          {/* Quick Actions */}
          {showActions && !isEditMode && (
            <div className={twMerge(
              'absolute -bottom-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity',
              'bg-white border border-gray-200 rounded-lg shadow-sm px-2 py-1',
              isUser ? 'right-0' : 'left-0'
            )}>
              {/* Copy Button */}
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={handleCopy}
              >
                {copySuccess ? (
                  <Check className="h-3 w-3 text-green-600" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </Button>

              {/* Edit Button (for user messages) */}
              {isUser && onEdit && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={handleEdit}
                >
                  <Edit3 className="h-3 w-3" />
                </Button>
              )}

              {/* Regenerate Button (for assistant messages) */}
              {isAssistant && onRegenerate && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={handleRegenerate}
                >
                  <RotateCcw className="h-3 w-3" />
                </Button>
              )}

              {/* Feedback Buttons (for assistant messages) */}
              {isAssistant && onFeedback && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={twMerge(
                      'h-6 w-6 p-0',
                      feedback === 'positive' && 'text-green-600 bg-green-50'
                    )}
                    onClick={() => handleFeedback('positive')}
                  >
                    <ThumbsUp className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={twMerge(
                      'h-6 w-6 p-0',
                      feedback === 'negative' && 'text-red-600 bg-red-50'
                    )}
                    onClick={() => handleFeedback('negative')}
                  >
                    <ThumbsDown className="h-3 w-3" />
                  </Button>
                </>
              )}

              {/* More Actions */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                  >
                    <MoreHorizontal className="h-3 w-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align={isUser ? 'end' : 'start'}>
                  <DropdownMenuItem onClick={handleShare}>
                    <Share className="h-3 w-3 mr-2" />
                    Share
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleCopy}>
                    <Copy className="h-3 w-3 mr-2" />
                    Copy text
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
