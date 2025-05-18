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

import re
from pytest_bdd import given, parsers
from parlant.core.utterances import UtteranceStore, UtteranceId, UtteranceField

from tests.core.common.engines.alpha.utils import step
from tests.core.common.utils import ContextOfTest


@step(given, parsers.parse('an utterance, "{text}"'))
def given_an_utterance(
    context: ContextOfTest,
    text: str,
) -> UtteranceId:
    utterance_store = context.container[UtteranceStore]

    utterance_field_pattern = r"\{(.*?)\}"
    field_names = re.findall(utterance_field_pattern, text)

    utterance = context.sync_await(
        utterance_store.create_utterance(
            value=text,
            fields=[
                UtteranceField(
                    name=utterance_field_name,
                    description="",
                    examples=[],
                )
                for utterance_field_name in field_names
            ],
        )
    )

    return utterance.id
