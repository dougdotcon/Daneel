import React from 'react';
import { Settings as SettingsIcon, Palette, Globe, Bell } from 'lucide-react';

const Settings: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configurações da Interface</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Personalize a interface de administração
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Palette className="h-8 w-8 text-blue-500 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Tema
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Personalize a aparência da interface
          </p>
          <p className="text-xs text-gray-500">Em desenvolvimento...</p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Globe className="h-8 w-8 text-green-500 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Idioma
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure o idioma da interface
          </p>
          <p className="text-xs text-gray-500">Em desenvolvimento...</p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Bell className="h-8 w-8 text-yellow-500 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Notificações
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure alertas e notificações
          </p>
          <p className="text-xs text-gray-500">Em desenvolvimento...</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
