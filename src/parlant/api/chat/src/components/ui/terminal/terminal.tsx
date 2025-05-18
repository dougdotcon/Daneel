import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '../button';
import { Copy, Check, X, Maximize2, Minimize2, Terminal as TerminalIcon } from 'lucide-react';
import { Tooltip } from '../custom/tooltip';
import { useTheme } from 'next-themes';

interface TerminalProps {
  initialContent?: string;
  prompt?: string;
  className?: string;
  onCommand?: (command: string) => Promise<string>;
  autoFocus?: boolean;
  height?: number;
  title?: string;
  readOnly?: boolean;
}

interface HistoryEntry {
  command: string;
  output: string;
}

const Terminal: React.FC<TerminalProps> = ({
  initialContent = '',
  prompt = '$ ',
  className,
  onCommand,
  autoFocus = false,
  height = 300,
  title = 'Terminal',
  readOnly = false,
}) => {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [currentCommand, setCurrentCommand] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';

  useEffect(() => {
    if (initialContent) {
      setHistory([{ command: '', output: initialContent }]);
    }
  }, [initialContent]);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [history, currentCommand]);

  const handleKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      
      if (!currentCommand.trim()) return;
      
      const command = currentCommand;
      setCurrentCommand('');
      setIsLoading(true);
      
      let output = '';
      
      try {
        if (onCommand) {
          output = await onCommand(command);
        } else {
          output = `Command not supported: ${command}`;
        }
      } catch (error) {
        output = `Error: ${error instanceof Error ? error.message : String(error)}`;
      }
      
      setHistory([...history, { command, output }]);
      setHistoryIndex(-1);
      setIsLoading(false);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      
      if (historyIndex === -1 && history.length > 0) {
        // Start navigating history from the most recent command
        const commandHistory = history.filter(entry => entry.command).map(entry => entry.command);
        if (commandHistory.length > 0) {
          setHistoryIndex(commandHistory.length - 1);
          setCurrentCommand(commandHistory[commandHistory.length - 1]);
        }
      } else if (historyIndex > 0) {
        // Navigate up in history
        const commandHistory = history.filter(entry => entry.command).map(entry => entry.command);
        setHistoryIndex(historyIndex - 1);
        setCurrentCommand(commandHistory[historyIndex - 1]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      
      if (historyIndex !== -1) {
        const commandHistory = history.filter(entry => entry.command).map(entry => entry.command);
        
        if (historyIndex < commandHistory.length - 1) {
          // Navigate down in history
          setHistoryIndex(historyIndex + 1);
          setCurrentCommand(commandHistory[historyIndex + 1]);
        } else {
          // Reached the end of history, clear command
          setHistoryIndex(-1);
          setCurrentCommand('');
        }
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      // Simple tab completion could be implemented here
    } else if (e.key === 'c' && e.ctrlKey) {
      if (isLoading) {
        setIsLoading(false);
        setHistory([...history, { command: currentCommand, output: '^C' }]);
        setCurrentCommand('');
      }
    } else if (e.key === 'l' && e.ctrlKey) {
      e.preventDefault();
      setHistory([]);
    }
  };

  const handleCopy = async () => {
    const content = history.map(entry => {
      let text = '';
      if (entry.command) {
        text += `${prompt}${entry.command}\n`;
      }
      if (entry.output) {
        text += `${entry.output}\n`;
      }
      return text;
    }).join('');
    
    await navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleClear = () => {
    setHistory([]);
    setCurrentCommand('');
    setHistoryIndex(-1);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const getOutputWithSyntaxHighlighting = (output: string) => {
    // Simple syntax highlighting for common terminal outputs
    return output.split('\n').map((line, i) => {
      if (line.startsWith('error:') || line.toLowerCase().includes('error') || line.includes('ERR!')) {
        return <div key={i} className="text-red-500">{line}</div>;
      } else if (line.startsWith('warning:') || line.toLowerCase().includes('warning') || line.includes('WARN')) {
        return <div key={i} className="text-yellow-500">{line}</div>;
      } else if (line.startsWith('success:') || line.toLowerCase().includes('success')) {
        return <div key={i} className="text-green-500">{line}</div>;
      } else if (line.match(/^\s*\d+\s*$/)) {
        return <div key={i} className="text-blue-500">{line}</div>;
      } else {
        return <div key={i}>{line}</div>;
      }
    });
  };

  return (
    <div 
      className={cn(
        'border rounded-md overflow-hidden',
        isDarkTheme ? 'bg-black border-gray-800' : 'bg-gray-900 border-gray-700',
        isFullscreen ? 'fixed inset-0 z-50' : '',
        className
      )}
    >
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 text-white">
        <div className="flex items-center">
          <TerminalIcon className="w-4 h-4 mr-2" />
          <span className="text-sm font-medium">{title}</span>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-6 w-6 p-0 text-gray-400 hover:text-white"
          >
            <Tooltip value={isCopied ? "Copied!" : "Copy terminal content"}>
              {isCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Tooltip>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="h-6 w-6 p-0 text-gray-400 hover:text-white"
          >
            <Tooltip value="Clear terminal">
              <X className="h-4 w-4" />
            </Tooltip>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleFullscreen}
            className="h-6 w-6 p-0 text-gray-400 hover:text-white"
          >
            <Tooltip value={isFullscreen ? "Exit fullscreen" : "Fullscreen"}>
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Tooltip>
          </Button>
        </div>
      </div>
      
      <div 
        ref={terminalRef}
        className="font-mono text-sm p-4 text-green-400 overflow-auto"
        style={{ height: isFullscreen ? 'calc(100vh - 40px)' : height }}
      >
        {history.map((entry, index) => (
          <div key={index}>
            {entry.command && (
              <div className="flex">
                <span className="text-blue-400 mr-1">{prompt}</span>
                <span>{entry.command}</span>
              </div>
            )}
            {entry.output && (
              <div className="whitespace-pre-wrap mb-2">
                {getOutputWithSyntaxHighlighting(entry.output)}
              </div>
            )}
          </div>
        ))}
        
        {!readOnly && (
          <div className="flex items-center">
            <span className="text-blue-400 mr-1">{prompt}</span>
            <input
              ref={inputRef}
              type="text"
              value={currentCommand}
              onChange={(e) => setCurrentCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 bg-transparent border-none outline-none text-green-400"
              disabled={isLoading}
              autoFocus={autoFocus}
              spellCheck={false}
            />
          </div>
        )}
        
        {isLoading && (
          <div className="animate-pulse">Processing...</div>
        )}
      </div>
    </div>
  );
};

export default Terminal;
