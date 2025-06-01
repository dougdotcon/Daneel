/* eslint-disable react-refresh/only-export-components */
import {createContext, ReactElement, useEffect, useState} from 'react';
import SessionList from '../session-list/session-list';
import ErrorBoundary from '../error-boundary/error-boundary';
import ChatHeader from '../chat-header/chat-header';
import {useDialog} from '@/hooks/useDialog';
import {Helmet} from 'react-helmet';
import {NEW_SESSION_ID} from '../agents-list/agent-list';
import {useAtom} from 'jotai';
import {dialogAtom, sessionAtom} from '@/store';
import {twMerge} from 'tailwind-merge';
import SessionView from '../session-view/session-view';

export const SessionProvider = createContext({});

const SessionsSection = () => {
	const [filterSessionVal, setFilterSessionVal] = useState('');
	return (
		<div className='bg-white [box-shadow:0px_0px_25px_0px_#0000000A] h-full rounded-[16px] overflow-hidden border-solid w-[352px] min-w-[352px] max-mobile:hidden z-[11] '>
			<ChatHeader setFilterSessionVal={setFilterSessionVal} />
			<SessionList filterSessionVal={filterSessionVal} />
		</div>
	);
};

interface ChatbotProps {
	onNavigateToAdmin?: () => void;
}

export default function Chatbot({ onNavigateToAdmin }: ChatbotProps): ReactElement {
	// const SessionView = lazy(() => import('../session-view/session-view'));
	const [sessionName, setSessionName] = useState<string | null>('');
	const {openDialog, DialogComponent, closeDialog} = useDialog();
	const [session] = useAtom(sessionAtom);
	const [, setDialog] = useAtom(dialogAtom);
	const [, setFilterSessionVal] = useState('');

	useEffect(() => {
		if (session?.id) {
			if (session?.id === NEW_SESSION_ID) setSessionName('Parlant | New Session');
			else {
				const sessionTitle = session?.title;
				if (sessionTitle) setSessionName(`Parlant | ${sessionTitle}`);
			}
		} else setSessionName('Parlant');
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [session?.id]);

	useEffect(() => {
		setDialog({openDialog, closeDialog});
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	return (
		<ErrorBoundary>
			<SessionProvider.Provider value={{}}>
				<Helmet defaultTitle={`${sessionName}`} />
				<div className={'flex items-center justify-between bg-blue-primary h-[80px] mb-[14px] [box-shadow:0px_0px_25px_0px_#0000000A] px-6'}>
					<div className="flex items-center space-x-3">
						<img src='/chat/logo.png' alt='Daneel Logo' className='h-12 w-12 object-contain' />
						<div className="flex flex-col">
							<h1 className="text-white text-xl font-bold">Daneel</h1>
							<p className="text-blue-100 text-sm">AI Assistant System</p>
						</div>
					</div>
					{onNavigateToAdmin && (
						<button
							onClick={onNavigateToAdmin}
							className="flex items-center space-x-2 px-6 py-3 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
						>
							<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							<span>Admin</span>
						</button>
					)}
				</div>
				<div data-testid='chatbot' className={'main bg-gradient-to-br from-blue-50 to-indigo-100 h-[calc(100vh-94px)] flex flex-col rounded-[20px] shadow-2xl border border-blue-200'}>
					<div className='hidden max-mobile:block rounded-[16px]'>
						<ChatHeader setFilterSessionVal={setFilterSessionVal} />
					</div>
					<div className={twMerge('flex bg-transparent justify-between flex-1 gap-[20px] w-full overflow-auto flex-row pb-[20px] px-[20px] pt-[10px]')}>
						<div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-blue-200/50 overflow-hidden">
							<SessionsSection />
						</div>
						{session?.id ? (
							<div className='h-full w-[calc(100vw-352px-55px)] bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-blue-200/50 max-w-[calc(100vw-352px-55px)] max-[800px]:max-w-full max-[800px]:w-full overflow-hidden'>
								{/* <Suspense> */}
								<SessionView />
								{/* </Suspense> */}
							</div>
						) : (
							<div className='flex-1 flex flex-col gap-[27px] items-center justify-center bg-white/60 backdrop-blur-sm rounded-xl border border-blue-200/50'>
								<div className="text-center space-y-4">
									<div className="w-24 h-24 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
										<svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
										</svg>
									</div>
									<div>
										<h3 className="text-xl font-semibold text-blue-800 mb-2">Welcome to Daneel</h3>
										<p className='text-blue-600 select-none font-medium text-[16px]'>Select a session to start chatting with your AI assistant</p>
									</div>
								</div>
							</div>
						)}
					</div>
				</div>
			</SessionProvider.Provider>
			<DialogComponent />
		</ErrorBoundary>
	);
}
