import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Settings,
  ArrowRight,
  Sparkles,
  Users,
  BarChart3,
  Zap,
  Shield,
  Cpu,
  Globe,
  Heart
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeScreenProps {
  onNavigateToChat: () => void;
  onNavigateToAdmin: () => void;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onNavigateToChat, onNavigateToAdmin }) => {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Trigger animation after component mounts
    const timer = setTimeout(() => setIsLoaded(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === '1' || event.key === 'c') {
        onNavigateToChat();
      } else if (event.key === '2' || event.key === 'a') {
        onNavigateToAdmin();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [onNavigateToChat, onNavigateToAdmin]);

  const features = [
    {
      icon: MessageSquare,
      title: 'Chat Inteligente',
      description: 'Converse com agentes AI especializados'
    },
    {
      icon: Users,
      title: 'Múltiplos Agentes',
      description: 'Agentes especializados para diferentes áreas'
    },
    {
      icon: BarChart3,
      title: 'Analytics Avançado',
      description: 'Métricas detalhadas de performance'
    },
    {
      icon: Shield,
      title: 'Seguro e Confiável',
      description: 'Dados protegidos e processamento local'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className={`max-w-6xl mx-auto text-center transition-all duration-1000 ${
          isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}>
          
          {/* Logo and Title */}
          <div className="mb-12">
            <div className="flex items-center justify-center mb-6">
              <div className="relative">
                <img 
                  src="/chat/logo.png" 
                  alt="Daneel" 
                  className="h-24 w-24 object-contain drop-shadow-lg"
                />
                <div className="absolute -top-2 -right-2">
                  <Sparkles className="h-6 w-6 text-yellow-500 animate-pulse" />
                </div>
              </div>
            </div>
            
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 dark:text-white mb-4">
              Bem-vindo ao <span className="text-blue-600 dark:text-blue-400">Daneel</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-2">
              Arsenal de Simulação Imersiva para Meios Ontológicos Virtuais
            </p>
            
            <p className="text-lg text-gray-500 dark:text-gray-400 max-w-3xl mx-auto">
              Sistema avançado de agentes AI para automação inteligente, 
              atendimento personalizado e análise de dados em tempo real.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div 
                  key={index}
                  className={`bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700 transition-all duration-500 hover:shadow-xl hover:scale-105 ${
                    isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                  }`}
                  style={{ transitionDelay: `${index * 100 + 200}ms` }}
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg mb-4">
                      <Icon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {feature.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Main Action Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-12">
            
            {/* Chat Option */}
            <div className={`group transition-all duration-700 ${
              isLoaded ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-8'
            }`}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-700 hover:shadow-2xl transition-all duration-300 hover:scale-105">
                <div className="flex flex-col items-center text-center">
                  <div className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl mb-6 group-hover:scale-110 transition-transform duration-300">
                    <MessageSquare className="h-8 w-8 text-white" />
                  </div>
                  
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                    Iniciar Chat
                  </h2>
                  
                  <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
                    Converse com agentes AI especializados. 
                    Obtenha respostas inteligentes e suporte personalizado.
                  </p>
                  
                  <div className="space-y-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
                    <div className="flex items-center justify-center gap-2">
                      <Zap className="h-4 w-4" />
                      <span>Respostas instantâneas</span>
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <Users className="h-4 w-4" />
                      <span>Múltiplos agentes especializados</span>
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <Globe className="h-4 w-4" />
                      <span>Disponível 24/7</span>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={onNavigateToChat}
                    size="lg"
                    className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 group-hover:shadow-lg"
                  >
                    Começar Conversa
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                  
                  <p className="text-xs text-gray-400 mt-3">
                    Pressione <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">C</kbd> ou <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">1</kbd>
                  </p>
                </div>
              </div>
            </div>

            {/* Admin Option */}
            <div className={`group transition-all duration-700 ${
              isLoaded ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'
            }`}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-700 hover:shadow-2xl transition-all duration-300 hover:scale-105">
                <div className="flex flex-col items-center text-center">
                  <div className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl mb-6 group-hover:scale-110 transition-transform duration-300">
                    <Settings className="h-8 w-8 text-white" />
                  </div>
                  
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                    Painel Admin
                  </h2>
                  
                  <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
                    Gerencie agentes, monitore performance e 
                    configure o sistema completo.
                  </p>
                  
                  <div className="space-y-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
                    <div className="flex items-center justify-center gap-2">
                      <Cpu className="h-4 w-4" />
                      <span>Controle total do sistema</span>
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      <span>Analytics e métricas</span>
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <Shield className="h-4 w-4" />
                      <span>Configurações avançadas</span>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={onNavigateToAdmin}
                    size="lg"
                    variant="outline"
                    className="w-full border-2 border-purple-500 text-purple-600 hover:bg-purple-500 hover:text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 group-hover:shadow-lg"
                  >
                    Acessar Admin
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                  </Button>
                  
                  <p className="text-xs text-gray-400 mt-3">
                    Pressione <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">A</kbd> ou <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">2</kbd>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Footer Info */}
          <div className={`text-center transition-all duration-1000 ${
            isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`} style={{ transitionDelay: '800ms' }}>
            <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center justify-center gap-1">
              Desenvolvido com <Heart className="h-4 w-4 text-red-500" /> para automação inteligente • Versão 1.0.0
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;
