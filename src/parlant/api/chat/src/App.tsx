import './App.css';
import React from 'react';
import AppRouter from './components/AppRouter';
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
	return (
		<ToastProvider>
			<div className='min-h-screen'>
				<AppRouter />
				<WebSocketComp />
			</div>
		</ToastProvider>
	);
}

export default App;
