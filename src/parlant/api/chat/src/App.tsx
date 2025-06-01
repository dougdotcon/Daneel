import './App.css';
import React, { useState } from 'react';
import Chatbot from './components/chatbot/chatbot';
import AdminInterface from './components/admin/AdminInterface';
import { ToastProvider } from './components/ui/toast';
import {useWebSocket} from './hooks/useWebSocket';
import {BASE_URL} from './utils/api';
import {handleChatLogs} from './utils/logs';

const WebSocketComp = () => {
	const socket = useWebSocket(`${BASE_URL}/logs`, true, null, handleChatLogs);
	void socket;
	return <div></div>;
};

function App() {
	const [currentView, setCurrentView] = useState<'chat' | 'admin'>('chat');

	// Check URL to determine initial view
	React.useEffect(() => {
		const path = window.location.pathname;
		if (path.includes('admin')) {
			setCurrentView('admin');
		} else {
			setCurrentView('chat');
		}
	}, []);

	// Update URL when view changes
	React.useEffect(() => {
		const newPath = currentView === 'admin' ? '/chat/admin' : '/chat/';
		if (window.location.pathname !== newPath) {
			window.history.pushState({}, '', newPath);
		}
	}, [currentView]);

	return (
		<ToastProvider>
			<div className='bg-blue-light min-h-screen'>
				{currentView === 'chat' ? (
					<>
						<Chatbot onNavigateToAdmin={() => setCurrentView('admin')} />
						<WebSocketComp />
					</>
				) : (
					<AdminInterface onNavigateToChat={() => setCurrentView('chat')} />
				)}
			</div>
		</ToastProvider>
	);
}

export default App;
