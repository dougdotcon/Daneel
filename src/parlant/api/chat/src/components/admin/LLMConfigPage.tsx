import React, { useState } from 'react';
import {
  Plus,
  Settings,
  Trash2,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Loader2,
  Cpu,
  Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import LLMProviderModal from './modals/LLMProviderModal';

interface LLMProvider {
  id: string;
  name: string;
  type: 'openai' | 'anthropic' | 'google' | 'ollama' | 'custom';
  status: 'connected' | 'disconnected' | 'testing';
  apiKey?: string;
  baseUrl?: string;
  model: string;
  lastTested?: string;
}

interface LLMProviderCardProps {
  provider: LLMProvider;
  onEdit: (provider: LLMProvider) => void;
  onDelete: (provider: LLMProvider) => void;
  onTest: (provider: LLMProvider) => void;
}

const LLMProviderCard: React.FC<LLMProviderCardProps> = ({ provider, onEdit, onDelete, onTest }) => {
  const [showApiKey, setShowApiKey] = useState(false);

  const getStatusIcon = () => {
    switch (provider.status) {
      case 'connected':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'disconnected':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'testing':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (provider.status) {
      case 'connected':
        return 'text-green-600 dark:text-green-400';
      case 'disconnected':
        return 'text-red-600 dark:text-red-400';
      case 'testing':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getProviderIcon = () => {
    switch (provider.type) {
      case 'openai':
        return <Zap className="h-6 w-6 text-green-500" />;
      case 'anthropic':
        return <Cpu className="h-6 w-6 text-orange-500" />;
      case 'google':
        return <Zap className="h-6 w-6 text-blue-500" />;
      case 'ollama':
        return <Settings className="h-6 w-6 text-purple-500" />;
      default:
        return <Settings className="h-6 w-6 text-gray-500" />;
    }
  };

  const maskApiKey = (key?: string) => {
    if (!key) return 'Não configurado';
    if (showApiKey) return key;
    return key.substring(0, 8) + '...' + key.substring(key.length - 4);
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getProviderIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {provider.name}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
              {provider.type}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className={`text-sm font-medium ${getStatusColor()}`}>
            {provider.status === 'connected' ? 'Conectado' :
             provider.status === 'testing' ? 'Testando...' : 'Desconectado'}
          </span>
        </div>
      </div>

      <div className="space-y-3 mb-4">
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Modelo
          </label>
          <p className="text-sm text-gray-900 dark:text-white">
            {provider.model}
          </p>
        </div>

        {provider.apiKey && (
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              API Key
            </label>
            <div className="flex items-center space-x-2">
              <p className="text-sm text-gray-900 dark:text-white font-mono">
                {maskApiKey(provider.apiKey)}
              </p>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        )}

        {provider.baseUrl && (
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              URL Base
            </label>
            <p className="text-sm text-gray-900 dark:text-white">
              {provider.baseUrl}
            </p>
          </div>
        )}

        {provider.lastTested && (
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Último Teste
            </label>
            <p className="text-sm text-gray-900 dark:text-white">
              {new Date(provider.lastTested).toLocaleString('pt-BR')}
            </p>
          </div>
        )}
      </div>

      <div className="flex space-x-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={() => onEdit(provider)}
        >
          <Settings className="h-4 w-4 mr-2" />
          Configurar
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onTest(provider)}
          disabled={provider.status === 'testing'}
        >
          {provider.status === 'testing' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <CheckCircle className="h-4 w-4" />
          )}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDelete(provider)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

const LLMConfigPage: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | null>(null);
  const [providers, setProviders] = useState<LLMProvider[]>([
    {
      id: '1',
      name: 'OpenAI GPT-4o',
      type: 'openai',
      status: 'connected',
      apiKey: 'sk-1234567890abcdef1234567890abcdef',
      model: 'gpt-4o',
      lastTested: new Date().toISOString(),
    },
    {
      id: '2',
      name: 'OpenAI GPT-4o Mini',
      type: 'openai',
      status: 'connected',
      apiKey: 'sk-1234567890abcdef1234567890abcdef',
      model: 'gpt-4o-mini',
      lastTested: new Date().toISOString(),
    },
    {
      id: '3',
      name: 'Claude 3.5 Sonnet',
      type: 'anthropic',
      status: 'connected',
      apiKey: 'sk-ant-1234567890abcdef1234567890abcdef',
      model: 'claude-3-5-sonnet-20241022',
      lastTested: new Date().toISOString(),
    },
    {
      id: '4',
      name: 'Gemini 1.5 Pro',
      type: 'google',
      status: 'disconnected',
      apiKey: 'AIzaSy1234567890abcdef1234567890abcdef',
      baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
      model: 'gemini-1.5-pro',
      lastTested: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: '5',
      name: 'Ollama Local',
      type: 'ollama',
      status: 'connected',
      baseUrl: 'http://localhost:11434',
      model: 'llama3.1:8b',
      lastTested: new Date().toISOString(),
    },
  ]);

  const handleEdit = (provider: LLMProvider) => {
    setSelectedProvider(provider);
    setModalMode('edit');
    setModalOpen(true);
  };

  const handleDelete = (provider: LLMProvider) => {
    if (window.confirm(`Tem certeza que deseja excluir o provedor "${provider.name}"?`)) {
      setProviders(prev => prev.filter(p => p.id !== provider.id));
    }
  };

  const handleTest = async (provider: LLMProvider) => {
    // Simular teste de conectividade
    setProviders(prev => prev.map(p =>
      p.id === provider.id ? { ...p, status: 'testing' } : p
    ));

    // Simular delay do teste
    setTimeout(() => {
      const success = Math.random() > 0.3; // 70% chance de sucesso
      setProviders(prev => prev.map(p =>
        p.id === provider.id ? {
          ...p,
          status: success ? 'connected' : 'disconnected',
          lastTested: new Date().toISOString()
        } : p
      ));
    }, 2000);
  };

  const handleAddProvider = () => {
    setSelectedProvider(null);
    setModalMode('create');
    setModalOpen(true);
  };

  const handleModalSave = async (providerData: Omit<LLMProvider, 'id'>): Promise<boolean> => {
    try {
      if (modalMode === 'create') {
        const newProvider: LLMProvider = {
          ...providerData,
          id: Date.now().toString(),
          status: 'disconnected',
          lastTested: undefined
        };
        setProviders(prev => [...prev, newProvider]);
      } else if (selectedProvider) {
        setProviders(prev => prev.map(p =>
          p.id === selectedProvider.id
            ? { ...p, ...providerData, lastTested: new Date().toISOString() }
            : p
        ));
      }
      return true;
    } catch (error) {
      console.error('Error saving provider:', error);
      return false;
    }
  };

  const handleModalTest = async (providerData: Omit<LLMProvider, 'id'>): Promise<boolean> => {
    // Simular teste de conectividade
    await new Promise(resolve => setTimeout(resolve, 2000));
    return Math.random() > 0.3; // 70% chance de sucesso
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedProvider(null);
  };

  const connectedCount = providers.filter(p => p.status === 'connected').length;
  const totalCount = providers.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Configuração de Provedores LLM
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Configure e gerencie seus provedores de linguagem
          </p>
        </div>
        <Button onClick={handleAddProvider}>
          <Plus className="h-4 w-4 mr-2" />
          Adicionar Provedor
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <Settings className="h-5 w-5 text-blue-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{totalCount}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Conectados</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{connectedCount}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <Zap className="h-5 w-5 text-yellow-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Taxa de Sucesso</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {totalCount > 0 ? Math.round((connectedCount / totalCount) * 100) : 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Providers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {providers.map((provider) => (
          <LLMProviderCard
            key={provider.id}
            provider={provider}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onTest={handleTest}
          />
        ))}
      </div>

      {providers.length === 0 && (
        <div className="text-center py-12">
          <Settings className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            Nenhum provedor configurado
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Comece adicionando seu primeiro provedor LLM.
          </p>
          <div className="mt-6">
            <Button onClick={handleAddProvider}>
              <Plus className="h-4 w-4 mr-2" />
              Adicionar Provedor
            </Button>
          </div>
        </div>
      )}

      {/* LLM Provider Modal */}
      <LLMProviderModal
        isOpen={modalOpen}
        onClose={handleModalClose}
        onSave={handleModalSave}
        onTest={handleModalTest}
        provider={selectedProvider}
        mode={modalMode}
      />
    </div>
  );
};

export default LLMConfigPage;
