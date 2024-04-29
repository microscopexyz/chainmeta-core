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

import pathlib


def test_upload():
    import chainmeta

    chainmeta.set_connection_string(
        "mysql+pymysql://root:test@127.0.0.1:3306/chainmeta"
    )

    data_folder = pathlib.Path(__file__).parent.resolve().joinpath("../data")
    resolved_input_file = data_folder.joinpath(
        "coinbase_additional_metadata_sample.json"
    )
    with open(resolved_input_file) as fp:
        m = chainmeta.load(fp, artifact_base_path=data_folder)
        total = chainmeta.upload_chainmeta(m["chainmetadata"]["artifact"])
        if total == 0:
            assert False, "make sure the local db is up and running"
        assert total == 21


def test_upload_flattened():
    import csv

    import chainmeta
    from chainmeta.db import ChainmetaRecord

    chainmeta.set_connection_string(
        "mysql+pymysql://root:test@127.0.0.1:3306/chainmeta"
    )

    flattened_file = (
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../data/artifacts/coinbase_sample_flattened.csv")
    )
    with open(flattened_file) as f:
        reader = csv.DictReader(f)
        data = [ChainmetaRecord(**r) for r in reader]

        total = chainmeta.upload_chainmeta(data)
        if total == 0:
            assert False, "make sure the local db is up and running"
        assert total == 5
