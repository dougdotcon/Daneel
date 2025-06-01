import React, { useState } from 'react';
import { 
  Bot, 
  Plus, 
  Download, 
  Star, 
  Users, 
  MessageSquare, 
  Brain, 
  Code, 
  Calculator, 
  BookOpen, 
  Briefcase, 
  Heart, 
  Palette, 
  Music,
  Camera,
  Gamepad2,
  Wrench,
  Shield,
  Zap,
  Target,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface DefaultAgent {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ComponentType<any>;
  color: string;
  features: string[];
  prompt: string;
  tags: string[];
  difficulty: 'Básico' | 'Intermediário' | 'Avançado';
  estimatedTime: string;
}

const DefaultAgentsPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isCreating, setIsCreating] = useState<string | null>(null);

  const defaultAgents: DefaultAgent[] = [
    {
      id: 'assistant',
      name: 'Assistente Geral',
      description: 'Assistente versátil para tarefas gerais, perguntas e suporte básico',
      category: 'Geral',
      icon: Bot,
      color: 'blue',
      features: ['Conversação natural', 'Suporte geral', 'Respostas rápidas'],
      prompt: 'Você é um assistente útil e amigável. Responda de forma clara e concisa.',
      tags: ['geral', 'suporte', 'conversação'],
      difficulty: 'Básico',
      estimatedTime: '2 min'
    },
    {
      id: 'customer-support',
      name: 'Suporte ao Cliente',
      description: 'Especializado em atendimento ao cliente e resolução de problemas',
      category: 'Atendimento',
      icon: Users,
      color: 'green',
      features: ['Atendimento 24/7', 'Resolução de problemas', 'Escalação inteligente'],
      prompt: 'Você é um agente de suporte ao cliente profissional e empático.',
      tags: ['suporte', 'atendimento', 'cliente'],
      difficulty: 'Intermediário',
      estimatedTime: '3 min'
    },
    {
      id: 'sales-assistant',
      name: 'Assistente de Vendas',
      description: 'Especializado em vendas, qualificação de leads e conversão',
      category: 'Vendas',
      icon: Target,
      color: 'purple',
      features: ['Qualificação de leads', 'Apresentação de produtos', 'Fechamento de vendas'],
      prompt: 'Você é um consultor de vendas experiente e persuasivo.',
      tags: ['vendas', 'leads', 'conversão'],
      difficulty: 'Avançado',
      estimatedTime: '5 min'
    },
    {
      id: 'technical-support',
      name: 'Suporte Técnico',
      description: 'Especializado em problemas técnicos e troubleshooting',
      category: 'Técnico',
      icon: Wrench,
      color: 'orange',
      features: ['Diagnóstico técnico', 'Soluções passo-a-passo', 'Documentação'],
      prompt: 'Você é um especialista técnico com conhecimento profundo em tecnologia.',
      tags: ['técnico', 'troubleshooting', 'suporte'],
      difficulty: 'Avançado',
      estimatedTime: '4 min'
    },
    {
      id: 'content-creator',
      name: 'Criador de Conteúdo',
      description: 'Especializado em criação de textos, artigos e conteúdo criativo',
      category: 'Criativo',
      icon: Palette,
      color: 'pink',
      features: ['Redação criativa', 'SEO otimizado', 'Múltiplos formatos'],
      prompt: 'Você é um redator criativo e especialista em marketing de conteúdo.',
      tags: ['conteúdo', 'redação', 'criativo'],
      difficulty: 'Intermediário',
      estimatedTime: '3 min'
    },
    {
      id: 'data-analyst',
      name: 'Analista de Dados',
      description: 'Especializado em análise de dados, relatórios e insights',
      category: 'Análise',
      icon: Calculator,
      color: 'indigo',
      features: ['Análise estatística', 'Visualização de dados', 'Relatórios'],
      prompt: 'Você é um analista de dados experiente com foco em insights acionáveis.',
      tags: ['dados', 'análise', 'relatórios'],
      difficulty: 'Avançado',
      estimatedTime: '6 min'
    },
    {
      id: 'educator',
      name: 'Educador',
      description: 'Especializado em ensino, explicações didáticas e tutoria',
      category: 'Educação',
      icon: BookOpen,
      color: 'emerald',
      features: ['Explicações didáticas', 'Exercícios práticos', 'Avaliação'],
      prompt: 'Você é um educador paciente e didático, especialista em ensinar.',
      tags: ['educação', 'ensino', 'tutoria'],
      difficulty: 'Intermediário',
      estimatedTime: '4 min'
    },
    {
      id: 'hr-assistant',
      name: 'Assistente de RH',
      description: 'Especializado em recursos humanos, recrutamento e gestão de pessoas',
      category: 'RH',
      icon: Heart,
      color: 'rose',
      features: ['Recrutamento', 'Avaliação de candidatos', 'Gestão de pessoas'],
      prompt: 'Você é um especialista em recursos humanos com foco em pessoas.',
      tags: ['rh', 'recrutamento', 'pessoas'],
      difficulty: 'Intermediário',
      estimatedTime: '4 min'
    }
  ];

  const categories = ['all', ...Array.from(new Set(defaultAgents.map(agent => agent.category)))];

  const filteredAgents = selectedCategory === 'all' 
    ? defaultAgents 
    : defaultAgents.filter(agent => agent.category === selectedCategory);

  const handleCreateAgent = async (agentId: string) => {
    setIsCreating(agentId);
    
    // Simular criação do agente
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setIsCreating(null);
    
    // Aqui você integraria com a API real para criar o agente
    console.log('Agente criado:', agentId);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Básico': return 'bg-green-100 text-green-800';
      case 'Intermediário': return 'bg-yellow-100 text-yellow-800';
      case 'Avançado': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getIconColor = (color: string) => {
    const colors: Record<string, string> = {
      blue: 'text-blue-600 bg-blue-100',
      green: 'text-green-600 bg-green-100',
      purple: 'text-purple-600 bg-purple-100',
      orange: 'text-orange-600 bg-orange-100',
      pink: 'text-pink-600 bg-pink-100',
      indigo: 'text-indigo-600 bg-indigo-100',
      emerald: 'text-emerald-600 bg-emerald-100',
      rose: 'text-rose-600 bg-rose-100'
    };
    return colors[color] || 'text-gray-600 bg-gray-100';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Agentes Pré-Prontos
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Crie agentes especializados automaticamente com configurações otimizadas
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Importar Template
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Bot className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Templates</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{defaultAgents.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Star className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Populares</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">4</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Zap className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Criação Rápida</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">2-6 min</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Shield className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Categorias</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{categories.length - 1}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <Button
            key={category}
            variant={selectedCategory === category ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(category)}
            className="capitalize"
          >
            {category === 'all' ? 'Todos' : category}
          </Button>
        ))}
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => {
          const Icon = agent.icon;
          const isCreatingThis = isCreating === agent.id;
          
          return (
            <Card key={agent.id} className="hover:shadow-lg transition-shadow duration-200">
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className={`p-3 rounded-lg ${getIconColor(agent.color)}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <Badge className={getDifficultyColor(agent.difficulty)}>
                    {agent.difficulty}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <CardTitle className="text-lg">{agent.name}</CardTitle>
                  <CardDescription className="text-sm">
                    {agent.description}
                  </CardDescription>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Features */}
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                    Funcionalidades:
                  </p>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    {agent.features.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2">
                        <CheckCircle className="h-3 w-3 text-green-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {agent.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>

                {/* Time Estimate */}
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <Clock className="h-4 w-4" />
                  <span>Tempo estimado: {agent.estimatedTime}</span>
                </div>

                {/* Action Button */}
                <Button 
                  onClick={() => handleCreateAgent(agent.id)}
                  disabled={isCreatingThis}
                  className="w-full"
                >
                  {isCreatingThis ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Criando...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 mr-2" />
                      Criar Agente
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredAgents.length === 0 && (
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Nenhum agente encontrado
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Tente selecionar uma categoria diferente.
          </p>
        </div>
      )}
    </div>
  );
};

export default DefaultAgentsPage;
