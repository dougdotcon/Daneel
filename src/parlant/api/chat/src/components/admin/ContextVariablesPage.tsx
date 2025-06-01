import React, { useState } from 'react';
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Eye, 
  Database,
  Clock,
  Tag,
  Loader2,
  AlertCircle,
  Variable
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useFetch } from '@/hooks/useFetch';

interface ContextVariable {
  id: string;
  name: string;
  description: string;
  tool_id?: {
    service_name: string;
    tool_name: string;
  };
  freshness_rules?: {
    max_age_seconds?: number;
    refresh_on_access?: boolean;
  };
  tags: string[];
}

interface ContextVariableValue {
  key: string;
  value: any;
  last_updated: string;
}

const ContextVariablesPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVariable, setSelectedVariable] = useState<string | null>(null);

  // Fetch real data from APIs
  const { data: variables, loading: variablesLoading, refetch: refetchVariables } = useFetch<ContextVariable[]>('context-variables');
  const { data: tags, loading: tagsLoading } = useFetch<{id: string, name: string}[]>('tags');

  const filteredVariables = variables?.filter(variable => 
    variable.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    variable.description.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir esta variável de contexto?')) return;
    
    try {
      const response = await fetch(`/context-variables/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        refetchVariables();
      }
    } catch (error) {
      console.error('Error deleting context variable:', error);
    }
  };

  const formatFreshnessRules = (rules?: ContextVariable['freshness_rules']) => {
    if (!rules) return 'Sem regras de atualização';
    
    const parts = [];
    if (rules.max_age_seconds) {
      const hours = Math.floor(rules.max_age_seconds / 3600);
      const minutes = Math.floor((rules.max_age_seconds % 3600) / 60);
      if (hours > 0) parts.push(`${hours}h`);
      if (minutes > 0) parts.push(`${minutes}m`);
      parts.push('max age');
    }
    if (rules.refresh_on_access) {
      parts.push('refresh on access');
    }
    
    return parts.join(', ') || 'Configuração personalizada';
  };

  if (variablesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-600">Carregando variáveis de contexto...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Context Variables</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Gerencie variáveis de contexto para personalização de agentes
          </p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Nova Variável
        </Button>
      </div>

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Buscar por nome ou descrição..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <Variable className="h-5 w-5 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Total</p>
              <p className="text-lg font-semibold text-blue-600">
                {variables?.length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <Database className="h-5 w-5 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Com Tool</p>
              <p className="text-lg font-semibold text-green-600">
                {variables?.filter(v => v.tool_id).length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <Clock className="h-5 w-5 text-orange-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Com Freshness</p>
              <p className="text-lg font-semibold text-orange-600">
                {variables?.filter(v => v.freshness_rules).length || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Variables List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Variáveis de Contexto ({filteredVariables.length})
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredVariables.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <Variable className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                Nenhuma variável encontrada
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {searchTerm 
                  ? 'Tente ajustar o termo de busca.'
                  : 'Comece criando sua primeira variável de contexto.'
                }
              </p>
            </div>
          ) : (
            filteredVariables.map((variable) => (
              <div key={variable.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-lg font-medium text-gray-900 dark:text-white">
                        {variable.name}
                      </h4>
                      {variable.tool_id && (
                        <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-800">
                          Tool: {variable.tool_id.service_name}.{variable.tool_id.tool_name}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {variable.description}
                    </p>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatFreshnessRules(variable.freshness_rules)}
                      </div>
                      
                      {variable.tags.length > 0 && (
                        <div className="flex items-center gap-1">
                          <Tag className="h-3 w-3" />
                          {variable.tags.length} tag(s)
                        </div>
                      )}
                    </div>
                    
                    {variable.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {variable.tags.map(tagId => {
                          const tag = tags?.find(t => t.id === tagId);
                          return (
                            <span
                              key={tagId}
                              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
                            >
                              <Tag className="h-3 w-3 mr-1" />
                              {tag?.name || tagId}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2 ml-4">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setSelectedVariable(variable.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleDelete(variable.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Variable Details Modal would go here */}
      {selectedVariable && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Detalhes da Variável
                </h3>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setSelectedVariable(null)}
                >
                  ×
                </Button>
              </div>
            </div>
            <div className="px-6 py-4">
              <p className="text-gray-600 dark:text-gray-400">
                Detalhes e valores da variável seriam exibidos aqui...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContextVariablesPage;
