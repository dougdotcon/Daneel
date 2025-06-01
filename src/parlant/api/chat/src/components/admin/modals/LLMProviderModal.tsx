import React, { useState, useEffect } from 'react';
import { X, Loader2, Eye, EyeOff, TestTube } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface LLMProvider {
  id?: string;
  name: string;
  type: 'openai' | 'anthropic' | 'ollama' | 'custom';
  apiKey?: string;
  baseUrl?: string;
  model: string;
  status?: 'connected' | 'disconnected' | 'testing';
}

interface LLMProviderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (provider: LLMProvider) => Promise<boolean>;
  onTest?: (provider: LLMProvider) => Promise<boolean>;
  provider?: LLMProvider | null;
  mode: 'create' | 'edit';
}

const LLMProviderModal: React.FC<LLMProviderModalProps> = ({ 
  isOpen, 
  onClose, 
  onSave, 
  onTest,
  provider, 
  mode 
}) => {
  const [formData, setFormData] = useState<LLMProvider>({
    name: '',
    type: 'openai',
    apiKey: '',
    baseUrl: '',
    model: ''
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const providerTypes = [
    { value: 'openai', label: 'OpenAI', models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
    { value: 'anthropic', label: 'Anthropic', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'] },
    { value: 'ollama', label: 'Ollama', models: ['llama2', 'mistral', 'codellama'] },
    { value: 'custom', label: 'Personalizado', models: [] }
  ];

  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && provider) {
        setFormData({ ...provider });
      } else {
        setFormData({
          name: '',
          type: 'openai',
          apiKey: '',
          baseUrl: '',
          model: ''
        });
      }
      setErrors({});
      setShowApiKey(false);
    }
  }, [isOpen, mode, provider]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Nome é obrigatório';
    }

    if (!formData.model.trim()) {
      newErrors.model = 'Modelo é obrigatório';
    }

    if (formData.type !== 'ollama' && !formData.apiKey?.trim()) {
      newErrors.apiKey = 'API Key é obrigatória para este provedor';
    }

    if (formData.type === 'ollama' && !formData.baseUrl?.trim()) {
      newErrors.baseUrl = 'URL Base é obrigatória para Ollama';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      const success = await onSave(formData);
      if (success) {
        onClose();
      }
    } catch (error) {
      console.error('Error saving provider:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (!validateForm() || !onTest) return;

    setTesting(true);
    try {
      const success = await onTest(formData);
      // O resultado do teste será mostrado na UI principal
    } catch (error) {
      console.error('Error testing provider:', error);
    } finally {
      setTesting(false);
    }
  };

  const handleTypeChange = (type: string) => {
    const newFormData = { ...formData, type: type as LLMProvider['type'] };
    
    // Reset fields based on type
    if (type === 'ollama') {
      newFormData.apiKey = '';
      newFormData.baseUrl = formData.baseUrl || 'http://localhost:11434';
    } else {
      newFormData.baseUrl = '';
    }
    
    // Set default model
    const providerType = providerTypes.find(p => p.value === type);
    if (providerType && providerType.models.length > 0) {
      newFormData.model = providerType.models[0];
    } else {
      newFormData.model = '';
    }

    setFormData(newFormData);
  };

  const selectedProviderType = providerTypes.find(p => p.value === formData.type);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {mode === 'create' ? 'Adicionar Provedor LLM' : 'Editar Provedor LLM'}
            </h3>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              disabled={loading || testing}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Name */}
            <div>
              <Label htmlFor="provider-name">Nome do Provedor *</Label>
              <Input
                id="provider-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Ex: OpenAI GPT-4"
                className={cn(errors.name && "border-red-500")}
                disabled={loading || testing}
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name}</p>
              )}
            </div>

            {/* Type */}
            <div>
              <Label>Tipo de Provedor *</Label>
              <Select 
                value={formData.type} 
                onValueChange={handleTypeChange}
                disabled={loading || testing}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {providerTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* API Key (not for Ollama) */}
            {formData.type !== 'ollama' && (
              <div>
                <Label htmlFor="provider-apikey">API Key *</Label>
                <div className="relative">
                  <Input
                    id="provider-apikey"
                    type={showApiKey ? 'text' : 'password'}
                    value={formData.apiKey}
                    onChange={(e) => setFormData(prev => ({ ...prev, apiKey: e.target.value }))}
                    placeholder="sk-..."
                    className={cn(errors.apiKey && "border-red-500", "pr-10")}
                    disabled={loading || testing}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full"
                    onClick={() => setShowApiKey(!showApiKey)}
                    disabled={loading || testing}
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                {errors.apiKey && (
                  <p className="text-sm text-red-500 mt-1">{errors.apiKey}</p>
                )}
              </div>
            )}

            {/* Base URL (for Ollama and Custom) */}
            {(formData.type === 'ollama' || formData.type === 'custom') && (
              <div>
                <Label htmlFor="provider-baseurl">
                  URL Base {formData.type === 'ollama' ? '*' : ''}
                </Label>
                <Input
                  id="provider-baseurl"
                  value={formData.baseUrl}
                  onChange={(e) => setFormData(prev => ({ ...prev, baseUrl: e.target.value }))}
                  placeholder={formData.type === 'ollama' ? 'http://localhost:11434' : 'https://api.example.com'}
                  className={cn(errors.baseUrl && "border-red-500")}
                  disabled={loading || testing}
                />
                {errors.baseUrl && (
                  <p className="text-sm text-red-500 mt-1">{errors.baseUrl}</p>
                )}
              </div>
            )}

            {/* Model */}
            <div>
              <Label htmlFor="provider-model">Modelo *</Label>
              {selectedProviderType && selectedProviderType.models.length > 0 ? (
                <Select 
                  value={formData.model} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, model: value }))}
                  disabled={loading || testing}
                >
                  <SelectTrigger className={cn(errors.model && "border-red-500")}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedProviderType.models.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  id="provider-model"
                  value={formData.model}
                  onChange={(e) => setFormData(prev => ({ ...prev, model: e.target.value }))}
                  placeholder="Nome do modelo"
                  className={cn(errors.model && "border-red-500")}
                  disabled={loading || testing}
                />
              )}
              {errors.model && (
                <p className="text-sm text-red-500 mt-1">{errors.model}</p>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
            <div>
              {onTest && (
                <Button
                  variant="outline"
                  onClick={handleTest}
                  disabled={loading || testing}
                >
                  {testing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Testando...
                    </>
                  ) : (
                    <>
                      <TestTube className="h-4 w-4 mr-2" />
                      Testar
                    </>
                  )}
                </Button>
              )}
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={onClose}
                disabled={loading || testing}
              >
                Cancelar
              </Button>
              <Button
                onClick={handleSave}
                disabled={loading || testing}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {mode === 'create' ? 'Adicionando...' : 'Salvando...'}
                  </>
                ) : (
                  mode === 'create' ? 'Adicionar' : 'Salvar'
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMProviderModal;
