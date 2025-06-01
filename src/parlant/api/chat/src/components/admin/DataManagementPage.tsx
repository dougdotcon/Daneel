import React, { useState } from 'react';
import { 
  Database, 
  Download, 
  Upload, 
  Trash2, 
  RefreshCw, 
  FileText, 
  HardDrive,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Archive,
  Import,
  Export,
  BarChart3
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface DataStats {
  agents: number;
  sessions: number;
  messages: number;
  guidelines: number;
  contextVariables: number;
  utterances: number;
  tags: number;
  totalSize: string;
}

const DataManagementPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'xml'>('json');
  const [importFile, setImportFile] = useState<File | null>(null);
  const [stats, setStats] = useState<DataStats>({
    agents: 8,
    sessions: 156,
    messages: 2847,
    guidelines: 23,
    contextVariables: 15,
    utterances: 42,
    tags: 26,
    totalSize: '12.4 MB'
  });

  const handleExportData = async (type: 'all' | 'agents' | 'sessions' | 'config') => {
    setLoading(true);
    
    // Simulate export process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Create mock data for download
    const data = {
      exportDate: new Date().toISOString(),
      type,
      data: {
        agents: type === 'all' || type === 'agents' ? Array(stats.agents).fill(null).map((_, i) => ({
          id: `agent-${i}`,
          name: `Agent ${i + 1}`,
          description: `Description for agent ${i + 1}`
        })) : [],
        sessions: type === 'all' || type === 'sessions' ? Array(Math.min(stats.sessions, 10)).fill(null).map((_, i) => ({
          id: `session-${i}`,
          title: `Session ${i + 1}`,
          createdAt: new Date().toISOString()
        })) : [],
        config: type === 'all' || type === 'config' ? {
          version: '1.0.0',
          settings: { theme: 'auto', language: 'pt-BR' }
        } : null
      }
    };

    // Download file
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `daneel-${type}-${new Date().toISOString().split('T')[0]}.${exportFormat}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setLoading(false);
  };

  const handleImportData = async () => {
    if (!importFile) return;
    
    setLoading(true);
    
    // Simulate import process
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Update stats (mock)
    setStats(prev => ({
      ...prev,
      agents: prev.agents + 2,
      sessions: prev.sessions + 5,
      messages: prev.messages + 50
    }));
    
    setLoading(false);
    setImportFile(null);
  };

  const handleClearData = async (type: 'sessions' | 'messages' | 'all') => {
    if (!confirm(`Tem certeza que deseja limpar ${type === 'all' ? 'todos os dados' : type}? Esta ação não pode ser desfeita.`)) {
      return;
    }
    
    setLoading(true);
    
    // Simulate clear process
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Update stats
    if (type === 'sessions' || type === 'all') {
      setStats(prev => ({ ...prev, sessions: 0, messages: 0 }));
    } else if (type === 'messages') {
      setStats(prev => ({ ...prev, messages: 0 }));
    }
    
    setLoading(false);
  };

  const refreshStats = async () => {
    setLoading(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock updated stats
    setStats({
      agents: 8 + Math.floor(Math.random() * 3),
      sessions: 156 + Math.floor(Math.random() * 20),
      messages: 2847 + Math.floor(Math.random() * 100),
      guidelines: 23 + Math.floor(Math.random() * 5),
      contextVariables: 15 + Math.floor(Math.random() * 3),
      utterances: 42 + Math.floor(Math.random() * 8),
      tags: 26 + Math.floor(Math.random() * 4),
      totalSize: `${(12.4 + Math.random() * 5).toFixed(1)} MB`
    });
    
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Gerenciamento de Dados</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Exporte, importe e gerencie os dados do sistema Daneel
          </p>
        </div>
        <Button onClick={refreshStats} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Atualizar Estatísticas
        </Button>
      </div>

      {/* Data Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        {[
          { label: 'Agentes', value: stats.agents, icon: Database, color: 'blue' },
          { label: 'Sessões', value: stats.sessions, icon: FileText, color: 'green' },
          { label: 'Mensagens', value: stats.messages, icon: BarChart3, color: 'purple' },
          { label: 'Guidelines', value: stats.guidelines, icon: FileText, color: 'orange' },
          { label: 'Context Vars', value: stats.contextVariables, icon: Database, color: 'red' },
          { label: 'Utterances', value: stats.utterances, icon: FileText, color: 'yellow' },
          { label: 'Tags', value: stats.tags, icon: Archive, color: 'pink' },
          { label: 'Tamanho', value: stats.totalSize, icon: HardDrive, color: 'gray' }
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                    {stat.label}
                  </p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {stat.value}
                  </p>
                </div>
                <Icon className={`h-5 w-5 text-${stat.color}-500`} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Export Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Export className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Exportar Dados</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Formato de Exportação
            </label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'json' | 'csv' | 'xml')}
              className="w-full p-2 border border-gray-300 rounded-md bg-white text-gray-900"
            >
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="xml">XML</option>
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <Button 
              onClick={() => handleExportData('all')} 
              disabled={loading}
              className="w-full"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              <span className="ml-2">Todos os Dados</span>
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleExportData('agents')} 
              disabled={loading}
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              Agentes
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleExportData('sessions')} 
              disabled={loading}
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              Sessões
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleExportData('config')} 
              disabled={loading}
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              Configurações
            </Button>
          </div>
        </div>
      </div>

      {/* Import Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Import className="h-5 w-5 text-green-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Importar Dados</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Selecionar Arquivo
            </label>
            <input
              type="file"
              accept=".json,.csv,.xml"
              onChange={(e) => setImportFile(e.target.files?.[0] || null)}
              className="w-full p-2 border border-gray-300 rounded-md bg-white text-gray-900"
            />
          </div>
          
          {importFile && (
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600" />
                <span className="text-sm text-blue-800 dark:text-blue-200">
                  Arquivo selecionado: {importFile.name} ({(importFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
            </div>
          )}
          
          <Button 
            onClick={handleImportData} 
            disabled={!importFile || loading}
            className="w-full"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Upload className="h-4 w-4 mr-2" />
            )}
            Importar Dados
          </Button>
        </div>
      </div>

      {/* Data Cleanup */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Trash2 className="h-5 w-5 text-red-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Limpeza de Dados</h3>
        </div>
        
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 mb-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-900 dark:text-yellow-100">Atenção</h4>
              <p className="text-sm text-yellow-700 dark:text-yellow-200 mt-1">
                As operações de limpeza são irreversíveis. Faça backup dos dados antes de prosseguir.
              </p>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button 
            variant="outline" 
            onClick={() => handleClearData('messages')} 
            disabled={loading}
            className="w-full border-yellow-300 text-yellow-700 hover:bg-yellow-50"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Limpar Mensagens
          </Button>
          <Button 
            variant="outline" 
            onClick={() => handleClearData('sessions')} 
            disabled={loading}
            className="w-full border-orange-300 text-orange-700 hover:bg-orange-50"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Limpar Sessões
          </Button>
          <Button 
            variant="outline" 
            onClick={() => handleClearData('all')} 
            disabled={loading}
            className="w-full border-red-300 text-red-700 hover:bg-red-50"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Limpar Tudo
          </Button>
        </div>
      </div>

      {/* Status Messages */}
      {loading && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            <span className="text-blue-800 dark:text-blue-200 font-medium">
              Processando operação...
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataManagementPage;
