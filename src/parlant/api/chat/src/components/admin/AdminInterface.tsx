import React, { useState } from 'react';
import {
  LayoutDashboard,
  Settings,
  Users,
  Database,
  Activity,
  Wrench,
  LogOut,
  Menu,
  X,
  Plus,
  Search,
  MessageSquare,
  Clock,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Cpu,
  HardDrive,
  Wifi,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useSystemStats } from '@/hooks/useSystemStats';
import { useAgents } from '@/hooks/useAgents';
import { useSessions } from '@/hooks/useSessions';
import AgentsPage from './AgentsPage';
import LLMConfigPage from './LLMConfigPage';
import LogsPage from './LogsPage';
import BackupPage from './BackupPage';
import SystemSettingsPage from './SystemSettingsPage';
import AnalyticsPage from './AnalyticsPage';

interface AdminInterfaceProps {
  onNavigateToChat: () => void;
}

type AdminPage = 'dashboard' | 'setup' | 'agents' | 'configuration' | 'monitoring' | 'data' | 'settings' | 'analytics' | 'backup' | 'system-settings';

const AdminInterface: React.FC<AdminInterfaceProps> = ({ onNavigateToChat }) => {
  const [currentPage, setCurrentPage] = useState<AdminPage>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Hooks for real data
  const { status, stats, loading: systemLoading, formatUptime, getStatusColor, getUsageColor } = useSystemStats();
  const { agents, loading: agentsLoading } = useAgents();
  const { sessions, stats: sessionStats, loading: sessionsLoading } = useSessions();

  const navigation = [
    { name: 'Dashboard', page: 'dashboard' as AdminPage, icon: LayoutDashboard },
    { name: 'Analytics', page: 'analytics' as AdminPage, icon: TrendingUp },
    { name: 'Setup Wizard', page: 'setup' as AdminPage, icon: Wrench },
    { name: 'Agentes', page: 'agents' as AdminPage, icon: Users },
    { name: 'Configuração LLM', page: 'configuration' as AdminPage, icon: Settings },
    { name: 'Logs', page: 'monitoring' as AdminPage, icon: Activity },
    { name: 'Backup', page: 'backup' as AdminPage, icon: Database },
    { name: 'Sistema', page: 'system-settings' as AdminPage, icon: Settings },
  ];

  const renderSidebar = () => (
    <div className="flex flex-col flex-grow bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex h-16 items-center px-4 border-b border-gray-200 dark:border-gray-700">
        <img src="/chat/app-logo.svg" alt="Daneel" className="h-8 w-auto" />
        <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">Admin</span>
      </div>
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.name}
              onClick={() => {
                setCurrentPage(item.page);
                setSidebarOpen(false);
              }}
              className={cn(
                "w-full group flex items-center px-2 py-2 text-sm font-medium rounded-md",
                currentPage === item.page
                  ? "bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white"
              )}
            >
              <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
              {item.name}
            </button>
          );
        })}
      </nav>
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <button
          onClick={onNavigateToChat}
          className="w-full group flex items-center px-2 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white rounded-md"
        >
          <LogOut className="mr-3 h-5 w-5 flex-shrink-0" />
          Voltar ao Chat
        </button>
      </div>
    </div>
  );

  const renderDashboard = () => {
    const isLoading = systemLoading || agentsLoading || sessionsLoading;

    const dashboardStats = [
      {
        title: 'Agentes Ativos',
        value: stats?.active_agents?.toString() || '0',
        change: `${stats?.total_agents || 0} total`,
        icon: Users,
        loading: agentsLoading
      },
      {
        title: 'Sessões Hoje',
        value: sessionStats?.sessions_today?.toString() || '0',
        change: `${sessionStats?.total_sessions || 0} total`,
        icon: MessageSquare,
        loading: sessionsLoading
      },
      {
        title: 'Tempo de Resposta',
        value: stats?.average_response_time ? `${stats.average_response_time.toFixed(1)}s` : '0s',
        change: 'Média atual',
        icon: Clock,
        loading: systemLoading
      },
      {
        title: 'Taxa de Sucesso',
        value: stats?.success_rate ? `${stats.success_rate.toFixed(1)}%` : '0%',
        change: 'Últimas 24h',
        icon: TrendingUp,
        loading: systemLoading
      }
    ];

    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Visão geral do sistema Daneel
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {dashboardStats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {stat.loading ? (
                        <Loader2 className="h-6 w-6 text-gray-400 animate-spin" />
                      ) : (
                        <Icon className="h-6 w-6 text-gray-400" />
                      )}
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          {stat.title}
                        </dt>
                        <dd className="text-lg font-medium text-gray-900 dark:text-white">
                          {stat.loading ? '...' : stat.value}
                        </dd>
                      </dl>
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {stat.loading ? 'Carregando...' : stat.change}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* System Status */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Status do Sistema
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {systemLoading ? (
                <div className="col-span-full flex items-center justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                  <span className="ml-2 text-sm text-gray-500">Carregando status...</span>
                </div>
              ) : (
                [
                  {
                    name: 'API Server',
                    status: status?.api_server || 'offline',
                    icon: Wifi,
                    displayValue: status?.api_server || 'offline'
                  },
                  {
                    name: 'Database',
                    status: status?.database || 'offline',
                    icon: Database,
                    displayValue: status?.database || 'offline'
                  },
                  {
                    name: 'CPU Usage',
                    status: 'usage',
                    icon: Cpu,
                    displayValue: status?.cpu_usage ? `${status.cpu_usage}%` : '0%'
                  },
                  {
                    name: 'Storage',
                    status: 'usage',
                    icon: HardDrive,
                    displayValue: status?.storage_usage ? `${status.storage_usage}%` : '0%'
                  }
                ].map((item, index) => {
                  const Icon = item.icon;
                  const isOnline = item.status === 'online';
                  const isUsage = item.status === 'usage';
                  const statusColor = isUsage
                    ? getUsageColor(parseInt(item.displayValue) || 0)
                    : getStatusColor(item.status as any);

                  return (
                    <div key={index} className="flex items-center space-x-3">
                      <Icon className="h-5 w-5 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {item.name}
                        </p>
                        <div className="flex items-center space-x-2">
                          {isOnline ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : isUsage ? (
                            <div className="h-4 w-4 rounded-full bg-current opacity-60" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          )}
                          <span className={`text-sm ${statusColor}`}>
                            {item.displayValue}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Ações Rápidas
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { title: 'Configurar Novo Agente', description: 'Criar e configurar um novo agente AI', icon: Users, page: 'agents' as AdminPage },
              { title: 'Configurar LLM', description: 'Adicionar ou configurar provedores LLM', icon: Settings, page: 'configuration' as AdminPage },
              { title: 'Ver Logs', description: 'Monitorar logs do sistema em tempo real', icon: Activity, page: 'monitoring' as AdminPage },
              { title: 'Backup de Dados', description: 'Fazer backup das configurações e dados', icon: Database, page: 'backup' as AdminPage }
            ].map((action, index) => {
              const Icon = action.icon;
              return (
                <button
                  key={index}
                  onClick={() => setCurrentPage(action.page)}
                  className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow text-left"
                >
                  <div className="flex items-center mb-4">
                    <div className="flex-shrink-0 p-3 rounded-md bg-gray-100 dark:bg-gray-700">
                      <Icon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        {action.title}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {action.description}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderPlaceholderPage = (title: string, description: string) => (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Esta funcionalidade está em desenvolvimento...
        </p>
        <div className="mt-4">
          <Button onClick={() => setCurrentPage('dashboard')} variant="outline">
            Voltar ao Dashboard
          </Button>
        </div>
      </div>
    </div>
  );

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return renderDashboard();
      case 'analytics':
        return <AnalyticsPage />;
      case 'setup':
        return renderPlaceholderPage('Setup Wizard', 'Configure seu sistema Daneel');
      case 'agents':
        return <AgentsPage />;
      case 'configuration':
        return <LLMConfigPage />;
      case 'monitoring':
        return <LogsPage />;
      case 'backup':
        return <BackupPage />;
      case 'system-settings':
        return <SystemSettingsPage />;
      case 'data':
        return renderPlaceholderPage('Gerenciamento de Dados', 'Backup, importação e exportação');
      case 'settings':
        return renderPlaceholderPage('Configurações', 'Configurações da interface');
      default:
        return renderDashboard();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile sidebar */}
      <div className={cn(
        "fixed inset-0 z-50 lg:hidden",
        sidebarOpen ? "block" : "hidden"
      )}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white dark:bg-gray-800 shadow-xl">
          <div className="flex h-16 items-center justify-between px-4">
            <img src="/chat/app-logo.svg" alt="Daneel" className="h-8 w-auto" />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </Button>
          </div>
          {renderSidebar()}
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        {renderSidebar()}
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </Button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1 items-center">
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                Daneel - Painel de Administração
              </h1>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {renderCurrentPage()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminInterface;
