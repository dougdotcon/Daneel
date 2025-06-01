import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  Trash2, 
  Download, 
  Filter,
  Search,
  AlertCircle,
  Info,
  CheckCircle,
  AlertTriangle,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  message: string;
  source: string;
  metadata?: Record<string, any>;
}

const LogsPage: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Mock log generation for demonstration
  useEffect(() => {
    if (!isStreaming) return;

    const sources = ['api', 'agent', 'database', 'llm', 'session'];
    const levels: LogEntry['level'][] = ['debug', 'info', 'warning', 'error'];
    const messages = [
      'Request processed successfully',
      'Agent response generated',
      'Database connection established',
      'LLM API call completed',
      'Session created',
      'User authentication successful',
      'Configuration updated',
      'Error processing request',
      'Warning: High memory usage',
      'Debug: Processing user input'
    ];

    const interval = setInterval(() => {
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        level: levels[Math.floor(Math.random() * levels.length)],
        message: messages[Math.floor(Math.random() * messages.length)],
        source: sources[Math.floor(Math.random() * sources.length)],
        metadata: {
          userId: Math.floor(Math.random() * 1000),
          duration: Math.floor(Math.random() * 1000) + 'ms'
        }
      };

      setLogs(prev => [...prev.slice(-99), newLog]); // Keep last 100 logs
    }, 2000);

    return () => clearInterval(interval);
  }, [isStreaming]);

  // Filter logs based on search and filters
  useEffect(() => {
    let filtered = logs;

    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.source.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (levelFilter !== 'all') {
      filtered = filtered.filter(log => log.level === levelFilter);
    }

    if (sourceFilter !== 'all') {
      filtered = filtered.filter(log => log.source === sourceFilter);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, levelFilter, sourceFilter]);

  // Auto scroll to bottom
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, autoScroll]);

  const handleScroll = () => {
    if (!logsContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop <= clientHeight + 50;
    setAutoScroll(isAtBottom);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const downloadLogs = () => {
    const logText = filteredLogs.map(log => 
      `[${log.timestamp}] ${log.level.toUpperCase()} [${log.source}] ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getLevelIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'debug':
        return <CheckCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return 'text-red-600 dark:text-red-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'info':
        return 'text-blue-600 dark:text-blue-400';
      case 'debug':
        return 'text-gray-600 dark:text-gray-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('pt-BR');
  };

  const uniqueSources = Array.from(new Set(logs.map(log => log.source)));

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Logs do Sistema</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Monitore logs em tempo real
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsStreaming(!isStreaming)}
          >
            {isStreaming ? (
              <>
                <Pause className="h-4 w-4 mr-2" />
                Pausar
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Iniciar
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={downloadLogs}
            disabled={filteredLogs.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={clearLogs}
            disabled={logs.length === 0}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Limpar
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Buscar logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={levelFilter} onValueChange={setLevelFilter}>
          <SelectTrigger className="w-full sm:w-32">
            <SelectValue placeholder="Nível" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="error">Error</SelectItem>
            <SelectItem value="warning">Warning</SelectItem>
            <SelectItem value="info">Info</SelectItem>
            <SelectItem value="debug">Debug</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sourceFilter} onValueChange={setSourceFilter}>
          <SelectTrigger className="w-full sm:w-32">
            <SelectValue placeholder="Fonte" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {uniqueSources.map(source => (
              <SelectItem key={source} value={source}>
                {source}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {['error', 'warning', 'info', 'debug'].map(level => {
          const count = logs.filter(log => log.level === level).length;
          return (
            <div key={level} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                {getLevelIcon(level as LogEntry['level'])}
                <div>
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    {level}
                  </p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {count}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            {isStreaming ? (
              <Loader2 className="h-4 w-4 text-green-500 animate-spin" />
            ) : (
              <Pause className="h-4 w-4 text-gray-500" />
            )}
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Status
              </p>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {isStreaming ? 'Streaming' : 'Pausado'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Logs Container */}
      <div className="flex-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div 
          ref={logsContainerRef}
          onScroll={handleScroll}
          className="h-96 overflow-y-auto p-4 space-y-2 font-mono text-sm"
        >
          {filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
              {logs.length === 0 ? 'Nenhum log disponível' : 'Nenhum log corresponde aos filtros'}
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className="flex items-start space-x-3 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded"
              >
                <span className="text-xs text-gray-500 dark:text-gray-400 w-20 flex-shrink-0">
                  {formatTimestamp(log.timestamp)}
                </span>
                <div className="flex items-center space-x-2 w-16 flex-shrink-0">
                  {getLevelIcon(log.level)}
                  <span className={cn("text-xs font-medium uppercase", getLevelColor(log.level))}>
                    {log.level}
                  </span>
                </div>
                <span className="text-xs text-purple-600 dark:text-purple-400 w-16 flex-shrink-0">
                  [{log.source}]
                </span>
                <span className="text-gray-900 dark:text-white flex-1">
                  {log.message}
                </span>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Auto-scroll indicator */}
      {!autoScroll && (
        <div className="fixed bottom-4 right-4">
          <Button
            size="sm"
            onClick={() => {
              setAutoScroll(true);
              logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Ir para o final
          </Button>
        </div>
      )}
    </div>
  );
};

export default LogsPage;
