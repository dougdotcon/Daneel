import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Activity, 
  Users, 
  MessageSquare, 
  Settings, 
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Database,
  Cpu,
  HardDrive,
  Wifi
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  href?: string;
}

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  change, 
  changeType = 'neutral', 
  icon: Icon,
  href 
}) => {
  const content = (
    <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                {title}
              </dt>
              <dd className="text-lg font-medium text-gray-900 dark:text-white">
                {value}
              </dd>
            </dl>
          </div>
        </div>
        {change && (
          <div className="mt-3">
            <span className={cn(
              "text-sm font-medium",
              changeType === 'positive' && "text-green-600 dark:text-green-400",
              changeType === 'negative' && "text-red-600 dark:text-red-400",
              changeType === 'neutral' && "text-gray-500 dark:text-gray-400"
            )}>
              {change}
            </span>
          </div>
        )}
      </div>
    </div>
  );

  if (href) {
    return <Link to={href}>{content}</Link>;
  }

  return content;
};

interface QuickActionProps {
  title: string;
  description: string;
  icon: React.ElementType;
  href: string;
  variant?: 'primary' | 'secondary';
}

const QuickAction: React.FC<QuickActionProps> = ({ 
  title, 
  description, 
  icon: Icon, 
  href,
  variant = 'secondary'
}) => (
  <Link to={href}>
    <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-center">
          <div className={cn(
            "flex-shrink-0 p-3 rounded-md",
            variant === 'primary' ? "bg-blue-500" : "bg-gray-100 dark:bg-gray-700"
          )}>
            <Icon className={cn(
              "h-6 w-6",
              variant === 'primary' ? "text-white" : "text-gray-600 dark:text-gray-300"
            )} />
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              {title}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {description}
            </p>
          </div>
        </div>
      </div>
    </div>
  </Link>
);

const Dashboard: React.FC = () => {
  // Mock data - em produção, estes dados viriam da API
  const stats = [
    {
      title: 'Agentes Ativos',
      value: '12',
      change: '+2 esta semana',
      changeType: 'positive' as const,
      icon: Users,
      href: '/admin/agents'
    },
    {
      title: 'Sessões Hoje',
      value: '847',
      change: '+12% vs ontem',
      changeType: 'positive' as const,
      icon: MessageSquare,
      href: '/admin/monitoring'
    },
    {
      title: 'Tempo de Resposta',
      value: '1.2s',
      change: '-0.3s vs média',
      changeType: 'positive' as const,
      icon: Clock,
      href: '/admin/monitoring'
    },
    {
      title: 'Taxa de Sucesso',
      value: '98.5%',
      change: '+0.2% esta semana',
      changeType: 'positive' as const,
      icon: TrendingUp,
      href: '/admin/monitoring'
    }
  ];

  const systemStatus = [
    { name: 'API Server', status: 'online', icon: Wifi },
    { name: 'Database', status: 'online', icon: Database },
    { name: 'CPU Usage', status: '45%', icon: Cpu },
    { name: 'Storage', status: '67%', icon: HardDrive }
  ];

  const quickActions = [
    {
      title: 'Configurar Novo Agente',
      description: 'Criar e configurar um novo agente AI',
      icon: Users,
      href: '/admin/agents/create',
      variant: 'primary' as const
    },
    {
      title: 'Configurar LLM',
      description: 'Adicionar ou configurar provedores LLM',
      icon: Settings,
      href: '/admin/configuration/llm'
    },
    {
      title: 'Ver Logs',
      description: 'Monitorar logs do sistema em tempo real',
      icon: Activity,
      href: '/admin/monitoring/logs'
    },
    {
      title: 'Backup de Dados',
      description: 'Fazer backup das configurações e dados',
      icon: Database,
      href: '/admin/data/backup'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Visão geral do sistema Daneel
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* System Status */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Status do Sistema
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {systemStatus.map((item, index) => {
              const Icon = item.icon;
              const isOnline = item.status === 'online';
              const isWarning = item.status.includes('%') && parseInt(item.status) > 80;
              
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
                      ) : isWarning ? (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                      <span className={cn(
                        "text-sm",
                        isOnline && "text-green-600 dark:text-green-400",
                        isWarning && "text-yellow-600 dark:text-yellow-400",
                        !isOnline && !isWarning && "text-red-600 dark:text-red-400"
                      )}>
                        {item.status}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Ações Rápidas
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action, index) => (
            <QuickAction key={index} {...action} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
