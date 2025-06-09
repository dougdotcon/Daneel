import React, { useState } from 'react';
import { 
  Save, 
  RefreshCw, 
  Server, 
  Shield, 
  Globe,
  Bell,
  Palette,
  Database,
  Loader2,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useToast, toast } from '@/components/ui/toast';

interface SystemSettings {
  server: {
    host: string;
    port: number;
    ssl: boolean;
    cors: boolean;
    maxConnections: number;
  };
  security: {
    authEnabled: boolean;
    sessionTimeout: number;
    maxLoginAttempts: number;
    requireHttps: boolean;
  };
  database: {
    host: string;
    port: number;
    name: string;
    maxConnections: number;
    timeout: number;
  };
  ui: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
    dateFormat: string;
  };
  notifications: {
    emailEnabled: boolean;
    webhookEnabled: boolean;
    logLevel: 'debug' | 'info' | 'warning' | 'error';
  };
}

const SystemSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings>({
    server: {
      host: '127.0.0.1',
      port: 8800,
      ssl: false,
      cors: true,
      maxConnections: 100
    },
    security: {
      authEnabled: false,
      sessionTimeout: 3600,
      maxLoginAttempts: 5,
      requireHttps: false
    },
    database: {
      host: 'localhost',
      port: 5432,
      name: 'Daneel',
      maxConnections: 20,
      timeout: 30
    },
    ui: {
      theme: 'auto',
      language: 'pt-BR',
      timezone: 'America/Sao_Paulo',
      dateFormat: 'DD/MM/YYYY'
    },
    notifications: {
      emailEnabled: false,
      webhookEnabled: false,
      logLevel: 'info'
    }
  });

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const { addToast } = useToast();

  const updateSetting = (section: keyof SystemSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      // Simular salvamento
      await new Promise(resolve => setTimeout(resolve, 2000));
      addToast(toast.success('Configurações salvas com sucesso!'));
    } catch (error) {
      addToast(toast.error('Erro ao salvar configurações'));
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async (type: 'database' | 'email' | 'webhook') => {
    setTesting(type);
    try {
      // Simular teste
      await new Promise(resolve => setTimeout(resolve, 3000));
      const success = Math.random() > 0.3; // 70% chance de sucesso
      
      if (success) {
        addToast(toast.success(`Teste de ${type} realizado com sucesso!`));
      } else {
        addToast(toast.error(`Falha no teste de ${type}`));
      }
    } catch (error) {
      addToast(toast.error(`Erro ao testar ${type}`));
    } finally {
      setTesting(null);
    }
  };

  const resetToDefaults = () => {
    if (window.confirm('Tem certeza que deseja restaurar as configurações padrão?')) {
      // Reset to default values
      setSettings({
        server: {
          host: '127.0.0.1',
          port: 8800,
          ssl: false,
          cors: true,
          maxConnections: 100
        },
        security: {
          authEnabled: false,
          sessionTimeout: 3600,
          maxLoginAttempts: 5,
          requireHttps: false
        },
        database: {
          host: 'localhost',
          port: 5432,
          name: 'Daneel',
          maxConnections: 20,
          timeout: 30
        },
        ui: {
          theme: 'auto',
          language: 'pt-BR',
          timezone: 'America/Sao_Paulo',
          dateFormat: 'DD/MM/YYYY'
        },
        notifications: {
          emailEnabled: false,
          webhookEnabled: false,
          logLevel: 'info'
        }
      });
      addToast(toast.info('Configurações restauradas para os valores padrão'));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configurações do Sistema</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Configure parâmetros globais do sistema
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={resetToDefaults}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Restaurar Padrões
          </Button>
          <Button onClick={saveSettings} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Salvar
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Server Settings */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Server className="h-5 w-5 text-blue-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configurações do Servidor
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="server-host">Host</Label>
            <Input
              id="server-host"
              value={settings.server.host}
              onChange={(e) => updateSetting('server', 'host', e.target.value)}
              placeholder="127.0.0.1"
            />
          </div>
          <div>
            <Label htmlFor="server-port">Porta</Label>
            <Input
              id="server-port"
              type="number"
              value={settings.server.port}
              onChange={(e) => updateSetting('server', 'port', parseInt(e.target.value))}
              placeholder="8800"
            />
          </div>
          <div>
            <Label htmlFor="max-connections">Máximo de Conexões</Label>
            <Input
              id="max-connections"
              type="number"
              value={settings.server.maxConnections}
              onChange={(e) => updateSetting('server', 'maxConnections', parseInt(e.target.value))}
              placeholder="100"
            />
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.server.ssl}
                onChange={(e) => updateSetting('server', 'ssl', e.target.checked)}
                className="mr-2"
              />
              SSL Habilitado
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.server.cors}
                onChange={(e) => updateSetting('server', 'cors', e.target.checked)}
                className="mr-2"
              />
              CORS Habilitado
            </label>
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Shield className="h-5 w-5 text-red-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configurações de Segurança
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="session-timeout">Timeout de Sessão (segundos)</Label>
            <Input
              id="session-timeout"
              type="number"
              value={settings.security.sessionTimeout}
              onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
              placeholder="3600"
            />
          </div>
          <div>
            <Label htmlFor="max-login-attempts">Máximo de Tentativas de Login</Label>
            <Input
              id="max-login-attempts"
              type="number"
              value={settings.security.maxLoginAttempts}
              onChange={(e) => updateSetting('security', 'maxLoginAttempts', parseInt(e.target.value))}
              placeholder="5"
            />
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.security.authEnabled}
                onChange={(e) => updateSetting('security', 'authEnabled', e.target.checked)}
                className="mr-2"
              />
              Autenticação Habilitada
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.security.requireHttps}
                onChange={(e) => updateSetting('security', 'requireHttps', e.target.checked)}
                className="mr-2"
              />
              Exigir HTTPS
            </label>
          </div>
        </div>
      </div>

      {/* Database Settings */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Database className="h-5 w-5 text-green-500 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Configurações do Banco de Dados
            </h3>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => testConnection('database')}
            disabled={testing === 'database'}
          >
            {testing === 'database' ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testando...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Testar Conexão
              </>
            )}
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="db-host">Host</Label>
            <Input
              id="db-host"
              value={settings.database.host}
              onChange={(e) => updateSetting('database', 'host', e.target.value)}
              placeholder="localhost"
            />
          </div>
          <div>
            <Label htmlFor="db-port">Porta</Label>
            <Input
              id="db-port"
              type="number"
              value={settings.database.port}
              onChange={(e) => updateSetting('database', 'port', parseInt(e.target.value))}
              placeholder="5432"
            />
          </div>
          <div>
            <Label htmlFor="db-name">Nome do Banco</Label>
            <Input
              id="db-name"
              value={settings.database.name}
              onChange={(e) => updateSetting('database', 'name', e.target.value)}
              placeholder="Daneel"
            />
          </div>
          <div>
            <Label htmlFor="db-timeout">Timeout (segundos)</Label>
            <Input
              id="db-timeout"
              type="number"
              value={settings.database.timeout}
              onChange={(e) => updateSetting('database', 'timeout', parseInt(e.target.value))}
              placeholder="30"
            />
          </div>
        </div>
      </div>

      {/* UI Settings */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Palette className="h-5 w-5 text-purple-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configurações da Interface
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="ui-theme">Tema</Label>
            <Select 
              value={settings.ui.theme} 
              onValueChange={(value) => updateSetting('ui', 'theme', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Claro</SelectItem>
                <SelectItem value="dark">Escuro</SelectItem>
                <SelectItem value="auto">Automático</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="ui-language">Idioma</Label>
            <Select 
              value={settings.ui.language} 
              onValueChange={(value) => updateSetting('ui', 'language', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pt-BR">Português (Brasil)</SelectItem>
                <SelectItem value="en-US">English (US)</SelectItem>
                <SelectItem value="es-ES">Español</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="ui-timezone">Fuso Horário</Label>
            <Select 
              value={settings.ui.timezone} 
              onValueChange={(value) => updateSetting('ui', 'timezone', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="America/Sao_Paulo">São Paulo (UTC-3)</SelectItem>
                <SelectItem value="America/New_York">New York (UTC-5)</SelectItem>
                <SelectItem value="Europe/London">London (UTC+0)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="ui-date-format">Formato de Data</Label>
            <Select 
              value={settings.ui.dateFormat} 
              onValueChange={(value) => updateSetting('ui', 'dateFormat', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Notifications Settings */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Bell className="h-5 w-5 text-yellow-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configurações de Notificações
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="log-level">Nível de Log</Label>
            <Select 
              value={settings.notifications.logLevel} 
              onValueChange={(value) => updateSetting('notifications', 'logLevel', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="debug">Debug</SelectItem>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.notifications.emailEnabled}
                onChange={(e) => updateSetting('notifications', 'emailEnabled', e.target.checked)}
                className="mr-2"
              />
              Email Habilitado
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.notifications.webhookEnabled}
                onChange={(e) => updateSetting('notifications', 'webhookEnabled', e.target.checked)}
                className="mr-2"
              />
              Webhook Habilitado
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettingsPage;
