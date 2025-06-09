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
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any, AsyncIterator, cast
from fastapi import FastAPI
import httpx
from lagom import Container, Singleton
from pytest import fixture, Config
import pytest

from Daneel.adapters.loggers.websocket import WebSocketLogger
from Daneel.adapters.nlp.openai_service import OpenAIService
from Daneel.adapters.vector_db.transient import TransientVectorDatabase
from Daneel.api.app import create_api_app, ASGIApplication
from Daneel.core.background_tasks import BackgroundTaskService
from Daneel.core.contextual_correlator import ContextualCorrelator
from Daneel.core.context_variables import ContextVariableDocumentStore, ContextVariableStore
from Daneel.core.emission.event_publisher import EventPublisherFactory
from Daneel.core.emissions import EventEmitterFactory
from Daneel.core.customers import CustomerDocumentStore, CustomerStore
from Daneel.core.engines.alpha import guideline_matcher
from Daneel.core.engines.alpha import tool_caller
from Daneel.core.engines.alpha import message_generator
from Daneel.core.engines.alpha.hooks import EngineHooks
from Daneel.core.engines.alpha.relational_guideline_resolver import RelationalGuidelineResolver
from Daneel.core.engines.alpha.utterance_selector import (
    UtteranceFieldExtractionSchema,
    UtteranceFieldExtractor,
    UtteranceSelector,
    UtteranceSelectionSchema,
    UtteranceCompositionSchema,
)
from Daneel.core.evaluations import (
    EvaluationListener,
    PollingEvaluationListener,
    EvaluationDocumentStore,
    EvaluationStore,
)
from Daneel.core.utterances import UtteranceDocumentStore, UtteranceStore
from Daneel.core.nlp.embedding import EmbedderFactory
from Daneel.core.nlp.generation import T, SchematicGenerator
from Daneel.core.relationships import (
    RelationshipDocumentStore,
    RelationshipStore,
)
from Daneel.core.guidelines import GuidelineDocumentStore, GuidelineStore
from Daneel.adapters.db.transient import TransientDocumentDatabase
from Daneel.core.nlp.service import NLPService
from Daneel.core.persistence.document_database import DocumentCollection
from Daneel.core.services.tools.service_registry import (
    ServiceDocumentRegistry,
    ServiceRegistry,
)
from Daneel.core.sessions import (
    PollingSessionListener,
    SessionDocumentStore,
    SessionListener,
    SessionStore,
)
from Daneel.core.engines.alpha.engine import AlphaEngine
from Daneel.core.glossary import GlossaryStore, GlossaryVectorStore
from Daneel.core.engines.alpha.guideline_matcher import (
    GuidelineMatcher,
    GenericGuidelineMatchingShot,
    GenericGuidelineMatchesSchema,
    GenericGuidelineMatching,
    DefaultGuidelineMatchingStrategyResolver,
    GuidelineMatchingStrategyResolver,
)
from Daneel.core.engines.alpha.message_generator import (
    MessageGenerator,
    MessageGeneratorShot,
    MessageSchema,
)
from Daneel.core.engines.alpha.tool_caller import ToolCallInferenceSchema, ToolCallerInferenceShot
from Daneel.core.engines.alpha.tool_event_generator import ToolEventGenerator
from Daneel.core.engines.types import Engine
from Daneel.core.services.indexing.behavioral_change_evaluation import (
    BehavioralChangeEvaluator,
)
from Daneel.core.services.indexing.coherence_checker import (
    CoherenceChecker,
    ConditionsEntailmentTestsSchema,
    ActionsContradictionTestsSchema,
)
from Daneel.core.services.indexing.guideline_connection_proposer import (
    GuidelineConnectionProposer,
    GuidelineConnectionPropositionsSchema,
)
from Daneel.core.loggers import LogLevel, Logger, StdoutLogger
from Daneel.core.application import Application
from Daneel.core.agents import AgentDocumentStore, AgentStore
from Daneel.core.guideline_tool_associations import (
    GuidelineToolAssociationDocumentStore,
    GuidelineToolAssociationStore,
)
from Daneel.core.shots import ShotCollection
from Daneel.core.entity_cq import EntityQueries, EntityCommands
from Daneel.core.tags import TagDocumentStore, TagStore
from Daneel.core.tools import LocalToolService

from .test_utilities import (
    CachedSchematicGenerator,
    JournalingEngineHooks,
    SchematicGenerationResultDocument,
    SyncAwaiter,
    create_schematic_generation_result_collection,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("caching")

    group.addoption(
        "--no-cache",
        action="store_true",
        dest="no_cache",
        default=False,
        help="Whether to avoid using the cache during the current test suite",
    )


@fixture
def correlator() -> ContextualCorrelator:
    return ContextualCorrelator()


@fixture
def logger(correlator: ContextualCorrelator) -> Logger:
    return StdoutLogger(correlator=correlator, log_level=LogLevel.INFO)


@dataclass(frozen=True)
class CacheOptions:
    cache_enabled: bool
    cache_collection: DocumentCollection[SchematicGenerationResultDocument] | None


@fixture
async def cache_options(
    request: pytest.FixtureRequest,
    logger: Logger,
) -> AsyncIterator[CacheOptions]:
    if not request.config.getoption("no_cache", True):
        logger.warning("*** Cache is enabled")
        async with create_schematic_generation_result_collection(logger=logger) as collection:
            yield CacheOptions(cache_enabled=True, cache_collection=collection)
    else:
        yield CacheOptions(cache_enabled=False, cache_collection=None)


@fixture
async def sync_await() -> SyncAwaiter:
    return SyncAwaiter(asyncio.get_event_loop())


@fixture
def test_config(pytestconfig: Config) -> dict[str, Any]:
    return {"patience": 10}


async def make_schematic_generator(
    container: Container,
    cache_options: CacheOptions,
    schema: type[T],
) -> SchematicGenerator[T]:
    base_generator = await container[NLPService].get_schematic_generator(schema)

    if cache_options.cache_enabled:
        assert cache_options.cache_collection

        return CachedSchematicGenerator[T](
            base_generator=base_generator,
            collection=cache_options.cache_collection,
            use_cache=True,
        )
    else:
        return base_generator


@fixture
async def container(
    correlator: ContextualCorrelator,
    logger: Logger,
    cache_options: CacheOptions,
) -> AsyncIterator[Container]:
    container = Container()

    container[ContextualCorrelator] = correlator
    container[Logger] = logger
    container[WebSocketLogger] = WebSocketLogger(container[ContextualCorrelator])

    async with AsyncExitStack() as stack:
        container[BackgroundTaskService] = await stack.enter_async_context(
            BackgroundTaskService(container[Logger])
        )

        await container[BackgroundTaskService].start(
            container[WebSocketLogger].start(), tag="websocket-logger"
        )

        container[AgentStore] = await stack.enter_async_context(
            AgentDocumentStore(TransientDocumentDatabase())
        )
        container[GuidelineStore] = await stack.enter_async_context(
            GuidelineDocumentStore(TransientDocumentDatabase())
        )
        container[RelationshipStore] = await stack.enter_async_context(
            RelationshipDocumentStore(TransientDocumentDatabase())
        )
        container[SessionStore] = await stack.enter_async_context(
            SessionDocumentStore(TransientDocumentDatabase())
        )
        container[ContextVariableStore] = await stack.enter_async_context(
            ContextVariableDocumentStore(TransientDocumentDatabase())
        )
        container[TagStore] = await stack.enter_async_context(
            TagDocumentStore(TransientDocumentDatabase())
        )
        container[CustomerStore] = await stack.enter_async_context(
            CustomerDocumentStore(TransientDocumentDatabase())
        )
        container[UtteranceStore] = await stack.enter_async_context(
            UtteranceDocumentStore(TransientDocumentDatabase())
        )
        container[GuidelineToolAssociationStore] = await stack.enter_async_context(
            GuidelineToolAssociationDocumentStore(TransientDocumentDatabase())
        )
        container[SessionListener] = PollingSessionListener
        container[EvaluationStore] = await stack.enter_async_context(
            EvaluationDocumentStore(TransientDocumentDatabase())
        )
        container[EvaluationListener] = PollingEvaluationListener
        container[BehavioralChangeEvaluator] = BehavioralChangeEvaluator
        container[EventEmitterFactory] = Singleton(EventPublisherFactory)

        container[ServiceRegistry] = await stack.enter_async_context(
            ServiceDocumentRegistry(
                database=TransientDocumentDatabase(),
                event_emitter_factory=container[EventEmitterFactory],
                logger=container[Logger],
                correlator=container[ContextualCorrelator],
                nlp_services={"default": OpenAIService(container[Logger])},
            )
        )

        container[NLPService] = await container[ServiceRegistry].read_nlp_service("default")

        embedder_type = type(await container[NLPService].get_embedder())
        embedder_factory = EmbedderFactory(container)
        container[GlossaryStore] = await stack.enter_async_context(
            GlossaryVectorStore(
                vector_db=await stack.enter_async_context(
                    TransientVectorDatabase(container[Logger], embedder_factory)
                ),
                document_db=TransientDocumentDatabase(),
                embedder_factory=embedder_factory,
                embedder_type=embedder_type,
            )
        )

        container[EntityQueries] = Singleton(EntityQueries)
        container[EntityCommands] = Singleton(EntityCommands)
        for generation_schema in (
            GenericGuidelineMatchesSchema,
            MessageSchema,
            UtteranceSelectionSchema,
            UtteranceCompositionSchema,
            UtteranceFieldExtractionSchema,
            ToolCallInferenceSchema,
            ConditionsEntailmentTestsSchema,
            ActionsContradictionTestsSchema,
            GuidelineConnectionPropositionsSchema,
        ):
            container[SchematicGenerator[generation_schema]] = await make_schematic_generator(  # type: ignore
                container,
                cache_options,
                generation_schema,
            )

        container[ShotCollection[GenericGuidelineMatchingShot]] = guideline_matcher.shot_collection
        container[ShotCollection[ToolCallerInferenceShot]] = tool_caller.shot_collection
        container[ShotCollection[MessageGeneratorShot]] = message_generator.shot_collection

        container[GuidelineConnectionProposer] = Singleton(GuidelineConnectionProposer)
        container[CoherenceChecker] = Singleton(CoherenceChecker)

        container[LocalToolService] = cast(
            LocalToolService,
            await container[ServiceRegistry].update_tool_service(
                name="local", kind="local", url=""
            ),
        )
        container[DefaultGuidelineMatchingStrategyResolver] = Singleton(
            DefaultGuidelineMatchingStrategyResolver
        )
        container[GuidelineMatchingStrategyResolver] = lambda container: container[
            DefaultGuidelineMatchingStrategyResolver
        ]
        container[GenericGuidelineMatching] = Singleton(GenericGuidelineMatching)
        container[GuidelineMatcher] = Singleton(GuidelineMatcher)
        container[RelationalGuidelineResolver] = Singleton(RelationalGuidelineResolver)
        container[UtteranceSelector] = Singleton(UtteranceSelector)
        container[UtteranceFieldExtractor] = Singleton(UtteranceFieldExtractor)
        container[MessageGenerator] = Singleton(MessageGenerator)
        container[ToolEventGenerator] = Singleton(ToolEventGenerator)

        hooks = JournalingEngineHooks()
        container[JournalingEngineHooks] = hooks
        container[EngineHooks] = hooks

        container[Engine] = Singleton(AlphaEngine)

        container[Application] = Application(container)

        yield container

        await container[BackgroundTaskService].cancel_all()


@fixture
async def api_app(container: Container) -> ASGIApplication:
    return await create_api_app(container)


@fixture
async def async_client(api_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://testserver",
    ) as client:
        yield client


class NoCachedGenerations:
    pass


@fixture
def no_cache(container: Container) -> None:
    if isinstance(
        container[SchematicGenerator[GenericGuidelineMatchesSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[GenericGuidelineMatchesSchema],
            container[SchematicGenerator[GenericGuidelineMatchesSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[MessageSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[MessageSchema],
            container[SchematicGenerator[MessageSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[UtteranceSelectionSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[UtteranceSelectionSchema],
            container[SchematicGenerator[UtteranceSelectionSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[UtteranceCompositionSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[UtteranceCompositionSchema],
            container[SchematicGenerator[UtteranceCompositionSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[UtteranceFieldExtractionSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[UtteranceFieldExtractionSchema],
            container[SchematicGenerator[UtteranceFieldExtractionSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[ToolCallInferenceSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[ToolCallInferenceSchema],
            container[SchematicGenerator[ToolCallInferenceSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[ConditionsEntailmentTestsSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[ConditionsEntailmentTestsSchema],
            container[SchematicGenerator[ConditionsEntailmentTestsSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[ActionsContradictionTestsSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[ActionsContradictionTestsSchema],
            container[SchematicGenerator[ActionsContradictionTestsSchema]],
        ).use_cache = False

    if isinstance(
        container[SchematicGenerator[GuidelineConnectionPropositionsSchema]],
        CachedSchematicGenerator,
    ):
        cast(
            CachedSchematicGenerator[GuidelineConnectionPropositionsSchema],
            container[SchematicGenerator[GuidelineConnectionPropositionsSchema]],
        ).use_cache = False
