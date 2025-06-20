# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import os
from typing import Awaitable, Callable, TypeAlias

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from lagom import Container

from Daneel.adapters.loggers.websocket import WebSocketLogger
from Daneel.api import agents, index, relationships
from Daneel.api import sessions
from Daneel.api import glossary
from Daneel.api import guidelines
from Daneel.api import context_variables as variables
from Daneel.api import services
from Daneel.api import tags
from Daneel.api import customers
from Daneel.api import logs
from Daneel.api import utterances
from Daneel.api import system_stats
from Daneel.core.context_variables import ContextVariableStore
from Daneel.core.contextual_correlator import ContextualCorrelator
from Daneel.core.agents import AgentStore
from Daneel.core.common import ItemNotFoundError, generate_id
from Daneel.core.customers import CustomerStore
from Daneel.core.evaluations import EvaluationStore, EvaluationListener
from Daneel.core.utterances import UtteranceStore
from Daneel.core.relationships import RelationshipStore
from Daneel.core.guidelines import GuidelineStore
from Daneel.core.guideline_tool_associations import GuidelineToolAssociationStore
from Daneel.core.nlp.service import NLPService
from Daneel.core.services.tools.service_registry import ServiceRegistry
from Daneel.core.sessions import SessionListener, SessionStore
from Daneel.core.glossary import GlossaryStore
from Daneel.core.services.indexing.behavioral_change_evaluation import (
    BehavioralChangeEvaluator,
)
from Daneel.core.loggers import Logger
from Daneel.core.application import Application
from Daneel.core.tags import TagStore

ASGIApplication: TypeAlias = Callable[
    [
        Scope,
        Receive,
        Send,
    ],
    Awaitable[None],
]


class AppWrapper:
    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """FastAPI's built-in exception handling doesn't catch BaseExceptions
        such as asyncio.CancelledError. This causes the server process to terminate
        with an ugly traceback. This wrapper addresses that by specifically allowing
        asyncio.CancelledError to gracefully exit.
        """
        try:
            return await self.app(scope, receive, send)
        except asyncio.CancelledError:
            pass


async def create_api_app(container: Container) -> ASGIApplication:
    logger = container[Logger]
    websocket_logger = container[WebSocketLogger]
    correlator = container[ContextualCorrelator]
    agent_store = container[AgentStore]
    customer_store = container[CustomerStore]
    tag_store = container[TagStore]
    session_store = container[SessionStore]
    session_listener = container[SessionListener]
    evaluation_store = container[EvaluationStore]
    evaluation_listener = container[EvaluationListener]
    evaluation_service = container[BehavioralChangeEvaluator]
    glossary_store = container[GlossaryStore]
    guideline_store = container[GuidelineStore]
    relationship_store = container[RelationshipStore]
    guideline_tool_association_store = container[GuidelineToolAssociationStore]
    context_variable_store = container[ContextVariableStore]
    utterance_store = container[UtteranceStore]
    service_registry = container[ServiceRegistry]
    nlp_service = container[NLPService]
    application = container[Application]

    api_app = FastAPI()

    @api_app.middleware("http")
    async def handle_cancellation(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except asyncio.CancelledError:
            return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api_app.middleware("http")
    async def add_correlation_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path.startswith("/chat/"):
            return await call_next(request)

        request_id = generate_id()
        with correlator.correlation_scope(f"RID({request_id})"):
            with logger.operation(f"HTTP Request: {request.method} {request.url.path}"):
                return await call_next(request)

    @api_app.exception_handler(ItemNotFoundError)
    async def item_not_found_error_handler(
        request: Request, exc: ItemNotFoundError
    ) -> HTTPException:
        logger.info(str(exc))

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    static_dir = os.path.join(os.path.dirname(__file__), "chat/dist")
    api_app.mount("/chat", StaticFiles(directory=static_dir, html=True), name="static")

    @api_app.get("/", include_in_schema=False)
    async def root() -> Response:
        return RedirectResponse("/chat")

    agent_router = APIRouter(prefix="/agents")

    agent_router.include_router(
        guidelines.create_legacy_router(
            application=application,
            guideline_store=guideline_store,
            tag_store=tag_store,
            relationship_store=relationship_store,
            service_registry=service_registry,
            guideline_tool_association_store=guideline_tool_association_store,
        ),
    )
    agent_router.include_router(
        glossary.create_legacy_router(
            glossary_store=glossary_store,
        ),
    )
    agent_router.include_router(
        variables.create_legacy_router(
            context_variable_store=context_variable_store,
            service_registry=service_registry,
        ),
    )

    api_app.include_router(
        router=agents.create_router(
            agent_store=agent_store,
            tag_store=tag_store,
        ),
        prefix="/agents",
    )

    api_app.include_router(
        router=agent_router,
    )

    api_app.include_router(
        prefix="/sessions",
        router=sessions.create_router(
            logger=logger,
            application=application,
            agent_store=agent_store,
            customer_store=customer_store,
            session_store=session_store,
            session_listener=session_listener,
            nlp_service=nlp_service,
        ),
    )

    api_app.include_router(
        prefix="/index",
        router=index.legacy_create_router(
            evaluation_service=evaluation_service,
            evaluation_store=evaluation_store,
            evaluation_listener=evaluation_listener,
            agent_store=agent_store,
        ),
    )

    api_app.include_router(
        prefix="/services",
        router=services.create_router(
            service_registry=service_registry,
        ),
    )

    api_app.include_router(
        prefix="/tags",
        router=tags.create_router(
            tag_store=tag_store,
        ),
    )

    api_app.include_router(
        prefix="/terms",
        router=glossary.create_router(
            glossary_store=glossary_store,
            agent_store=agent_store,
            tag_store=tag_store,
        ),
    )

    api_app.include_router(
        prefix="/customers",
        router=customers.create_router(
            customer_store=customer_store,
            tag_store=tag_store,
            agent_store=agent_store,
        ),
    )

    api_app.include_router(
        prefix="/utterances",
        router=utterances.create_router(
            utterance_store=utterance_store,
            tag_store=tag_store,
        ),
    )

    api_app.include_router(
        prefix="/context-variables",
        router=variables.create_router(
            context_variable_store=context_variable_store,
            service_registry=service_registry,
            agent_store=agent_store,
            tag_store=tag_store,
        ),
    )

    api_app.include_router(
        prefix="/guidelines",
        router=guidelines.create_router(
            guideline_store=guideline_store,
            relationship_store=relationship_store,
            service_registry=service_registry,
            guideline_tool_association_store=guideline_tool_association_store,
            agent_store=agent_store,
            tag_store=tag_store,
        ),
    )

    api_app.include_router(
        prefix="/relationships",
        router=relationships.create_router(
            relationship_store=relationship_store,
            tag_store=tag_store,
            guideline_store=guideline_store,
        ),
    )

    api_app.include_router(
        router=logs.create_router(
            websocket_logger,
        )
    )

    api_app.include_router(
        router=system_stats.create_router(
            agent_store=agent_store,
            session_store=session_store,
            customer_store=customer_store,
            guideline_store=guideline_store,
        )
    )

    return AppWrapper(api_app)
