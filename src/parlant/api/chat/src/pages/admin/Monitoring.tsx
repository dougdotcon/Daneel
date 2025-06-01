import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, FileText, AlertTriangle, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

const MonitoringNav: React.FC = () => {
  const location = useLocation();
  
  const navItems = [
    { name: 'Dashboard', href: '/admin/monitoring/dashboard', icon: BarChart3 },
    { name: 'Logs', href: '/admin/monitoring/logs', icon: FileText },
    { name: 'Alertas', href: '/admin/monitoring/alerts', icon: AlertTriangle },
  ];

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
      <nav className="-mb-px flex space-x-8">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;
          
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm",
                isActive
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
              )}
            >
              <Icon className="mr-2 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
};

const MonitoringDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Dashboard de Monitoramento
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Métricas e performance em tempo real
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Dashboard de monitoramento em desenvolvimento...
        </p>
        <div className="mt-4 space-y-2">
          <p className="text-sm text-gray-500">Funcionalidades planejadas:</p>
          <ul className="text-sm text-gray-500 list-disc list-inside space-y-1">
            <li>Gráficos de performance em tempo real</li>
            <li>Métricas de uso de tokens</li>
            <li>Monitoramento de sessões ativas</li>
            <li>Alertas de sistema</li>
            <li>Histórico de uptime</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

const LogsViewer: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Visualizador de Logs
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Logs do sistema em tempo real
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de logs em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const AlertsManagement: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Gerenciamento de Alertas
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Configure alertas e notificações
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de alertas em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const MonitoringOverview: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Monitoramento</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Monitore a performance e saúde do sistema
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/admin/monitoring/dashboard">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <BarChart3 className="h-8 w-8 text-blue-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Dashboard
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Métricas de performance e uso em tempo real
            </p>
          </div>
        </Link>

        <Link to="/admin/monitoring/logs">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <FileText className="h-8 w-8 text-green-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Logs
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Visualize e filtre logs do sistema em tempo real
            </p>
          </div>
        </Link>

        <Link to="/admin/monitoring/alerts">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <AlertTriangle className="h-8 w-8 text-red-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Alertas
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Configure alertas e notificações do sistema
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
};

const Monitoring: React.FC = () => {
  const location = useLocation();
  const isOverview = location.pathname === '/admin/monitoring';

  return (
    <div>
      {!isOverview && <MonitoringNav />}
      <Routes>
        <Route index element={<MonitoringOverview />} />
        <Route path="dashboard" element={<MonitoringDashboard />} />
        <Route path="logs" element={<LogsViewer />} />
        <Route path="alerts" element={<AlertsManagement />} />
      </Routes>
    </div>
  );
};

export default Monitoring;
