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

"""Code-related UI components for Daneel."""

from Daneel.ui.components.code.code_block import CodeBlock, CodeBlockOptions
from Daneel.ui.components.code.diff_viewer import DiffViewer, DiffViewerOptions, DiffMode

__all__ = [
    "CodeBlock",
    "CodeBlockOptions",
    "DiffViewer",
    "DiffViewerOptions",
    "DiffMode",
]
