import React, { useState } from 'react';
import { 
  CheckCircle, 
  Circle, 
  Users, 
  BookOpen, 
  Tag, 
  MessageSquare,
  Loader2,
  AlertCircle,
  Wand2,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAgents, CreateAgentParams } from '@/hooks/useAgents';
import DefaultAgentsSetup from './DefaultAgentsSetup';

interface SetupStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  icon: React.ComponentType<any>;
}

const defaultAgents: CreateAgentParams[] = [
  {
    name: 'Assistente Geral',
    description: 'Agente versátil para atendimento geral e suporte básico',
    tags: ['general', 'support'],
    composition_mode: 'auto'
  },
  {
    name: 'Suporte Técnico',
    description: 'Especialista em resolver problemas técnicos e questões de TI',
    tags: ['technical', 'support', 'it'],
    composition_mode: 'auto'
  },
  {
    name: 'Vendas',
    description: 'Agente focado em vendas, prospecção e relacionamento com clientes',
    tags: ['sales', 'customer-service'],
    composition_mode: 'auto'
  },
  {
    name: 'Recursos Humanos',
    description: 'Especialista em questões de RH, recrutamento e gestão de pessoas',
    tags: ['hr', 'recruitment', 'people'],
    composition_mode: 'auto'
  },
  {
    name: 'Atendimento ao Cliente',
    description: 'Agente dedicado ao atendimento e satisfação do cliente',
    tags: ['customer-service', 'support'],
    composition_mode: 'auto'
  }
];

const defaultTags = [
  { name: 'general', description: 'Uso geral' },
  { name: 'support', description: 'Suporte e atendimento' },
  { name: 'technical', description: 'Questões técnicas' },
  { name: 'it', description: 'Tecnologia da informação' },
  { name: 'sales', description: 'Vendas e comercial' },
  { name: 'customer-service', description: 'Atendimento ao cliente' },
  { name: 'hr', description: 'Recursos humanos' },
  { name: 'recruitment', description: 'Recrutamento' },
  { name: 'people', description: 'Gestão de pessoas' }
];

const SetupWizardPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isCreatingAgents, setIsCreatingAgents] = useState(false);
  const [isCreatingTags, setIsCreatingTags] = useState(false);
  const [createdAgents, setCreatedAgents] = useState<string[]>([]);
  const [createdTags, setCreatedTags] = useState<string[]>([]);
  const [setupComplete, setSetupComplete] = useState(false);

  const { createAgent } = useAgents();

  const steps: SetupStep[] = [
    {
      id: 'welcome',
      title: 'Bem-vindo ao Daneel',
      description: 'Configure seu sistema de agentes AI',
      completed: currentStep > 0,
      icon: Wand2
    },
    {
      id: 'tags',
      title: 'Criar Tags Padrão',
      description: 'Configurar tags para organização',
      completed: createdTags.length > 0,
      icon: Tag
    },
    {
      id: 'agents',
      title: 'Criar Agentes Padrão',
      description: 'Configurar agentes básicos do sistema',
      completed: createdAgents.length > 0,
      icon: Users
    },
    {
      id: 'complete',
      title: 'Configuração Completa',
      description: 'Sistema pronto para uso',
      completed: setupComplete,
      icon: CheckCircle
    }
  ];

  const createDefaultTags = async () => {
    setIsCreatingTags(true);
    const created: string[] = [];

    for (const tag of defaultTags) {
      try {
        const response = await fetch('/tags', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: tag.name })
        });

        if (response.ok) {
          created.push(tag.name);
        }
      } catch (error) {
        console.error(`Error creating tag ${tag.name}:`, error);
      }
    }

    setCreatedTags(created);
    setIsCreatingTags(false);
    if (created.length > 0) {
      setCurrentStep(2);
    }
  };

  const createDefaultAgents = async () => {
    setIsCreatingAgents(true);
    const created: string[] = [];

    for (const agentData of defaultAgents) {
      try {
        const result = await createAgent(agentData);
        if (result) {
          created.push(agentData.name);
        }
      } catch (error) {
        console.error(`Error creating agent ${agentData.name}:`, error);
      }
    }

    setCreatedAgents(created);
    setIsCreatingAgents(false);
    if (created.length > 0) {
      setCurrentStep(3);
      setSetupComplete(true);
    }
  };

  const renderWelcomeStep = () => (
    <div className="text-center space-y-6">
      <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
        <img src="/chat/logo.png" alt="Daneel" className="w-12 h-12 object-contain" />
      </div>
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Bem-vindo ao Daneel
        </h2>
        <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Vamos configurar seu sistema com agentes e tags padrão para você começar rapidamente.
        </p>
      </div>
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
          O que será criado:
        </h3>
        <ul className="text-sm text-blue-700 dark:text-blue-200 space-y-1">
          <li>• {defaultTags.length} tags para organização</li>
          <li>• {defaultAgents.length} agentes especializados</li>
          <li>• Configurações básicas do sistema</li>
        </ul>
      </div>
      <Button onClick={() => setCurrentStep(1)} className="w-full sm:w-auto">
        Começar Configuração
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );

  const renderTagsStep = () => (
    <div className="space-y-6">
      <div className="text-center">
        <Tag className="w-12 h-12 text-blue-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          Criar Tags Padrão
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Tags ajudam a organizar agentes, guidelines e outros recursos.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {defaultTags.map((tag, index) => (
          <div key={index} className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <Tag className="h-4 w-4 text-blue-500 mr-3" />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">{tag.name}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">{tag.description}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <Button 
          onClick={createDefaultTags} 
          disabled={isCreatingTags}
          className="flex-1"
        >
          {isCreatingTags ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Criando Tags...
            </>
          ) : (
            <>
              Criar {defaultTags.length} Tags
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
        <Button variant="outline" onClick={() => setCurrentStep(2)}>
          Pular
        </Button>
      </div>

      {createdTags.length > 0 && (
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            <span className="font-medium text-green-900 dark:text-green-100">
              {createdTags.length} tags criadas com sucesso!
            </span>
          </div>
        </div>
      )}
    </div>
  );

  const renderAgentsStep = () => (
    <DefaultAgentsSetup />
  );

  const renderCompleteStep = () => (
    <div className="text-center space-y-6">
      <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto">
        <CheckCircle className="w-12 h-12 text-green-500" />
      </div>
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Configuração Completa!
        </h2>
        <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Seu sistema Daneel está pronto para uso. Você pode começar a criar sessões e interagir com os agentes.
        </p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md mx-auto">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <Tag className="h-6 w-6 text-blue-500 mx-auto mb-2" />
          <div className="font-medium text-blue-900 dark:text-blue-100">
            {createdTags.length} Tags
          </div>
          <div className="text-sm text-blue-700 dark:text-blue-200">
            Criadas
          </div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <Users className="h-6 w-6 text-green-500 mx-auto mb-2" />
          <div className="font-medium text-green-900 dark:text-green-100">
            {createdAgents.length} Agentes
          </div>
          <div className="text-sm text-green-700 dark:text-green-200">
            Criados
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <Button className="w-full sm:w-auto" onClick={() => window.location.href = '/chat/'}>
          Ir para o Chat
        </Button>
        <div>
          <Button variant="outline" onClick={() => setCurrentStep(0)}>
            Executar Setup Novamente
          </Button>
        </div>
      </div>
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 0: return renderWelcomeStep();
      case 1: return renderTagsStep();
      case 2: return renderAgentsStep();
      case 3: return renderCompleteStep();
      default: return renderWelcomeStep();
    }
  };

  return (
    <div className="space-y-8">
      {/* Progress Steps */}
      <div className="flex items-center justify-center">
        <div className="flex items-center space-x-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = step.completed;
            
            return (
              <div key={step.id} className="flex items-center">
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors
                  ${isCompleted 
                    ? 'bg-green-500 border-green-500 text-white' 
                    : isActive 
                      ? 'bg-blue-500 border-blue-500 text-white'
                      : 'bg-gray-100 border-gray-300 text-gray-400'
                  }
                `}>
                  <Icon className="w-5 h-5" />
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-12 h-0.5 mx-2 ${
                    step.completed ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <div className="max-w-2xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8">
          {renderCurrentStep()}
        </div>
      </div>
    </div>
  );
};

export default SetupWizardPage;
