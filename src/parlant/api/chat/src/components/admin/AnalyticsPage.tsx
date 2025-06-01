import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  MessageSquare, 
  Clock, 
  Target,
  Calendar,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface MetricCard {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
}

interface ChartData {
  label: string;
  value: number;
  color: string;
}

const AnalyticsPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState('7d');
  const [refreshing, setRefreshing] = useState(false);

  // Mock data - em produção viria da API
  const metrics: MetricCard[] = [
    {
      title: 'Total de Sessões',
      value: '2,847',
      change: '+12.5%',
      changeType: 'positive',
      icon: MessageSquare
    },
    {
      title: 'Usuários Únicos',
      value: '1,234',
      change: '+8.2%',
      changeType: 'positive',
      icon: Users
    },
    {
      title: 'Tempo Médio de Resposta',
      value: '1.2s',
      change: '-0.3s',
      changeType: 'positive',
      icon: Clock
    },
    {
      title: 'Taxa de Sucesso',
      value: '98.5%',
      change: '+0.8%',
      changeType: 'positive',
      icon: Target
    }
  ];

  const agentUsage: ChartData[] = [
    { label: 'Assistente de Vendas', value: 45, color: '#3B82F6' },
    { label: 'Suporte Técnico', value: 30, color: '#10B981' },
    { label: 'Agente de Marketing', value: 15, color: '#F59E0B' },
    { label: 'Outros', value: 10, color: '#6B7280' }
  ];

  const hourlyActivity = [
    { hour: '00', sessions: 12 },
    { hour: '01', sessions: 8 },
    { hour: '02', sessions: 5 },
    { hour: '03', sessions: 3 },
    { hour: '04', sessions: 2 },
    { hour: '05', sessions: 4 },
    { hour: '06', sessions: 15 },
    { hour: '07', sessions: 28 },
    { hour: '08', sessions: 45 },
    { hour: '09', sessions: 67 },
    { hour: '10', sessions: 89 },
    { hour: '11', sessions: 95 },
    { hour: '12', sessions: 78 },
    { hour: '13', sessions: 82 },
    { hour: '14', sessions: 91 },
    { hour: '15', sessions: 88 },
    { hour: '16', sessions: 76 },
    { hour: '17', sessions: 65 },
    { hour: '18', sessions: 45 },
    { hour: '19', sessions: 32 },
    { hour: '20', sessions: 25 },
    { hour: '21', sessions: 18 },
    { hour: '22', sessions: 15 },
    { hour: '23', sessions: 10 }
  ];

  const refreshData = async () => {
    setRefreshing(true);
    // Simular carregamento
    await new Promise(resolve => setTimeout(resolve, 1500));
    setRefreshing(false);
  };

  const exportData = () => {
    // Simular exportação
    const data = {
      timeRange,
      metrics,
      agentUsage,
      hourlyActivity,
      exportedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getChangeIcon = (changeType: MetricCard['changeType']) => {
    switch (changeType) {
      case 'positive':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'negative':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getChangeColor = (changeType: MetricCard['changeType']) => {
    switch (changeType) {
      case 'positive':
        return 'text-green-600 dark:text-green-400';
      case 'negative':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const maxActivity = Math.max(...hourlyActivity.map(h => h.sessions));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Métricas e análises de uso do sistema
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">Hoje</SelectItem>
              <SelectItem value="7d">7 dias</SelectItem>
              <SelectItem value="30d">30 dias</SelectItem>
              <SelectItem value="90d">90 dias</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={refreshData} disabled={refreshing}>
            <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
            Atualizar
          </Button>
          <Button variant="outline" size="sm" onClick={exportData}>
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <div key={index} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {metric.value}
                  </p>
                  <div className="flex items-center mt-1">
                    {getChangeIcon(metric.changeType)}
                    <span className={cn("text-sm font-medium ml-1", getChangeColor(metric.changeType))}>
                      {metric.change}
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-full">
                  <Icon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Usage Chart */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Uso por Agente
          </h3>
          <div className="space-y-4">
            {agentUsage.map((item, index) => (
              <div key={index} className="flex items-center">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {item.label}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {item.value}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${item.value}%`,
                        backgroundColor: item.color
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Hourly Activity Chart */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Atividade por Hora
          </h3>
          <div className="flex items-end space-x-1 h-48">
            {hourlyActivity.map((item, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-blue-500 rounded-t"
                  style={{
                    height: `${(item.sessions / maxActivity) * 100}%`,
                    minHeight: '2px'
                  }}
                />
                <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {item.hour}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Estatísticas Detalhadas
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Performance
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Tempo médio de resposta</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">1.2s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">P95 tempo de resposta</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">2.8s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Uptime</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">99.9%</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Uso de Recursos
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">CPU médio</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">45%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Memória média</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">67%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Tokens processados</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">1.2M</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Qualidade
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Taxa de sucesso</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">98.5%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Satisfação do usuário</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">4.7/5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Erros por hora</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">0.3</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
