import React, { useState, useEffect } from 'react';
import WelcomeScreen from './WelcomeScreen';
import Chatbot from './chatbot/chatbot';
import AdminInterface from './admin/AdminInterface';

type AppView = 'welcome' | 'chat' | 'admin';

const AppRouter: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>('welcome');
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Check URL on mount to determine initial view
  useEffect(() => {
    const path = window.location.pathname;
    if (path.includes('/admin')) {
      setCurrentView('admin');
    } else if (path.includes('/chat')) {
      setCurrentView('chat');
    } else {
      setCurrentView('welcome');
    }
  }, []);

  // Update URL when view changes
  useEffect(() => {
    const newPath = currentView === 'welcome' ? '/chat/' : `/chat/${currentView}`;
    if (window.location.pathname !== newPath) {
      window.history.pushState({}, '', newPath);
    }
  }, [currentView]);

  const handleViewChange = (newView: AppView) => {
    if (newView === currentView) return;
    
    setIsTransitioning(true);
    
    // Small delay for smooth transition
    setTimeout(() => {
      setCurrentView(newView);
      setIsTransitioning(false);
    }, 150);
  };

  const handleNavigateToChat = () => {
    handleViewChange('chat');
  };

  const handleNavigateToAdmin = () => {
    handleViewChange('admin');
  };

  const handleNavigateToWelcome = () => {
    handleViewChange('welcome');
  };

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      if (path.includes('/admin')) {
        setCurrentView('admin');
      } else if (path.includes('/chat')) {
        setCurrentView('chat');
      } else {
        setCurrentView('welcome');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const renderCurrentView = () => {
    switch (currentView) {
      case 'welcome':
        return (
          <WelcomeScreen 
            onNavigateToChat={handleNavigateToChat}
            onNavigateToAdmin={handleNavigateToAdmin}
          />
        );
      case 'chat':
        return (
          <div className='bg-blue-light min-h-screen'>
            <Chatbot
              onNavigateToAdmin={handleNavigateToAdmin}
              onNavigateToWelcome={handleNavigateToWelcome}
            />
          </div>
        );
      case 'admin':
        return (
          <AdminInterface 
            onNavigateToChat={handleNavigateToChat}
            onNavigateToWelcome={handleNavigateToWelcome}
          />
        );
      default:
        return (
          <WelcomeScreen 
            onNavigateToChat={handleNavigateToChat}
            onNavigateToAdmin={handleNavigateToAdmin}
          />
        );
    }
  };

  return (
    <div className="min-h-screen">
      {/* Transition overlay */}
      {isTransitioning && (
        <div className="fixed inset-0 bg-white dark:bg-gray-900 z-50 flex items-center justify-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-gray-600 dark:text-gray-400">Carregando...</span>
          </div>
        </div>
      )}
      
      {/* Current view */}
      <div className={`transition-opacity duration-300 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}>
        {renderCurrentView()}
      </div>
    </div>
  );
};

export default AppRouter;
