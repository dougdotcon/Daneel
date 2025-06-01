import React, { useState } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Filter, 
  MoreVertical, 
  Edit, 
  Trash2, 
  Copy,
  Users,
  MessageSquare,
  Settings,
  Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'draft';
  sessions: number;
  lastUsed: string;
  tags: string[];
  guidelines: number;
}

const AgentCard: React.FC<{ agent: Agent }> = ({ agent }) => {
  const navigate = useNavigate();
  
  const statusColors = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    draft: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
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
            <span className={cn(
              "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
              statusColors[agent.status]
            )}>
              {agent.status === 'active' ? 'Ativo' : agent.status === 'inactive' ? 'Inativo' : 'Rascunho'}
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
            {agent.sessions}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Sessões
          </div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {agent.guidelines}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Guidelines
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Último uso
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">
            {agent.lastUsed}
          </div>
        </div>
      </div>
      
      <div className="flex space-x-2">
        <Button 
          variant="outline" 
          size="sm" 
          className="flex-1"
          onClick={() => navigate(`/admin/agents/edit/${agent.id}`)}
        >
          <Edit className="h-4 w-4 mr-2" />
          Editar
        </Button>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => navigate(`/admin/agents/view/${agent.id}`)}
        >
          <Eye className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="sm">
          <Copy className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

const AgentsList: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const navigate = useNavigate();

  // Mock data - em produção viria da API
  const agents: Agent[] = [
    {
      id: '1',
      name: 'Assistente de Vendas',
      description: 'Agente especializado em vendas e atendimento ao cliente',
      status: 'active',
      sessions: 245,
      lastUsed: '2 horas atrás',
      tags: ['vendas', 'atendimento'],
      guidelines: 12
    },
    {
      id: '2',
      name: 'Suporte Técnico',
      description: 'Agente para resolver problemas técnicos e dúvidas',
      status: 'active',
      sessions: 189,
      lastUsed: '1 hora atrás',
      tags: ['suporte', 'técnico'],
      guidelines: 8
    },
    {
      id: '3',
      name: 'Agente de Marketing',
      description: 'Especialista em campanhas e estratégias de marketing',
      status: 'draft',
      sessions: 0,
      lastUsed: 'Nunca',
      tags: ['marketing'],
      guidelines: 5
    }
  ];

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

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
        <Button onClick={() => navigate('/admin/agents/create')}>
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
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="Filtrar por status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os status</SelectItem>
            <SelectItem value="active">Ativo</SelectItem>
            <SelectItem value="inactive">Inativo</SelectItem>
            <SelectItem value="draft">Rascunho</SelectItem>
          </SelectContent>
        </Select>
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
                {agents.filter(a => a.status === 'active').length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <MessageSquare className="h-5 w-5 text-green-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Sessões Hoje</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {agents.reduce((sum, agent) => sum + agent.sessions, 0)}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center">
            <Settings className="h-5 w-5 text-purple-500 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Guidelines</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {agents.reduce((sum, agent) => sum + agent.guidelines, 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {filteredAgents.length === 0 && (
        <div className="text-center py-12">
          <Users className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            Nenhum agente encontrado
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {searchTerm || statusFilter !== 'all' 
              ? 'Tente ajustar os filtros de busca.'
              : 'Comece criando seu primeiro agente.'}
          </p>
          {!searchTerm && statusFilter === 'all' && (
            <div className="mt-6">
              <Button onClick={() => navigate('/admin/agents/create')}>
                <Plus className="h-4 w-4 mr-2" />
                Criar Agente
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const CreateAgent: React.FC = () => {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Criar Novo Agente
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Funcionalidade em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const EditAgent: React.FC = () => {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Editar Agente
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Funcionalidade em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const ViewAgent: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Visualizar Agente
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Funcionalidade em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const AgentsManagement: React.FC = () => {
  return (
    <Routes>
      <Route index element={<AgentsList />} />
      <Route path="create" element={<CreateAgent />} />
      <Route path="edit/:id" element={<EditAgent />} />
      <Route path="view/:id" element={<ViewAgent />} />
    </Routes>
  );
};

export default AgentsManagement;
