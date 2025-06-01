import React from 'react';
import { X, Calendar, Tag, FileText, MessageSquare, Clock, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Agent } from '@/hooks/useAgents';

interface AgentViewModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent: Agent | null;
  sessionCount?: number;
}

const AgentViewModal: React.FC<AgentViewModalProps> = ({ 
  isOpen, 
  onClose, 
  agent,
  sessionCount = 0
}) => {
  if (!isOpen || !agent) return null;

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('pt-BR');
    } catch {
      return 'Data inválida';
    }
  };

  const formatMetadata = (metadata: Record<string, any>) => {
    if (!metadata || Object.keys(metadata).length === 0) {
      return 'Nenhum metadado disponível';
    }
    return JSON.stringify(metadata, null, 2);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Detalhes do Agente
            </h3>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Basic Info */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Informações Básicas
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nome
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                    {agent.name}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    ID
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-md font-mono">
                    {agent.id}
                  </p>
                </div>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Descrição
              </label>
              <p className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                {agent.description}
              </p>
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tags
              </label>
              {agent.tags.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {agent.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                    >
                      <Tag className="h-3 w-3 mr-1" />
                      {tag}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                  Nenhuma tag definida
                </p>
              )}
            </div>

            {/* Statistics */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Estatísticas
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <div className="flex items-center">
                    <MessageSquare className="h-5 w-5 text-blue-500 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Sessões
                      </p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {sessionCount}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Tag className="h-5 w-5 text-green-500 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Tags
                      </p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {agent.tags.length}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <div className="flex items-center">
                    <Calendar className="h-5 w-5 text-purple-500 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Criado em
                      </p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {formatDate(agent.creation_utc).split(' ')[0]}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Timestamps */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Informações Temporais
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data de Criação
                  </label>
                  <div className="flex items-center text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                    <Calendar className="h-4 w-4 mr-2 text-gray-500" />
                    {formatDate(agent.creation_utc)}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Última Atividade
                  </label>
                  <div className="flex items-center text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
                    <Clock className="h-4 w-4 mr-2 text-gray-500" />
                    {sessionCount > 0 ? 'Recente' : 'Nunca usado'}
                  </div>
                </div>
              </div>
            </div>

            {/* Metadata */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Metadados
              </h4>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <pre className="text-xs text-gray-600 dark:text-gray-300 whitespace-pre-wrap overflow-x-auto">
                  {formatMetadata(agent.metadata)}
                </pre>
              </div>
            </div>

            {/* Actions Section */}
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Ações Disponíveis
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Button variant="outline" className="justify-start">
                  <FileText className="h-4 w-4 mr-2" />
                  Ver Guidelines
                </Button>
                <Button variant="outline" className="justify-start">
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Ver Sessões
                </Button>
                <Button variant="outline" className="justify-start">
                  <User className="h-4 w-4 mr-2" />
                  Ver Clientes
                </Button>
                <Button variant="outline" className="justify-start">
                  <Clock className="h-4 w-4 mr-2" />
                  Histórico de Atividade
                </Button>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <Button variant="outline" onClick={onClose}>
              Fechar
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentViewModal;
