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

"""Local model adapters for Parlant."""

from parlant.adapters.nlp.local.llama import LlamaService
from parlant.adapters.nlp.local.deepseek import DeepSeekService
from parlant.adapters.nlp.local.model_manager import LocalModelManager

__all__ = ["LlamaService", "DeepSeekService", "LocalModelManager"]
