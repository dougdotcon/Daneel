import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Settings, Cpu, Shield, Server } from 'lucide-react';
import { cn } from '@/lib/utils';

const ConfigurationNav: React.FC = () => {
  const location = useLocation();
  
  const navItems = [
    { name: 'LLM Providers', href: '/admin/configuration/llm', icon: Cpu },
    { name: 'Servidor', href: '/admin/configuration/server', icon: Server },
    { name: 'Segurança', href: '/admin/configuration/security', icon: Shield },
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

const LLMConfiguration: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Configuração de Provedores LLM
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Configure e gerencie seus provedores de linguagem
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de configuração de LLM em desenvolvimento...
        </p>
        <div className="mt-4 space-y-2">
          <p className="text-sm text-gray-500">Funcionalidades planejadas:</p>
          <ul className="text-sm text-gray-500 list-disc list-inside space-y-1">
            <li>Configuração de OpenAI, Anthropic, Ollama</li>
            <li>Gerenciamento seguro de API keys</li>
            <li>Teste de conectividade em tempo real</li>
            <li>Configuração de modelos e parâmetros</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

const ServerConfiguration: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Configuração do Servidor
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Configure porta, host e outras opções do servidor
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de configuração do servidor em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const SecurityConfiguration: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Configuração de Segurança
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Configure autenticação, autorização e outras opções de segurança
        </p>
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <p className="text-gray-600 dark:text-gray-400">
          Interface de configuração de segurança em desenvolvimento...
        </p>
      </div>
    </div>
  );
};

const ConfigurationOverview: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configuração</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Configure todos os aspectos do sistema Daneel
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/admin/configuration/llm">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <Cpu className="h-8 w-8 text-blue-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Provedores LLM
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Configure OpenAI, Anthropic, Ollama e outros provedores de linguagem
            </p>
          </div>
        </Link>

        <Link to="/admin/configuration/server">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <Server className="h-8 w-8 text-green-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Servidor
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Configure porta, host, SSL e outras opções do servidor
            </p>
          </div>
        </Link>

        <Link to="/admin/configuration/security">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-4">
              <Shield className="h-8 w-8 text-red-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Segurança
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Configure autenticação, autorização e políticas de segurança
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
};

const Configuration: React.FC = () => {
  const location = useLocation();
  const isOverview = location.pathname === '/admin/configuration';

  return (
    <div>
      {!isOverview && <ConfigurationNav />}
      <Routes>
        <Route index element={<ConfigurationOverview />} />
        <Route path="llm" element={<LLMConfiguration />} />
        <Route path="server" element={<ServerConfiguration />} />
        <Route path="security" element={<SecurityConfiguration />} />
      </Routes>
    </div>
  );
};

export default Configuration;
