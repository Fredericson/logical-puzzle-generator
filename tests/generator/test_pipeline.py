def test_pipeline_import():
    from logical_puzzle_generator.create_puzzle import create_puzzle

    assert callable(create_puzzle)
