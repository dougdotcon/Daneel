import React, { useState } from 'react';
import {
  Plus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  Copy,
  Users,
  MessageSquare,
  Settings,
  Eye,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useAgents, Agent, CreateAgentParams, UpdateAgentParams } from '@/hooks/useAgents';
import { useSessions } from '@/hooks/useSessions';
import AgentModal from './modals/AgentModal';
import AgentViewModal from './modals/AgentViewModal';

interface AgentCardProps {
  agent: Agent;
  sessionCount: number;
  onEdit: (agent: Agent) => void;
  onDelete: (agent: Agent) => void;
  onView: (agent: Agent) => void;
}

const AgentCard: React.FC<AgentCardProps> = ({ agent, sessionCount, onEdit, onDelete, onView }) => {
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR');
    } catch {
      return 'Data inválida';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            {agent.name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            {agent.description}
          </p>
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              Ativo
            </span>
            {agent.tags.map((tag) => (
              <span key={tag} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="icon">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {sessionCount}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Sessões
          </div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {agent.tags.length}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Tags
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Criado em
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">
            {formatDate(agent.creation_utc)}
          </div>
        </div>
      </div>

      <div className="flex space-x-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={() => onEdit(agent)}
        >
          <Edit className="h-4 w-4 mr-2" />
          Editar
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onView(agent)}
        >
          <Eye className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDelete(agent)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

const AgentsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [viewAgent, setViewAgent] = useState<Agent | null>(null);

  const { agents, loading, error, createAgent, updateAgent, deleteAgent } = useAgents();
  const { sessions } = useSessions();

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const getSessionCount = (agentId: string): number => {
    return sessions.filter(session => session.agent_id === agentId).length;
  };

  const handleEdit = (agent: Agent) => {
    setSelectedAgent(agent);
    setModalMode('edit');
    setModalOpen(true);
  };

  const handleDelete = async (agent: Agent) => {
    if (window.confirm(`Tem certeza que deseja excluir o agente "${agent.name}"?`)) {
      const success = await deleteAgent(agent.id);
      if (success) {
        // Sucesso - o hook já atualizou a lista
      } else {
        // Erro já foi tratado no hook
      }
    }
  };

  const handleView = (agent: Agent) => {
    setViewAgent(agent);
    setViewModalOpen(true);
  };

  const handleCreateAgent = () => {
    setSelectedAgent(null);
    setModalMode('create');
    setModalOpen(true);
  };

  const handleModalSave = async (params: CreateAgentParams | UpdateAgentParams): Promise<boolean> => {
    if (modalMode === 'create') {
      const result = await createAgent(params as CreateAgentParams);
      return result !== null;
    } else if (selectedAgent) {
      const result = await updateAgent(selectedAgent.id, params as UpdateAgentParams);
      return result !== null;
    }
    return false;
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedAgent(null);
  };

  if (loading && agents.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">Carregando agentes...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12">
          <AlertCircle className="h-8 w-8 text-red-400" />
          <span className="ml-2 text-red-500">Erro ao carregar agentes: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agentes</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Gerencie seus agentes AI e suas configurações
          </p>
        </div>
        <Button onClick={handleCreateAgent}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Agente
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Buscar agentes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-full sm:w-48 h-10 px-3 py-2 border border-gray-300 rounded-md bg-white text-sm"
        >
          <option value="all">Todos os status</option>
          <option value="active">Ativo</option>
          <option value="inactive">Inativo</option>
          <option value="draft">Rascunho</option>
        </select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <Users className="h-5 w-5 text-blue-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{agents.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Ativos</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {agents.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <MessageSquare className="h-5 w-5 text-green-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Sessões Total</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {sessions.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <Settings className="h-5 w-5 text-purple-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Tags Únicas</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {new Set(agents.flatMap(agent => agent.tags)).size}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            sessionCount={getSessionCount(agent.id)}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onView={handleView}
          />
        ))}
      </div>

      {filteredAgents.length === 0 && !loading && (
        <div className="text-center py-12">
          <Users className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            Nenhum agente encontrado
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {searchTerm
              ? 'Tente ajustar os filtros de busca.'
              : 'Comece criando seu primeiro agente.'}
          </p>
          {!searchTerm && (
            <div className="mt-6">
              <Button onClick={handleCreateAgent}>
                <Plus className="h-4 w-4 mr-2" />
                Criar Agente
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Agent Modal */}
      <AgentModal
        isOpen={modalOpen}
        onClose={handleModalClose}
        onSave={handleModalSave}
        agent={selectedAgent}
        mode={modalMode}
      />

      {/* Agent View Modal */}
      <AgentViewModal
        isOpen={viewModalOpen}
        onClose={() => setViewModalOpen(false)}
        agent={viewAgent}
        sessionCount={viewAgent ? getSessionCount(viewAgent.id) : 0}
      />
    </div>
  );
};

export default AgentsPage;
