import React, { useState } from 'react';
import { 
  Settings, 
  Palette, 
  Monitor, 
  Moon, 
  Sun, 
  Globe, 
  Bell, 
  Volume2, 
  VolumeX,
  Save,
  RotateCcw,
  Loader2,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface InterfaceSettings {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: boolean;
  sounds: boolean;
  autoSave: boolean;
  compactMode: boolean;
  animationsEnabled: boolean;
  fontSize: 'small' | 'medium' | 'large';
  sidebarCollapsed: boolean;
  showTooltips: boolean;
}

const InterfaceSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<InterfaceSettings>({
    theme: 'auto',
    language: 'pt-BR',
    notifications: true,
    sounds: true,
    autoSave: true,
    compactMode: false,
    animationsEnabled: true,
    fontSize: 'medium',
    sidebarCollapsed: false,
    showTooltips: true
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSettingChange = (key: keyof InterfaceSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Save to localStorage for demo
    localStorage.setItem('daneel-interface-settings', JSON.stringify(settings));
    
    setSaving(false);
    setSaved(true);
    
    // Reset saved status after 3 seconds
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setSettings({
      theme: 'auto',
      language: 'pt-BR',
      notifications: true,
      sounds: true,
      autoSave: true,
      compactMode: false,
      animationsEnabled: true,
      fontSize: 'medium',
      sidebarCollapsed: false,
      showTooltips: true
    });
    setSaved(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configurações da Interface</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Personalize a aparência e comportamento da interface do Daneel
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Restaurar Padrões
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : saved ? (
              <CheckCircle className="h-4 w-4 mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {saved ? 'Salvo!' : 'Salvar Configurações'}
          </Button>
        </div>
      </div>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Appearance */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Palette className="h-5 w-5 text-blue-500" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Aparência</h3>
          </div>
          
          <div className="space-y-4">
            {/* Theme */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tema
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'light', label: 'Claro', icon: Sun },
                  { value: 'dark', label: 'Escuro', icon: Moon },
                  { value: 'auto', label: 'Auto', icon: Monitor }
                ].map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => handleSettingChange('theme', value)}
                    className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                      settings.theme === value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-4 w-4 mx-auto mb-1" />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Font Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tamanho da Fonte
              </label>
              <select
                value={settings.fontSize}
                onChange={(e) => handleSettingChange('fontSize', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md bg-white text-gray-900"
              >
                <option value="small">Pequena</option>
                <option value="medium">Média</option>
                <option value="large">Grande</option>
              </select>
            </div>

            {/* Compact Mode */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Modo Compacto
                </label>
                <p className="text-xs text-gray-500">Reduz espaçamentos na interface</p>
              </div>
              <button
                onClick={() => handleSettingChange('compactMode', !settings.compactMode)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.compactMode ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.compactMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Behavior */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Settings className="h-5 w-5 text-green-500" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Comportamento</h3>
          </div>
          
          <div className="space-y-4">
            {/* Language */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Globe className="h-4 w-4 inline mr-1" />
                Idioma
              </label>
              <select
                value={settings.language}
                onChange={(e) => handleSettingChange('language', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md bg-white text-gray-900"
              >
                <option value="pt-BR">Português (Brasil)</option>
                <option value="en-US">English (US)</option>
                <option value="es-ES">Español</option>
                <option value="fr-FR">Français</option>
              </select>
            </div>

            {/* Auto Save */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Salvamento Automático
                </label>
                <p className="text-xs text-gray-500">Salva alterações automaticamente</p>
              </div>
              <button
                onClick={() => handleSettingChange('autoSave', !settings.autoSave)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.autoSave ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.autoSave ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Animations */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Animações
                </label>
                <p className="text-xs text-gray-500">Habilita transições e animações</p>
              </div>
              <button
                onClick={() => handleSettingChange('animationsEnabled', !settings.animationsEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.animationsEnabled ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.animationsEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Tooltips */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Dicas de Ferramenta
                </label>
                <p className="text-xs text-gray-500">Mostra tooltips explicativos</p>
              </div>
              <button
                onClick={() => handleSettingChange('showTooltips', !settings.showTooltips)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.showTooltips ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.showTooltips ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bell className="h-5 w-5 text-yellow-500" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Notificações</h3>
          </div>
          
          <div className="space-y-4">
            {/* Notifications */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Notificações do Sistema
                </label>
                <p className="text-xs text-gray-500">Receber alertas e notificações</p>
              </div>
              <button
                onClick={() => handleSettingChange('notifications', !settings.notifications)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.notifications ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.notifications ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Sounds */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1">
                  {settings.sounds ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                  Sons do Sistema
                </label>
                <p className="text-xs text-gray-500">Sons para notificações e ações</p>
              </div>
              <button
                onClick={() => handleSettingChange('sounds', !settings.sounds)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.sounds ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.sounds ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Layout */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Monitor className="h-5 w-5 text-purple-500" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Layout</h3>
          </div>
          
          <div className="space-y-4">
            {/* Sidebar */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Sidebar Recolhida
                </label>
                <p className="text-xs text-gray-500">Inicia com sidebar minimizada</p>
              </div>
              <button
                onClick={() => handleSettingChange('sidebarCollapsed', !settings.sidebarCollapsed)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.sidebarCollapsed ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.sidebarCollapsed ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Save Status */}
      {saved && (
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span className="text-green-800 dark:text-green-200 font-medium">
              Configurações salvas com sucesso!
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterfaceSettingsPage;
