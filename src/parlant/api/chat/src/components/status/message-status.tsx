import React from 'react';
import { twMerge } from 'tailwind-merge';
import { 
  Clock, 
  Check, 
  CheckCheck, 
  AlertCircle, 
  Loader2,
  Send,
  Eye,
  Zap
} from 'lucide-react';

export type MessageStatus = 
  | 'sending'
  | 'sent'
  | 'delivered'
  | 'read'
  | 'error'
  | 'processing'
  | 'typing'
  | 'thinking';

interface MessageStatusProps {
  status: MessageStatus;
  timestamp?: Date;
  error?: string;
  className?: string;
  showText?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function MessageStatus({
  status,
  timestamp,
  error,
  className,
  showText = false,
  size = 'sm'
}: MessageStatusProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'sending':
        return {
          icon: Send,
          color: 'text-gray-400',
          bgColor: 'bg-gray-100',
          text: 'Sending...',
          animate: true
        };
      case 'sent':
        return {
          icon: Check,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100',
          text: 'Sent',
          animate: false
        };
      case 'delivered':
        return {
          icon: CheckCheck,
          color: 'text-blue-500',
          bgColor: 'bg-blue-100',
          text: 'Delivered',
          animate: false
        };
      case 'read':
        return {
          icon: Eye,
          color: 'text-green-500',
          bgColor: 'bg-green-100',
          text: 'Read',
          animate: false
        };
      case 'error':
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-100',
          text: error || 'Failed to send',
          animate: false
        };
      case 'processing':
        return {
          icon: Loader2,
          color: 'text-blue-500',
          bgColor: 'bg-blue-100',
          text: 'Processing...',
          animate: true
        };
      case 'typing':
        return {
          icon: Zap,
          color: 'text-blue-500',
          bgColor: 'bg-blue-100',
          text: 'Typing...',
          animate: true
        };
      case 'thinking':
        return {
          icon: Loader2,
          color: 'text-purple-500',
          bgColor: 'bg-purple-100',
          text: 'Thinking...',
          animate: true
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-400',
          bgColor: 'bg-gray-100',
          text: 'Unknown',
          animate: false
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={twMerge(
      'flex items-center gap-1',
      className
    )}>
      <div className={twMerge(
        'flex items-center justify-center rounded-full p-1',
        config.bgColor
      )}>
        <Icon 
          className={twMerge(
            sizeClasses[size],
            config.color,
            config.animate && 'animate-spin'
          )}
        />
      </div>
      
      {showText && (
        <span className={twMerge(
          'text-xs',
          config.color
        )}>
          {config.text}
        </span>
      )}
      
      {timestamp && (
        <span className="text-xs text-gray-400">
          {formatTimestamp(timestamp)}
        </span>
      )}
    </div>
  );
}

// Typing indicator component
interface TypingIndicatorProps {
  agentName?: string;
  className?: string;
}

export function TypingIndicator({ agentName = 'Assistant', className }: TypingIndicatorProps) {
  return (
    <div className={twMerge(
      'flex items-center gap-2 text-sm text-gray-500',
      className
    )}>
      <div className="flex gap-1">
        <div 
          className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" 
          style={{ animationDelay: '0ms' }} 
        />
        <div 
          className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" 
          style={{ animationDelay: '150ms' }} 
        />
        <div 
          className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" 
          style={{ animationDelay: '300ms' }} 
        />
      </div>
      <span>{agentName} is typing...</span>
    </div>
  );
}

// Connection status component
interface ConnectionStatusProps {
  isConnected: boolean;
  isReconnecting?: boolean;
  className?: string;
}

export function ConnectionStatus({ 
  isConnected, 
  isReconnecting = false, 
  className 
}: ConnectionStatusProps) {
  if (isReconnecting) {
    return (
      <div className={twMerge(
        'flex items-center gap-2 text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded-full',
        className
      )}>
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>Reconnecting...</span>
      </div>
    );
  }

  return (
    <div className={twMerge(
      'flex items-center gap-2 text-xs px-2 py-1 rounded-full',
      isConnected 
        ? 'text-green-600 bg-green-50' 
        : 'text-red-600 bg-red-50',
      className
    )}>
      <div className={twMerge(
        'w-2 h-2 rounded-full',
        isConnected ? 'bg-green-500' : 'bg-red-500'
      )} />
      <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
    </div>
  );
}

// Message delivery status for chat bubbles
interface MessageDeliveryStatusProps {
  status: MessageStatus;
  timestamp?: Date;
  className?: string;
}

export function MessageDeliveryStatus({ 
  status, 
  timestamp, 
  className 
}: MessageDeliveryStatusProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'sending':
        return <Clock className="h-3 w-3 text-gray-400" />;
      case 'sent':
        return <Check className="h-3 w-3 text-gray-500" />;
      case 'delivered':
        return <CheckCheck className="h-3 w-3 text-blue-500" />;
      case 'read':
        return <CheckCheck className="h-3 w-3 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className={twMerge(
      'flex items-center gap-1 text-xs text-gray-500',
      className
    )}>
      {getStatusIcon()}
      {timestamp && (
        <span>{timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      )}
    </div>
  );
}

// Batch status for multiple messages
interface BatchStatusProps {
  totalMessages: number;
  sentMessages: number;
  failedMessages: number;
  className?: string;
}

export function BatchStatus({ 
  totalMessages, 
  sentMessages, 
  failedMessages, 
  className 
}: BatchStatusProps) {
  const pendingMessages = totalMessages - sentMessages - failedMessages;
  const progress = (sentMessages / totalMessages) * 100;

  return (
    <div className={twMerge(
      'flex items-center gap-2 text-xs text-gray-600 bg-gray-50 px-3 py-2 rounded-lg',
      className
    )}>
      <div className="flex items-center gap-1">
        <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <span className="text-green-600">{sentMessages} sent</span>
        {pendingMessages > 0 && (
          <span className="text-yellow-600">{pendingMessages} pending</span>
        )}
        {failedMessages > 0 && (
          <span className="text-red-600">{failedMessages} failed</span>
        )}
      </div>
    </div>
  );
}
