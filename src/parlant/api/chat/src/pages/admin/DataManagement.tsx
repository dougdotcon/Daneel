import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Database, Download, Upload, Archive } from 'lucide-react';
import { cn } from '@/lib/utils';

const DataNav: React.FC = () => {
  const location = useLocation();
  
  const navItems = [
    { name: 'Backup', href: '/admin/data/backup', icon: Archive },
    { name: 'Importar', href: '/admin/data/import', icon: Upload },
    { name: 'Exportar', href: '/admin/data/export', icon: Download },
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

const BackupManagement: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Backup e Restore
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Faça backup e restore de dados e configurações
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de backup em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const ImportData: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Importar Dados
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Importe dados de outras instâncias ou sistemas
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de importação em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const ExportData: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Exportar Dados
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Exporte dados para backup ou migração
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de exportação em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const DataOverview: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Gerenciamento de Dados</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Gerencie backup, importação e exportação de dados
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/admin/data/backup">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <Archive className="h-8 w-8 text-blue-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Backup
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Faça backup automático ou manual de dados e configurações
            </p>
          </div>
        </Link>

        <Link to="/admin/data/import">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <Upload className="h-8 w-8 text-green-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Importar
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Importe dados de outras instâncias ou sistemas externos
            </p>
          </div>
        </Link>

        <Link to="/admin/data/export">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <Download className="h-8 w-8 text-purple-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Exportar
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Exporte dados para backup ou migração para outros sistemas
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
};

const DataManagement: React.FC = () => {
  const location = useLocation();
  const isOverview = location.pathname === '/admin/data';

  return (
    <div>
      {!isOverview && <DataNav />}
      <Routes>
        <Route index element={<DataOverview />} />
        <Route path="backup" element={<BackupManagement />} />
        <Route path="import" element={<ImportData />} />
        <Route path="export" element={<ExportData />} />
      </Routes>
    </div>
  );
};

export default DataManagement;
