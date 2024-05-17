# Copyright 2023 The chainmetareader Authors. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
from abc import ABC
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChainmetaItem:
    """ChainmetaItem is the common schema for all chain metadata items.
    Reference: /chainmeta/schema/artifact_schema.json
    """

    # Chain identification
    chain: str

    # Wallet or contract address
    address: str

    # Entity id of the address
    entity: Optional[str]

    # name of the address
    name: Optional[str]

    # Category ids of the address
    categories: List[str]

    # Source of the metadata
    source: str

    # Submitter of the metadata
    submitted_by: str

    # Last updated time
    submitted_on: str

    # Additional metadata
    additional_metadata: dict

    def __post_init__(self):
        if isinstance(self.categories, str):
            if not self.categories:
                self.categories = []
            else:
                self.categories = ast.literal_eval(self.categories)

        if isinstance(self.additional_metadata, str):
            if not self.additional_metadata:
                self.additional_metadata = {}
            else:
                print(self.additional_metadata)
                self.additional_metadata = ast.literal_eval(self.additional_metadata)


class ITranslator(ABC):
    def to_common_schema(self, raw_metadata) -> Optional[ChainmetaItem]:
        pass

    def from_common_schema(
        self, common_schema_metadata: ChainmetaItem
    ) -> Optional[object]:
        pass


class Translator(ITranslator):
    def to_common_schema(self, raw_metadata) -> Optional[ChainmetaItem]:
        if "additional_metadata" not in raw_metadata:
            raw_metadata["additional_metadata"] = {}
        return ChainmetaItem(**raw_metadata)

    def from_common_schema(
        self, common_schema_metadata: ChainmetaItem
    ) -> Optional[object]:
        return common_schema_metadata.__dict__
