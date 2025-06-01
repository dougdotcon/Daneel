import { useState, useEffect } from 'react';
import { BASE_URL } from '@/utils/api';

export interface Session {
  id: string;
  title: string;
  creation_utc: string;
  agent_id: string;
  customer_id: string;
  metadata: Record<string, any>;
}

export interface SessionStats {
  total_sessions: number;
  active_sessions: number;
  sessions_today: number;
  average_response_time: number;
  success_rate: number;
}

export const useSessions = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BASE_URL}/sessions`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sessions');
      console.error('Error fetching sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionStats = async () => {
    setLoading(true);
    setError(null);
    try {
      // Mock stats for now - in production this would be a real endpoint
      const mockStats: SessionStats = {
        total_sessions: sessions.length,
        active_sessions: Math.floor(sessions.length * 0.1),
        sessions_today: Math.floor(Math.random() * 100) + 50,
        average_response_time: 1.2,
        success_rate: 98.5,
      };
      setStats(mockStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch session stats');
      console.error('Error fetching session stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSessionsByAgent = (agentId: string): Session[] => {
    return sessions.filter(session => session.agent_id === agentId);
  };

  const getSessionsToday = (): Session[] => {
    const today = new Date().toISOString().split('T')[0];
    return sessions.filter(session => 
      session.creation_utc.startsWith(today)
    );
  };

  const getRecentSessions = (limit: number = 10): Session[] => {
    return sessions
      .sort((a, b) => new Date(b.creation_utc).getTime() - new Date(a.creation_utc).getTime())
      .slice(0, limit);
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (sessions.length > 0) {
      fetchSessionStats();
    }
  }, [sessions]);

  return {
    sessions,
    stats,
    loading,
    error,
    fetchSessions,
    fetchSessionStats,
    getSessionsByAgent,
    getSessionsToday,
    getRecentSessions,
  };
};
