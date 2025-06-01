import React, { useState } from 'react';
import { 
  Users, 
  Plus, 
  Check, 
  X, 
  Loader2, 
  AlertCircle,
  Info,
  Star,
  Briefcase,
  HeadphonesIcon,
  TrendingUp,
  UserCheck,
  Scale,
  Calculator,
  Megaphone
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { defaultAgents, defaultTags, DefaultAgentConfig } from '@/data/defaultAgents';
import { useAgents, CreateAgentParams } from '@/hooks/useAgents';

interface AgentCreationStatus {
  agent: DefaultAgentConfig;
  status: 'pending' | 'creating' | 'success' | 'error';
  error?: string;
}

const getAgentIcon = (agentName: string) => {
  switch (agentName) {
    case 'Assistente Geral': return Star;
    case 'Suporte Técnico': return HeadphonesIcon;
    case 'Vendas': return TrendingUp;
    case 'Recursos Humanos': return UserCheck;
    case 'Atendimento ao Cliente': return Users;
    case 'Assistente Jurídico': return Scale;
    case 'Assistente Financeiro': return Calculator;
    case 'Assistente de Marketing': return Megaphone;
    default: return Briefcase;
  }
};

const DefaultAgentsSetup: React.FC = () => {
  const [agentStatuses, setAgentStatuses] = useState<AgentCreationStatus[]>(
    defaultAgents.map(agent => ({ agent, status: 'pending' }))
  );
  const [isCreatingAll, setIsCreatingAll] = useState(false);
  const [tagsCreated, setTagsCreated] = useState(false);
  const [isCreatingTags, setIsCreatingTags] = useState(false);

  const { createAgent } = useAgents();

  const createDefaultTags = async () => {
    setIsCreatingTags(true);
    let successCount = 0;

    for (const tag of defaultTags) {
      try {
        const response = await fetch('/tags', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: tag.name })
        });

        if (response.ok) {
          successCount++;
        }
      } catch (error) {
        console.error(`Error creating tag ${tag.name}:`, error);
      }
    }

    setTagsCreated(successCount > 0);
    setIsCreatingTags(false);
    return successCount;
  };

  const createSingleAgent = async (agentConfig: DefaultAgentConfig, index: number) => {
    setAgentStatuses(prev => prev.map((status, i) => 
      i === index ? { ...status, status: 'creating' } : status
    ));

    try {
      const agentData: CreateAgentParams = {
        name: agentConfig.name,
        description: agentConfig.description,
        tags: agentConfig.tags,
        composition_mode: agentConfig.composition_mode
      };

      const result = await createAgent(agentData);
      
      if (result) {
        setAgentStatuses(prev => prev.map((status, i) => 
          i === index ? { ...status, status: 'success' } : status
        ));
        return true;
      } else {
        throw new Error('Failed to create agent');
      }
    } catch (error) {
      setAgentStatuses(prev => prev.map((status, i) => 
        i === index ? { 
          ...status, 
          status: 'error', 
          error: error instanceof Error ? error.message : 'Unknown error'
        } : status
      ));
      return false;
    }
  };

  const createAllAgents = async () => {
    setIsCreatingAll(true);
    
    // First create tags if not already created
    if (!tagsCreated) {
      await createDefaultTags();
    }

    // Then create agents
    for (let i = 0; i < defaultAgents.length; i++) {
      await createSingleAgent(defaultAgents[i], i);
      // Small delay between creations to avoid overwhelming the API
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setIsCreatingAll(false);
  };

  const resetStatuses = () => {
    setAgentStatuses(defaultAgents.map(agent => ({ agent, status: 'pending' })));
  };

  const successCount = agentStatuses.filter(s => s.status === 'success').length;
  const errorCount = agentStatuses.filter(s => s.status === 'error').length;
  const pendingCount = agentStatuses.filter(s => s.status === 'pending').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
          <Users className="w-8 h-8 text-blue-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Agentes Pré-Prontos
          </h2>
          <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Crie agentes especializados para diferentes áreas do seu negócio. 
            Cada agente vem com configurações otimizadas para sua função específica.
          </p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{defaultAgents.length}</div>
          <div className="text-sm text-blue-700 dark:text-blue-300">Total</div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{successCount}</div>
          <div className="text-sm text-green-700 dark:text-green-300">Criados</div>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{errorCount}</div>
          <div className="text-sm text-red-700 dark:text-red-300">Erros</div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-600">{pendingCount}</div>
          <div className="text-sm text-gray-700 dark:text-gray-300">Pendentes</div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Button 
          onClick={createAllAgents}
          disabled={isCreatingAll || successCount === defaultAgents.length}
          className="flex items-center gap-2"
        >
          {isCreatingAll ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Criando Agentes...
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              Criar Todos os Agentes
            </>
          )}
        </Button>
        
        {(successCount > 0 || errorCount > 0) && (
          <Button variant="outline" onClick={resetStatuses}>
            Resetar Status
          </Button>
        )}
      </div>

      {/* Tags Status */}
      {!tagsCreated && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-900 dark:text-yellow-100">
                Tags Necessárias
              </h4>
              <p className="text-sm text-yellow-700 dark:text-yellow-200 mt-1">
                Primeiro criaremos {defaultTags.length} tags organizacionais para categorizar os agentes.
              </p>
              {isCreatingTags && (
                <div className="flex items-center gap-2 mt-2">
                  <Loader2 className="w-4 h-4 animate-spin text-yellow-600" />
                  <span className="text-sm text-yellow-700 dark:text-yellow-200">
                    Criando tags...
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Agents List */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Agentes Disponíveis
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agentStatuses.map((agentStatus, index) => {
            const { agent, status, error } = agentStatus;
            const Icon = getAgentIcon(agent.name);
            
            return (
              <div 
                key={agent.name}
                className={`border rounded-lg p-4 transition-colors ${
                  status === 'success' 
                    ? 'border-green-200 bg-green-50 dark:bg-green-900/20' 
                    : status === 'error'
                      ? 'border-red-200 bg-red-50 dark:bg-red-900/20'
                      : status === 'creating'
                        ? 'border-blue-200 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 bg-white dark:bg-gray-800'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    status === 'success' 
                      ? 'bg-green-100 text-green-600' 
                      : status === 'error'
                        ? 'bg-red-100 text-red-600'
                        : status === 'creating'
                          ? 'bg-blue-100 text-blue-600'
                          : 'bg-gray-100 text-gray-600'
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {agent.name}
                      </h4>
                      {status === 'success' && <Check className="w-4 h-4 text-green-600" />}
                      {status === 'error' && <X className="w-4 h-4 text-red-600" />}
                      {status === 'creating' && <Loader2 className="w-4 h-4 animate-spin text-blue-600" />}
                    </div>
                    
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {agent.description}
                    </p>
                    
                    <div className="flex flex-wrap gap-1 mb-2">
                      {agent.tags.slice(0, 3).map(tag => (
                        <span 
                          key={tag}
                          className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                      {agent.tags.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                          +{agent.tags.length - 3}
                        </span>
                      )}
                    </div>

                    {error && (
                      <div className="flex items-center gap-1 text-sm text-red-600">
                        <AlertCircle className="w-3 h-3" />
                        {error}
                      </div>
                    )}

                    {status === 'pending' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => createSingleAgent(agent, index)}
                        className="mt-2"
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        Criar Este Agente
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Success Message */}
      {successCount === defaultAgents.length && (
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-6 text-center">
          <Check className="w-12 h-12 text-green-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-green-900 dark:text-green-100 mb-2">
            Todos os Agentes Criados!
          </h3>
          <p className="text-green-700 dark:text-green-200">
            {successCount} agentes especializados foram criados com sucesso. 
            Agora você pode começar a usar o sistema com agentes pré-configurados.
          </p>
        </div>
      )}
    </div>
  );
};

export default DefaultAgentsSetup;
