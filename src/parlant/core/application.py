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

from __future__ import annotations
import asyncio
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Optional, TypeAlias, cast
from lagom import Container

from Daneel.core.async_utils import Timeout
from Daneel.core.background_tasks import BackgroundTaskService
from Daneel.core.common import generate_id
from Daneel.core.contextual_correlator import ContextualCorrelator
from Daneel.core.agents import AgentId
from Daneel.core.emissions import EventEmitterFactory
from Daneel.core.customers import CustomerId
from Daneel.core.evaluations import (
    EntailmentRelationshipProposition,
    EntailmentRelationshipPropositionKind,
    GuidelinePayloadOperation,
    Invoice,
)
from Daneel.core.relationships import (
    EntityType,
    GuidelineRelationshipKind,
    RelationshipStore,
)
from Daneel.core.guidelines import GuidelineId, GuidelineStore
from Daneel.core.sessions import (
    Event,
    EventKind,
    EventSource,
    Session,
    SessionId,
    SessionListener,
    SessionStore,
)
from Daneel.core.engines.types import Context, Engine, UtteranceRequest
from Daneel.core.loggers import Logger


TaskQueue: TypeAlias = list[asyncio.Task[None]]


class Application:
    def __init__(self, container: Container) -> None:
        self._logger = container[Logger]
        self._correlator = container[ContextualCorrelator]
        self._session_store = container[SessionStore]
        self._session_listener = container[SessionListener]
        self._guideline_store = container[GuidelineStore]
        self._relationship_store = container[RelationshipStore]
        self._engine = container[Engine]
        self._event_emitter_factory = container[EventEmitterFactory]
        self._background_task_service = container[BackgroundTaskService]

        self._lock = asyncio.Lock()

    async def wait_for_update(
        self,
        session_id: SessionId,
        min_offset: int,
        kinds: Sequence[EventKind] = [],
        source: Optional[EventSource] = None,
        timeout: Timeout = Timeout.infinite(),
    ) -> bool:
        return await self._session_listener.wait_for_events(
            session_id=session_id,
            min_offset=min_offset,
            kinds=kinds,
            source=source,
            timeout=timeout,
        )

    async def create_customer_session(
        self,
        customer_id: CustomerId,
        agent_id: AgentId,
        title: Optional[str] = None,
        allow_greeting: bool = False,
    ) -> Session:
        session = await self._session_store.create_session(
            creation_utc=datetime.now(timezone.utc),
            customer_id=customer_id,
            agent_id=agent_id,
            title=title,
        )

        if allow_greeting:
            await self.dispatch_processing_task(session)

        return session

    async def post_event(
        self,
        session_id: SessionId,
        kind: EventKind,
        data: Mapping[str, Any],
        source: EventSource = EventSource.CUSTOMER,
        trigger_processing: bool = True,
    ) -> Event:
        event = await self._session_store.create_event(
            session_id=session_id,
            source=source,
            kind=kind,
            correlation_id=self._correlator.correlation_id,
            data=data,
        )

        if trigger_processing:
            session = await self._session_store.read_session(session_id)
            await self.dispatch_processing_task(session)

        return event

    async def dispatch_processing_task(self, session: Session) -> str:
        with self._correlator.correlation_scope(generate_id()):
            await self._background_task_service.restart(
                self._process_session(session),
                tag=f"process-session({session.id})",
            )

            return self._correlator.correlation_id

    async def _process_session(self, session: Session) -> None:
        event_emitter = await self._event_emitter_factory.create_event_emitter(
            emitting_agent_id=session.agent_id,
            session_id=session.id,
        )

        await self._engine.process(
            Context(
                session_id=session.id,
                agent_id=session.agent_id,
            ),
            event_emitter=event_emitter,
        )

    async def utter(
        self,
        session: Session,
        requests: Sequence[UtteranceRequest],
    ) -> str:
        with self._correlator.correlation_scope(generate_id()):
            event_emitter = await self._event_emitter_factory.create_event_emitter(
                emitting_agent_id=session.agent_id,
                session_id=session.id,
            )

            await self._engine.utter(
                context=Context(session_id=session.id, agent_id=session.agent_id),
                event_emitter=event_emitter,
                requests=requests,
            )

            return self._correlator.correlation_id

    async def create_guidelines(
        self,
        invoices: Sequence[Invoice],
    ) -> Iterable[GuidelineId]:
        async def _create_with_existing_guideline(
            source_key: str,
            target_key: str,
            content_guidelines: dict[str, GuidelineId],
            proposition: EntailmentRelationshipProposition,
        ) -> None:
            if source_key in content_guidelines:
                source_guideline_id = content_guidelines[source_key]
                target_guideline_id = (
                    await self._guideline_store.find_guideline(
                        guideline_content=proposition.target,
                    )
                ).id
            else:
                source_guideline_id = (
                    await self._guideline_store.find_guideline(
                        guideline_content=proposition.source,
                    )
                ).id
                target_guideline_id = content_guidelines[target_key]

            await self._relationship_store.create_relationship(
                source=source_guideline_id,
                source_type=EntityType.GUIDELINE,
                target=target_guideline_id,
                target_type=EntityType.GUIDELINE,
                kind=GuidelineRelationshipKind.ENTAILMENT,
            )

        content_guidelines: dict[str, GuidelineId] = {
            f"{invoice.payload.content.condition}_{invoice.payload.content.action}": (
                await self._guideline_store.create_guideline(
                    condition=invoice.payload.content.condition,
                    action=invoice.payload.content.action,
                )
                if invoice.payload.operation == GuidelinePayloadOperation.ADD
                else await self._guideline_store.update_guideline(
                    guideline_id=cast(GuidelineId, invoice.payload.updated_id),
                    params={
                        "condition": invoice.payload.content.condition,
                        "action": invoice.payload.content.action,
                    },
                )
            ).id
            for invoice in invoices
        }

        for invoice in invoices:
            if (
                invoice.payload.operation == GuidelinePayloadOperation.UPDATE
                and invoice.payload.connection_proposition
            ):
                guideline_id = cast(GuidelineId, invoice.payload.updated_id)

                relationships_to_delete = list(
                    await self._relationship_store.list_relationships(
                        kind=GuidelineRelationshipKind.ENTAILMENT,
                        indirect=False,
                        source=guideline_id,
                    )
                )

                relationships_to_delete.extend(
                    await self._relationship_store.list_relationships(
                        kind=GuidelineRelationshipKind.ENTAILMENT,
                        indirect=False,
                        target=guideline_id,
                    )
                )

                for relationship in relationships_to_delete:
                    await self._relationship_store.delete_relationship(relationship.id)

        entailment_propositions: set[EntailmentRelationshipProposition] = set([])

        for invoice in invoices:
            assert invoice.data

            if not invoice.data.entailment_propositions:
                continue

            for proposition in invoice.data.entailment_propositions:
                source_key = f"{proposition.source.condition}_{proposition.source.action}"
                target_key = f"{proposition.target.condition}_{proposition.target.action}"

                if proposition not in entailment_propositions:
                    if (
                        proposition.check_kind
                        == EntailmentRelationshipPropositionKind.CONNECTION_WITH_ANOTHER_EVALUATED_GUIDELINE
                    ):
                        await self._relationship_store.create_relationship(
                            source=content_guidelines[source_key],
                            source_type=EntityType.GUIDELINE,
                            target=content_guidelines[target_key],
                            target_type=EntityType.GUIDELINE,
                            kind=GuidelineRelationshipKind.ENTAILMENT,
                        )
                    else:
                        await _create_with_existing_guideline(
                            source_key,
                            target_key,
                            content_guidelines,
                            proposition,
                        )
                    entailment_propositions.add(proposition)

        return content_guidelines.values()
