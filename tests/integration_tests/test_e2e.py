import pathlib

def test_upload():
    import chainmeta

    chainmeta.set_connection_string("mysql+pymysql://root:test@127.0.0.1:3306/chainmeta")

    data_folder = pathlib.Path(__file__).parent.resolve().joinpath("../data")
    resolved_input_file = data_folder.joinpath("coinbase_additional_metadata_sample.json")
    with open(resolved_input_file) as fp:
        m = chainmeta.load(fp, artifact_base_path=data_folder)
        total = chainmeta.upload_chainmeta(m["chainmetadata"]["artifact"])
        if total == 0:
            assert False, "make sure the local db is up and running"
        assert total == 21
