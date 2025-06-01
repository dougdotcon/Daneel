/* eslint-disable react-hooks/exhaustive-deps */
import React, {ReactElement, useEffect, useRef, useState} from 'react';
import useFetch from '@/hooks/useFetch';
import {Textarea} from '../ui/textarea';
import {Button} from '../ui/button';
import EnhancedInput from '../chat-input/enhanced-input';
import {deleteData, postData} from '@/utils/api';
import {groupBy} from '@/utils/obj';
import Message from '../message/message';
import {EventInterface, ServerStatus, SessionInterface} from '@/utils/interfaces';
import Spacer from '../ui/custom/spacer';
import {toast} from 'sonner';
import {NEW_SESSION_ID} from '../chat-header/chat-header';
import {useQuestionDialog} from '@/hooks/useQuestionDialog';
import {twJoin, twMerge} from 'tailwind-merge';
import MessageDetails from '../message-details/message-details';
import {useAtom} from 'jotai';
import {agentAtom, agentsAtom, emptyPendingMessage, newSessionAtom, pendingMessageAtom, sessionAtom, sessionsAtom, viewingMessageDetailsAtom} from '@/store';
import ErrorBoundary from '../error-boundary/error-boundary';
import DateHeader from './date-header/date-header';
import SessoinViewHeader from './session-view-header/session-view-header';
import {isSameDay} from '@/lib/utils';
import {DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger} from '../ui/dropdown-menu';
import {ShieldEllipsis} from 'lucide-react';

const SessionView = (): ReactElement => {
	const lastMessageRef = useRef<HTMLDivElement>(null);
	const submitButtonRef = useRef<HTMLButtonElement>(null);
	const textareaRef = useRef<HTMLTextAreaElement>(null);
	const messagesRef = useRef<HTMLDivElement>(null);

	const [message, setMessage] = useState('');
	const [lastOffset, setLastOffset] = useState(0);
	const [messages, setMessages] = useState<EventInterface[]>([]);
	const [showTyping, setShowTyping] = useState(false);
	const [showThinking, setShowThinking] = useState(false);
	const [isFirstScroll, setIsFirstScroll] = useState(true);
	const {openQuestionDialog, closeQuestionDialog} = useQuestionDialog();
	const [useContentFiltering, setUseContentFiltering] = useState(false);
	const [showLogsForMessage, setShowLogsForMessage] = useState<EventInterface | null>(null);
	const [isMissingAgent, setIsMissingAgent] = useState<boolean | null>(null);
	const [isContentFilterMenuOpen, setIsContentFilterMenuOpen] = useState(false);

	const [pendingMessage, setPendingMessage] = useAtom<EventInterface>(pendingMessageAtom);
	const [agents] = useAtom(agentsAtom);
	const [session, setSession] = useAtom(sessionAtom);
	const [agent] = useAtom(agentAtom);
	const [newSession, setNewSession] = useAtom(newSessionAtom);
	const [, setViewingMessage] = useAtom(viewingMessageDetailsAtom);
	const [, setSessions] = useAtom(sessionsAtom);
	const {data: lastEvents, refetch, ErrorTemplate} = useFetch<EventInterface[]>(`sessions/${session?.id}/events`, {min_offset: lastOffset}, [], session?.id !== NEW_SESSION_ID, !!(session?.id && session?.id !== NEW_SESSION_ID), false);

	const resetChat = () => {
		setMessage('');
		setLastOffset(0);
		setMessages([]);
		setShowTyping(false);
		setShowLogsForMessage(null);
	};

	const resendMessageDialog = (index: number) => (sessionId: string, text?: string) => {
		const isLastMessage = index === messages.length - 1;
		const lastUserMessageOffset = messages[index].offset;

		if (isLastMessage) {
			setShowLogsForMessage(null);
			return resendMessage(index, sessionId, lastUserMessageOffset, text);
		}

		const onApproved = () => {
			setShowLogsForMessage(null);
			closeQuestionDialog();
			resendMessage(index, sessionId, lastUserMessageOffset, text);
		};

		const question = 'Resending this message would cause all of the following messages in the session to disappear.';
		openQuestionDialog('Are you sure?', question, [{text: 'Resend Anyway', onClick: onApproved, isMainAction: true}]);
	};

	const regenerateMessageDialog = (index: number) => (sessionId: string) => {
		const isLastMessage = index === messages.length - 1;
		const prevMessages = messages.slice(0, index + 1);
		const lastUserMessageIndex = prevMessages.findLastIndex((message) => message.source === 'customer' && message.kind === 'message');
		const lastUserMessage = prevMessages[lastUserMessageIndex];
		const lastUserMessageOffset = lastUserMessage?.offset ?? messages.length - 1;

		if (isLastMessage) {
			setShowLogsForMessage(null);
			return regenerateMessage(lastUserMessageIndex, sessionId, lastUserMessageOffset);
		}

		const onApproved = () => {
			setShowLogsForMessage(null);
			closeQuestionDialog();
			regenerateMessage(lastUserMessageIndex, sessionId, lastUserMessageOffset);
		};

		const question = 'Regenerating this message would cause all of the following messages in the session to disappear.';
		openQuestionDialog('Are you sure?', question, [{text: 'Regenerate Anyway', onClick: onApproved, isMainAction: true}]);
	};

	const resendMessage = async (index: number, sessionId: string, offset: number, text?: string) => {
		const event = messages[index];

		const deleteSession = await deleteData(`sessions/${sessionId}/events?min_offset=${offset}`).catch((e) => ({error: e}));
		if (deleteSession?.error) {
			toast.error(deleteSession.error.message || deleteSession.error);
			return;
		}

		setLastOffset(offset);
		setMessages((messages) => messages.slice(0, index));
		postMessage(text ?? event.data?.message);
	};

	const regenerateMessage = async (index: number, sessionId: string, offset: number) => {
		resendMessage(index, sessionId, offset);
	};

	const formatMessagesFromEvents = () => {
		if (session?.id === NEW_SESSION_ID) return;
		const lastEvent = lastEvents?.at(-1);
		const lastStatusEvent = lastEvents?.findLast((e) => e.kind === 'status');
		if (!lastEvent) return;

		const offset = lastEvent?.offset;
		if (offset || offset === 0) setLastOffset(offset + 1);

		const correlationsMap = groupBy(lastEvents || [], (item: EventInterface) => item?.correlation_id.split('::')[0]);

		const newMessages = lastEvents?.filter((e) => e.kind === 'message') || [];
		const withStatusMessages = newMessages.map((newMessage, i) => {
			const data: EventInterface = {...newMessage};
			const item = correlationsMap?.[newMessage.correlation_id.split('::')[0]]?.at(-1)?.data;
			data.serverStatus = (item?.status || (newMessages[i + 1] ? 'ready' : null)) as ServerStatus;
			if (data.serverStatus === 'error') data.error = item?.data?.exception;
			return data;
		});

		setMessages((messages) => {
			const last = messages.at(-1);
			if (last?.source === 'customer' && correlationsMap?.[last?.correlation_id]) {
				last.serverStatus = correlationsMap[last.correlation_id].at(-1)?.data?.status || last.serverStatus;
				if (last.serverStatus === 'error') last.error = correlationsMap[last.correlation_id].at(-1)?.data?.data?.exception;
			}
			if (!withStatusMessages?.length) return [...messages];
			if (pendingMessage?.data?.message) setPendingMessage(emptyPendingMessage());

			const newVals: EventInterface[] = [];
			for (const messageArray of [messages, withStatusMessages]) {
				for (const message of messageArray) {
					newVals[message.offset] = message;
				}
			}
			return newVals.filter((message) => message);
		});

		const lastStatusEventStaus = lastStatusEvent?.data?.status;

		if (lastStatusEventStaus) {
			setShowThinking(!!messages?.length && lastStatusEventStaus === 'processing');
			setShowTyping(lastStatusEventStaus === 'typing');
		}

		refetch();
	};

	const scrollToLastMessage = () => {
		lastMessageRef?.current?.scrollIntoView?.({behavior: isFirstScroll ? 'instant' : 'smooth'});
		if (lastMessageRef?.current && isFirstScroll) setIsFirstScroll(false);
	};

	const resetSession = () => {
		setIsFirstScroll(true);
		if (newSession && session?.id !== NEW_SESSION_ID) setNewSession(null);
		resetChat();
		textareaRef?.current?.focus();
	};

	useEffect(() => {
		if (lastOffset === 0) refetch();
	}, [lastOffset]);
	useEffect(() => setViewingMessage(showLogsForMessage), [showLogsForMessage]);
	useEffect(formatMessagesFromEvents, [lastEvents]);
	useEffect(scrollToLastMessage, [messages?.length, pendingMessage, isFirstScroll]);
	useEffect(resetSession, [session?.id]);
	useEffect(() => {
		if (agents && agent?.id) setIsMissingAgent(!agents?.find((a) => a.id === agent?.id));
	}, [agents, agent?.id]);

	const createSession = async (): Promise<SessionInterface | undefined> => {
		if (!newSession) return;
		const {customer_id, title} = newSession;
		return postData('sessions?allow_greeting=false', {customer_id, agent_id: agent?.id, title} as object)
			.then((res: SessionInterface) => {
				if (newSession) {
					setSession(res);
					setNewSession(null);
				}
				setSessions((sessions) => [...sessions, res]);
				return res;
			})
			.catch(() => {
				toast.error('Something went wrong');
				return undefined;
			});
	};

	const postMessage = async (content: string): Promise<void> => {
		setPendingMessage((pendingMessage) => ({...pendingMessage, sessionId: session?.id, data: {message: content}}));
		setMessage('');
		const eventSession = newSession ? (await createSession())?.id : session?.id;
		const useContentFilteringStatus = useContentFiltering ? 'auto' : 'none';
		postData(`sessions/${eventSession}/events?moderation=${useContentFilteringStatus}`, {kind: 'message', message: content, source: 'customer'})
			.then(() => {
				refetch();
			})
			.catch(() => toast.error('Something went wrong'));
	};

	const handleTextareaKeydown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			submitButtonRef?.current?.click();
		} else if (e.key === 'Enter' && e.shiftKey) e.preventDefault();
	};

	const isCurrSession = (session?.id === NEW_SESSION_ID && !pendingMessage?.id) || (session?.id !== NEW_SESSION_ID && pendingMessage?.sessionId === session?.id);
	const visibleMessages = (!messages?.length || isCurrSession) && pendingMessage?.data?.message ? [...messages, pendingMessage] : messages;

	const showLogs = (i: number) => (event: EventInterface) => {
		event.index = i;
		setShowLogsForMessage(event.id === showLogsForMessage?.id ? null : event);
	};

	return (
		<>
			<div ref={messagesRef} className={twMerge('flex items-center h-full w-full bg-white gap-[14px] rounded-[10px]', showLogsForMessage && 'bg-green-light')}>
				<div className={twMerge('h-full w-full pb-[14px] pt-0 rounded-[10px] flex flex-col transition-all duration-500 bg-white', showLogsForMessage && 'w-[calc(100%-min(700px,35vw))]')}>
					<div className='h-full flex flex-col rounded-[10px] m-auto w-full min-w-[unset]'>
						{/* <div className='h-[58px] bg-[#f5f5f9]'></div> */}
						<SessoinViewHeader />
						<div className={twMerge('h-[21px] border-t-0 bg-white')}></div>
						<div className={twMerge('flex flex-col rounded-es-[16px] rounded-ee-[16px] items-center bg-white mx-auto w-full flex-1 overflow-hidden')}>
							<div className='messages [scroll-snap-type:y_mandatory] fixed-scroll flex-1 flex flex-col w-full pb-4 overflow-x-hidden' aria-live='polite' role='log' aria-label='Chat messages'>
								{ErrorTemplate && <ErrorTemplate />}
								{visibleMessages.map((event, i) => (
									<React.Fragment key={i}>
										{!isSameDay(messages[i - 1]?.creation_utc, event.creation_utc) && <DateHeader date={event.creation_utc} isFirst={!i} bgColor='bg-white' />}
										<div ref={lastMessageRef} className='flex snap-end flex-col max-w-[min(1020px,100%)] w-[1020px] self-center'>
											<Message
												isFirstMessageInDate={!isSameDay(messages[i - 1]?.creation_utc, event.creation_utc)}
												isRegenerateHidden={!!isMissingAgent}
												event={event}
												isContinual={event.source === visibleMessages[i - 1]?.source}
												regenerateMessageFn={regenerateMessageDialog(i)}
												resendMessageFn={resendMessageDialog(i)}
												showLogsForMessage={showLogsForMessage}
												showLogs={showLogs(i)}
											/>
										</div>
									</React.Fragment>
								))}
							</div>
							<div className={twMerge('w-full flex justify-center px-4', isMissingAgent && 'hidden')}>
								<div className="w-full max-w-[1000px] mb-6">
									<EnhancedInput
										value={message}
										onChange={setMessage}
										onSend={(content, attachments) => {
											console.log('Attachments:', attachments); // Handle attachments in the future
											postMessage(content);
										}}
										placeholder="Type your message..."
										disabled={!agent?.id}
										className="shadow-lg"
									/>

									{/* Content filtering options */}
									<div className="flex items-center justify-between mt-2 px-2">
										<div className="flex items-center gap-2">
											<DropdownMenu open={isContentFilterMenuOpen} onOpenChange={setIsContentFilterMenuOpen}>
												<DropdownMenuTrigger className='outline-none text-sm text-gray-600 hover:text-gray-800' data-testid='menu-button'>
													<div className="flex items-center gap-1">
														{!useContentFiltering && <img src='icons/edit.svg' alt='' className='h-3 w-3' />}
														{useContentFiltering && <ShieldEllipsis className='h-3 w-3' />}
														<span>{useContentFiltering ? 'Content Moderation' : 'Direct Mode'}</span>
													</div>
												</DropdownMenuTrigger>
												<DropdownMenuContent side='top' align='start' className='max-w-[480px]'>
													<DropdownMenuItem
														onClick={() => setUseContentFiltering(false)}
														className={twMerge('cursor-pointer', !useContentFiltering && 'bg-gray-100')}>
														<img src='icons/edit.svg' alt='' className='me-2 h-4 w-4' />
														Direct (No Moderation)
													</DropdownMenuItem>
													<DropdownMenuItem
														onClick={() => setUseContentFiltering(true)}
														className={twMerge('cursor-pointer', useContentFiltering && 'bg-gray-100')}>
														<ShieldEllipsis className='me-2 h-4 w-4' />
														<div>
															<div>Content Moderation</div>
															<small className='text-gray-500'>
																Messages will be flagged for harmful content
															</small>
														</div>
													</DropdownMenuItem>
												</DropdownMenuContent>
											</DropdownMenu>
										</div>

										{/* Typing indicator */}
										{(showTyping || showThinking) && (
											<p className='text-sm text-gray-500'>
												{showTyping ? `${agent?.name} is typing...` : `${agent?.name} is thinking...`}
											</p>
										)}
									</div>
								</div>
							</div>
							<div className='w-full'>
								<Spacer />
								<div></div>
								<Spacer />
							</div>
						</div>
					</div>
				</div>
				<ErrorBoundary component={<div className='flex h-full min-w-[50%] justify-center items-center text-[20px]'>Failed to load logs</div>}>
					<div
						className={twMerge(
							'fixed top-0 left-[unset] h-full right-0 z-[99] bg-white translate-x-[100%] max-w-[min(700px,35vw)] [box-shadow:0px_0px_30px_0px_#0000001F] w-[min(700px,35vw)] [transition-duration:600ms]',
							showLogsForMessage && 'translate-x-0'
						)}>
						{showLogsForMessage && (
							<MessageDetails
								event={showLogsForMessage}
								regenerateMessageFn={showLogsForMessage?.index ? regenerateMessageDialog(showLogsForMessage.index) : undefined}
								resendMessageFn={showLogsForMessage?.index || showLogsForMessage?.index === 0 ? resendMessageDialog(showLogsForMessage.index) : undefined}
								closeLogs={() => setShowLogsForMessage(null)}
							/>
						)}
					</div>
				</ErrorBoundary>
			</div>
		</>
	);
};

export default SessionView;
