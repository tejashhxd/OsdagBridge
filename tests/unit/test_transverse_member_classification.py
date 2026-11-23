def test_classify_member_tags_separates_longitudinal_and_transverse_elements():
    from osdagbridge.core.bridge_types.plate_girder.results_data import (
        classify_member_tags,
    )

    nodes = {
        1: [0.0, 0.0, 0.0],
        2: [5.0, 0.0, 0.0],
        3: [0.0, 0.0, 2.0],
        4: [5.0, 0.0, 2.0],
        5: [1.0, 0.0, 0.0],
        6: [1.0, 0.0, 3.0],
        7: [2.0, 0.0, 1.0],
        8: [2.0, 1.0, 1.0],
    }
    members = {
        11: [1, 2],
        12: [3, 4],
        21: [5, 6],
        31: [7, 8],
        41: [1, 999],
        51: [1, 2, 3],
    }

    assert classify_member_tags(nodes, members) == ([11, 12], [21])
