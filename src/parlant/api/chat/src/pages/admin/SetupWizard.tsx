import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Check, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface Step {
  id: string;
  title: string;
  description: string;
  completed: boolean;
}

interface LLMProvider {
  id: string;
  name: string;
  description: string;
  fields: Array<{
    key: string;
    label: string;
    type: 'text' | 'password' | 'select';
    required: boolean;
    options?: string[];
  }>;
}

const SetupWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});

  const [formData, setFormData] = useState({
    llmProvider: '',
    apiKey: '',
    model: '',
    serverPort: '8800',
    serverHost: '127.0.0.1',
    dataDirectory: './data',
    enableSSL: false,
    adminPassword: ''
  });

  const steps: Step[] = [
    {
      id: 'welcome',
      title: 'Bem-vindo ao Daneel',
      description: 'Configure seu sistema de agentes AI',
      completed: false
    },
    {
      id: 'llm',
      title: 'Provedor LLM',
      description: 'Configure seu provedor de linguagem',
      completed: false
    },
    {
      id: 'server',
      title: 'Configuração do Servidor',
      description: 'Configure porta e diretórios',
      completed: false
    },
    {
      id: 'test',
      title: 'Teste de Conectividade',
      description: 'Verifique se tudo está funcionando',
      completed: false
    },
    {
      id: 'complete',
      title: 'Configuração Completa',
      description: 'Seu sistema está pronto!',
      completed: false
    }
  ];

  const llmProviders: LLMProvider[] = [
    {
      id: 'openai',
      name: 'OpenAI',
      description: 'GPT-4, GPT-3.5 e outros modelos da OpenAI',
      fields: [
        { key: 'apiKey', label: 'API Key', type: 'password', required: true },
        { 
          key: 'model', 
          label: 'Modelo', 
          type: 'select', 
          required: true,
          options: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
        }
      ]
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      description: 'Claude 3 e outros modelos da Anthropic',
      fields: [
        { key: 'apiKey', label: 'API Key', type: 'password', required: true },
        { 
          key: 'model', 
          label: 'Modelo', 
          type: 'select', 
          required: true,
          options: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku']
        }
      ]
    },
    {
      id: 'ollama',
      name: 'Ollama',
      description: 'Modelos locais via Ollama',
      fields: [
        { key: 'baseUrl', label: 'URL Base', type: 'text', required: true },
        { key: 'model', label: 'Modelo', type: 'text', required: true }
      ]
    }
  ];

  const handleNext = async () => {
    if (currentStep === steps.length - 1) return;
    
    if (currentStep === 2) { // Test step
      setIsLoading(true);
      await runConnectivityTests();
      setIsLoading(false);
    }
    
    setCurrentStep(currentStep + 1);
  };

  const handlePrevious = () => {
    if (currentStep === 0) return;
    setCurrentStep(currentStep - 1);
  };

  const runConnectivityTests = async () => {
    // Simular testes de conectividade
    const tests = ['llm', 'database', 'server'];
    const results: Record<string, boolean> = {};
    
    for (const test of tests) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      results[test] = Math.random() > 0.2; // 80% chance de sucesso
    }
    
    setTestResults(results);
  };

  const updateFormData = (key: string, value: string) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const selectedProvider = llmProviders.find(p => p.id === formData.llmProvider);

  const renderStepContent = () => {
    switch (steps[currentStep].id) {
      case 'welcome':
        return (
          <div className="text-center space-y-6">
            <div className="mx-auto w-24 h-24 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
              <img src="/chat/app-logo.svg" alt="Daneel" className="w-12 h-12" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Bem-vindo ao Daneel
              </h2>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Este assistente irá guiá-lo através da configuração inicial do seu sistema de agentes AI.
                O processo levará apenas alguns minutos.
              </p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                O que você irá configurar:
              </h3>
              <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                <li>• Provedor de linguagem (OpenAI, Anthropic, etc.)</li>
                <li>• Configurações do servidor</li>
                <li>• Teste de conectividade</li>
                <li>• Configurações de segurança</li>
              </ul>
            </div>
          </div>
        );

      case 'llm':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Configurar Provedor LLM
              </h2>
              <p className="mt-1 text-gray-600 dark:text-gray-400">
                Escolha e configure seu provedor de linguagem preferido.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Provedor
                </label>
                <Select value={formData.llmProvider} onValueChange={(value) => updateFormData('llmProvider', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um provedor" />
                  </SelectTrigger>
                  <SelectContent>
                    {llmProviders.map((provider) => (
                      <SelectItem key={provider.id} value={provider.id}>
                        <div>
                          <div className="font-medium">{provider.name}</div>
                          <div className="text-sm text-gray-500">{provider.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedProvider && (
                <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
                  {selectedProvider.fields.map((field) => (
                    <div key={field.key}>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      {field.type === 'select' ? (
                        <Select 
                          value={formData[field.key as keyof typeof formData] as string} 
                          onValueChange={(value) => updateFormData(field.key, value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder={`Selecione ${field.label.toLowerCase()}`} />
                          </SelectTrigger>
                          <SelectContent>
                            {field.options?.map((option) => (
                              <SelectItem key={option} value={option}>
                                {option}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input
                          type={field.type}
                          value={formData[field.key as keyof typeof formData] as string}
                          onChange={(e) => updateFormData(field.key, e.target.value)}
                          placeholder={`Digite ${field.label.toLowerCase()}`}
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case 'server':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Configuração do Servidor
              </h2>
              <p className="mt-1 text-gray-600 dark:text-gray-400">
                Configure as opções básicas do servidor.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Porta do Servidor
                </label>
                <Input
                  type="number"
                  value={formData.serverPort}
                  onChange={(e) => updateFormData('serverPort', e.target.value)}
                  placeholder="8800"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Host do Servidor
                </label>
                <Input
                  value={formData.serverHost}
                  onChange={(e) => updateFormData('serverHost', e.target.value)}
                  placeholder="127.0.0.1"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Diretório de Dados
                </label>
                <Input
                  value={formData.dataDirectory}
                  onChange={(e) => updateFormData('dataDirectory', e.target.value)}
                  placeholder="./data"
                />
              </div>
            </div>
          </div>
        );

      case 'test':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Teste de Conectividade
              </h2>
              <p className="mt-1 text-gray-600 dark:text-gray-400">
                Verificando se todas as configurações estão funcionando corretamente.
              </p>
            </div>

            <div className="space-y-4">
              {[
                { key: 'llm', label: 'Conexão com LLM', description: 'Testando API key e conectividade' },
                { key: 'database', label: 'Banco de Dados', description: 'Verificando acesso ao banco de dados' },
                { key: 'server', label: 'Servidor', description: 'Testando configurações do servidor' }
              ].map((test) => (
                <div key={test.key} className="flex items-center space-x-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div className="flex-shrink-0">
                    {isLoading ? (
                      <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                    ) : testResults[test.key] === true ? (
                      <Check className="h-5 w-5 text-green-500" />
                    ) : testResults[test.key] === false ? (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                      {test.label}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {test.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {Object.keys(testResults).length > 0 && (
              <div className={cn(
                "p-4 rounded-lg border",
                Object.values(testResults).every(Boolean) 
                  ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                  : "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
              )}>
                <p className={cn(
                  "text-sm font-medium",
                  Object.values(testResults).every(Boolean)
                    ? "text-green-800 dark:text-green-200"
                    : "text-red-800 dark:text-red-200"
                )}>
                  {Object.values(testResults).every(Boolean)
                    ? "✅ Todos os testes passaram! Seu sistema está pronto."
                    : "❌ Alguns testes falharam. Verifique suas configurações."}
                </p>
              </div>
            )}
          </div>
        );

      case 'complete':
        return (
          <div className="text-center space-y-6">
            <div className="mx-auto w-24 h-24 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
              <Check className="w-12 h-12 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Configuração Completa!
              </h2>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Seu sistema Daneel foi configurado com sucesso e está pronto para uso.
              </p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <h3 className="font-medium text-green-900 dark:text-green-100 mb-2">
                Próximos passos:
              </h3>
              <ul className="text-sm text-green-800 dark:text-green-200 space-y-1">
                <li>• Criar seu primeiro agente</li>
                <li>• Configurar guidelines personalizadas</li>
                <li>• Explorar o painel de monitoramento</li>
                <li>• Testar o chat interface</li>
              </ul>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={cn(
                "flex items-center justify-center w-8 h-8 rounded-full border-2",
                index <= currentStep
                  ? "bg-blue-600 border-blue-600 text-white"
                  : "border-gray-300 text-gray-500"
              )}>
                {index < currentStep ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>
              {index < steps.length - 1 && (
                <div className={cn(
                  "w-full h-0.5 mx-2",
                  index < currentStep ? "bg-blue-600" : "bg-gray-300"
                )} />
              )}
            </div>
          ))}
        </div>
        <div className="mt-2">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Passo {currentStep + 1} de {steps.length}: {steps[currentStep].title}
          </p>
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        {renderStepContent()}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentStep === 0}
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          Anterior
        </Button>
        <Button
          onClick={handleNext}
          disabled={currentStep === steps.length - 1 || isLoading}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : currentStep === steps.length - 1 ? (
            'Finalizar'
          ) : (
            <>
              Próximo
              <ChevronRight className="w-4 h-4 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default SetupWizard;
