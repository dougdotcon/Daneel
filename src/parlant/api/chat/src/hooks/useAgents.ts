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

  const fetchAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BASE_URL}/agents`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agents');
      console.error('Error fetching agents:', err);
    } finally {
      setLoading(false);
    }
  };

  const createAgent = async (params: CreateAgentParams): Promise<Agent | null> => {
    setLoading(true);
    setError(null);
    try {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
      console.error('Error creating agent:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const updateAgent = async (id: string, params: UpdateAgentParams): Promise<Agent | null> => {
    setLoading(true);
    setError(null);
    try {
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update agent');
      console.error('Error updating agent:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const deleteAgent = async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BASE_URL}/agents/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setAgents(prev => prev.filter(agent => agent.id !== id));
      addToast(toast.success('Agente excluído com sucesso!'));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete agent');
      console.error('Error deleting agent:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const getAgent = async (id: string): Promise<Agent | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BASE_URL}/agents/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const agent = await response.json();
      return agent;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent');
      console.error('Error fetching agent:', err);
      return null;
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
