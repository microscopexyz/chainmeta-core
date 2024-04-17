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
from pathlib import Path
from typing import Dict, Optional, Union, no_type_check

import boto3

file_prefix = "file:///"
s3_prefix = "s3://"


def local_loader(uri: str, *, base_path: Union[str, Path, None] = None) -> str:
    if not base_path:
        raise ValueError("missing artifact base path for local artifact file")

    base_path = Path(base_path)
    relative_path = uri[len(file_prefix) :]
    resolved_path = base_path.joinpath(relative_path)
    with open(resolved_path) as f:
        return f.read()


@no_type_check
def s3_loader(uri: str, **kw) -> str:
    s3_client = boto3.client("s3")
    bucket, key = uri[5:].split("/", 1)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    return content


@no_type_check
def http_loader(uri: str, **kw) -> str:
    pass


def json_parser(c: str) -> object:
    return json.loads(c)


def csv_parser(c: str) -> object:
    meta_data = []
    try:
        # first line is header, the separator between fields is '\t'
        rows = c.split("\n")
        filed_names = rows[0].split("\t")
        for i in range(1, len(rows)):
            row = rows[i]
            if not row:
                continue
            dic: Dict[str, Optional[str]] = {}
            arr = row.split("\t")
            for j in range(0, len(filed_names)):
                if arr[j] == "":
                    dic[filed_names[j]] = None
                else:
                    dic[filed_names[j]] = arr[j]
            meta_data.append(dic)
        return meta_data
    finally:
        return meta_data


parsers = {
    "json": json_parser,
    "JSON": json_parser,
    "csv": csv_parser,
    "CSV": csv_parser,
}


def load(
    uri: str, fileformat: str, *, base_path: Union[str, Path, None] = None
) -> object:
    loader = None
    if uri.startswith(file_prefix):
        loader = local_loader
    if uri.startswith(s3_prefix):
        loader = s3_loader
    parser = parsers.get(fileformat)
    if loader and parser:
        return parser(loader(uri, base_path=base_path))
    raise ValueError("unsupported artifact type")
