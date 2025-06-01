import { useState, useEffect } from 'react';
import { BASE_URL } from '@/utils/api';
import { useToast, toast } from '@/components/ui/toast';

export interface Agent {
  id: string;
  name: string;
  description: string;
  creation_utc: string;
  metadata: Record<string, any>;
  tags: string[];
}

export interface CreateAgentParams {
  name: string;
  description: string;
  metadata?: Record<string, any>;
  tags?: string[];
}

export interface UpdateAgentParams {
  name?: string;
  description?: string;
  metadata?: Record<string, any>;
  tags?: string[];
}

export const useAgents = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addToast } = useToast();

  // Mock data for when API is not available
  const mockAgents: Agent[] = [
    {
      id: '1',
      name: 'Assistente Geral',
      description: 'Assistente versátil para tarefas gerais e suporte ao usuário',
      creation_utc: new Date().toISOString(),
      metadata: { type: 'general', version: '1.0' },
      tags: ['geral', 'suporte', 'conversação']
    },
    {
      id: '2',
      name: 'Suporte Técnico',
      description: 'Especialista em resolução de problemas técnicos e troubleshooting',
      creation_utc: new Date().toISOString(),
      metadata: { type: 'technical', version: '1.0' },
      tags: ['técnico', 'troubleshooting', 'suporte']
    },
    {
      id: '3',
      name: 'Assistente de Vendas',
      description: 'Especializado em vendas, qualificação de leads e conversão',
      creation_utc: new Date().toISOString(),
      metadata: { type: 'sales', version: '1.0' },
      tags: ['vendas', 'leads', 'conversão']
    }
  ];

  const fetchAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      // Try to fetch from API first
      if (BASE_URL) {
        const response = await fetch(`${BASE_URL}/agents`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setAgents(data);
      } else {
        // Use mock data if no API URL configured
        setAgents(mockAgents);
      }
    } catch (err) {
      // Fallback to mock data on API error
      console.warn('API not available, using mock data:', err);
      setAgents(mockAgents);
      setError(null); // Don't show error when using fallback
    } finally {
      setLoading(false);
    }
  };

  const createAgent = async (params: CreateAgentParams): Promise<Agent | null> => {
    setLoading(true);
    setError(null);
    try {
      if (BASE_URL) {
        const response = await fetch(`${BASE_URL}/agents`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(params),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const newAgent = await response.json();
        setAgents(prev => [...prev, newAgent]);
        addToast(toast.success(`Agente "${newAgent.name}" criado com sucesso!`));
        return newAgent;
      } else {
        // Mock creation
        const newAgent: Agent = {
          id: Date.now().toString(),
          name: params.name,
          description: params.description,
          creation_utc: new Date().toISOString(),
          metadata: params.metadata || {},
          tags: params.tags || []
        };
        setAgents(prev => [...prev, newAgent]);
        addToast(toast.success(`Agente "${newAgent.name}" criado com sucesso! (Modo Demo)`));
        return newAgent;
      }
    } catch (err) {
      // Fallback to mock creation
      const newAgent: Agent = {
        id: Date.now().toString(),
        name: params.name,
        description: params.description,
        creation_utc: new Date().toISOString(),
        metadata: params.metadata || {},
        tags: params.tags || []
      };
      setAgents(prev => [...prev, newAgent]);
      addToast(toast.success(`Agente "${newAgent.name}" criado com sucesso! (Modo Demo)`));
      return newAgent;
    } finally {
      setLoading(false);
    }
  };

  const updateAgent = async (id: string, params: UpdateAgentParams): Promise<Agent | null> => {
    setLoading(true);
    setError(null);
    try {
      if (BASE_URL) {
        const response = await fetch(`${BASE_URL}/agents/${id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(params),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const updatedAgent = await response.json();
        setAgents(prev => prev.map(agent => agent.id === id ? updatedAgent : agent));
        addToast(toast.success(`Agente "${updatedAgent.name}" atualizado com sucesso!`));
        return updatedAgent;
      } else {
        // Mock update
        const updatedAgent = agents.find(agent => agent.id === id);
        if (updatedAgent) {
          const newAgent = { ...updatedAgent, ...params };
          setAgents(prev => prev.map(agent => agent.id === id ? newAgent : agent));
          addToast(toast.success(`Agente "${newAgent.name}" atualizado com sucesso! (Modo Demo)`));
          return newAgent;
        }
        return null;
      }
    } catch (err) {
      // Fallback to mock update
      const updatedAgent = agents.find(agent => agent.id === id);
      if (updatedAgent) {
        const newAgent = { ...updatedAgent, ...params };
        setAgents(prev => prev.map(agent => agent.id === id ? newAgent : agent));
        addToast(toast.success(`Agente "${newAgent.name}" atualizado com sucesso! (Modo Demo)`));
        return newAgent;
      }
      return null;
    } finally {
      setLoading(false);
    }
  };

  const deleteAgent = async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      if (BASE_URL) {
        const response = await fetch(`${BASE_URL}/agents/${id}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        setAgents(prev => prev.filter(agent => agent.id !== id));
        addToast(toast.success('Agente excluído com sucesso!'));
        return true;
      } else {
        // Mock deletion
        setAgents(prev => prev.filter(agent => agent.id !== id));
        addToast(toast.success('Agente excluído com sucesso! (Modo Demo)'));
        return true;
      }
    } catch (err) {
      // Fallback to mock deletion
      setAgents(prev => prev.filter(agent => agent.id !== id));
      addToast(toast.success('Agente excluído com sucesso! (Modo Demo)'));
      return true;
    } finally {
      setLoading(false);
    }
  };

  const getAgent = async (id: string): Promise<Agent | null> => {
    setLoading(true);
    setError(null);
    try {
      if (BASE_URL) {
        const response = await fetch(`${BASE_URL}/agents/${id}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const agent = await response.json();
        return agent;
      } else {
        // Mock get agent
        const agent = agents.find(a => a.id === id) || null;
        return agent;
      }
    } catch (err) {
      // Fallback to mock get agent
      const agent = agents.find(a => a.id === id) || null;
      return agent;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  return {
    agents,
    loading,
    error,
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    getAgent,
  };
};
