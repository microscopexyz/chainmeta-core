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
import json
import os
from pathlib import Path
from typing import Optional, Union

from chainmeta.artifact import load as artifact_load
from chainmeta.db import init_db
from chainmeta.db import search_chainmeta as search_chainmeta
from chainmeta.db import upload_chainmeta
from chainmeta.schema import Schema, common_schema
from chainmeta.schema import resolve as schema_resolve
from chainmeta.validator import common_artifact_validator, common_metadata_validator


def set_connection_string(connection_string: Optional[str] = None):
    if not connection_string:
        connection_string = os.environ.get("CHAINMETA_DB_CONN")

    if connection_string:
        init_db(connection_string)


def validate(
    fp, *, ignore_unrecognized=True, artifact_base_path: Union[str, Path, None], **kw
):
    """Validate ``fp`` (a ``.read()``-supporting file-like object containing
    an open chain metadata document) against the open chain metadata rule set.
    """

    validates(
        fp.read(),
        ignore_unrecognized=ignore_unrecognized,
        artifact_base_path=artifact_base_path,
    )


def validates(
    s: str,
    *,
    ignore_unrecognized=True,
    artifact_base_path: Union[str, Path, None],
    **kw,
):
    """Validate ``s`` (a ``str``, ``bytes`` or ``bytearray`` instance containing
    an open chain metadata document) against the open chain metadata rule set.
    """

    metadata = json.loads(s)

    # Global validation
    common_metadata_validator.validate(metadata)
    raw_schema = metadata["chainmetadata"]["schema"]
    artifacts = metadata["chainmetadata"]["artifact"]

    # Artifact validation
    schema = schema_resolve(raw_schema)

    if not schema and not ignore_unrecognized:
        raise ValueError(f"schema {raw_schema} not registered")
    if not schema:
        return metadata

    loaded_artifacts: list = []

    base_path: Optional[Path] = Path(artifact_base_path) if artifact_base_path else None
    for artifact in artifacts:
        loaded_artifact = artifact_load(
            artifact["path"],
            fileformat=artifact["fileformat"],
            base_path=base_path,
        )
        schema.validator.validate(loaded_artifact)
        if isinstance(loaded_artifact, list):
            loaded_artifacts += loaded_artifact
    metadata["chainmetadata"]["raw_artifact"] = loaded_artifacts
    common_schema = [schema.translator.to_common_schema(a) for a in loaded_artifacts]
    common_artifact_validator.validate([c.__dict__ for c in common_schema])
    metadata["chainmetadata"]["artifact"] = common_schema

    return metadata


def load(
    fp, *, ignore_unrecognized=True, artifact_base_path: Union[str, Path, None], **kw
):
    """Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    an open chain metadata document) to a Python object.
    """

    return loads(
        fp.read(),
        ignore_unrecognized=ignore_unrecognized,
        artifact_base_path=artifact_base_path,
        **kw,
    )


def loads(
    s: str,
    *,
    ignore_unrecognized=True,
    artifact_base_path: Union[str, Path, None],
    **kw,
):
    """Deserialize ``s`` (a ``str``, ``bytes`` or ``bytearray`` instance containing
    an open chain metadata document) to a Python object.
    """
    return validates(
        s,
        ignore_unrecognized=ignore_unrecognized,
        artifact_base_path=artifact_base_path,
        **kw,
    )


def load_artifact(
    uri: str,
    *,
    schema: Schema = common_schema,
    artifact_base_path: Union[str, Path, None] = None,
    **kw,
):
    fileformat = uri.split(".")[-1].lower()
    if artifact_base_path:
        artifact_base_path = Path(artifact_base_path)
    loaded_artifact = artifact_load(
        uri, fileformat=fileformat, base_path=artifact_base_path
    )
    if not isinstance(loaded_artifact, list):
        raise ValueError("artifact must be a list")
    schema.validator.validate(loaded_artifact)
    common_schema = [schema.translator.to_common_schema(a) for a in loaded_artifact]
    common_artifact_validator.validate([c.__dict__ for c in common_schema])
    return common_schema


set_connection_string()

__all__ = [
    "validate",
    "validates",
    "load",
    "loads",
    "load_artifact",
    "upload_chainmeta",
    "search_chainmeta",
    "set_connection_string",
]
