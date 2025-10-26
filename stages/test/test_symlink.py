#!/usr/bin/python3

import os
import pytest

from osbuild import testutil

STAGE_NAME = "org.osbuild.symlink"


@pytest.mark.parametrize("test_data,expected_err", [
    # bad
    ({}, "'paths' is a required property"),
    ({"paths": "not-an-array"}, "'not-an-array' is not of type 'array'"),
    ({"paths": [{}]}, "'source' is a required property"),
    ({"paths": [{"source": "a"}]}, "'link' is a required property"),
    ({"paths": [{"link": "b"}]}, "'source' is a required property"),
    ({"paths": [{"source": "a", "link": "b", "extra": "c"}]}, "Additional properties are not allowed ('extra' was unexpected)"),
    # good
    ({"paths": []}, ""),
    ({"paths": [{"source": "a", "link": "b"}]}, ""),
])
def test_schema_validation(stage_schema, test_data, expected_err):
    test_input = {
        "type": STAGE_NAME,
        "options": {},
    }
    test_input["options"].update(test_data)
    res = stage_schema.validate(test_input)

    if expected_err == "":
        assert res.valid is True, f"err: {[e.as_dict() for e in res.errors]}"
    else:
        assert res.valid is False
        testutil.assert_jsonschema_error_contains(res, expected_err, expected_num_errs=1)


def test_symlink_integration(tmp_path, stage_module):
    tree = tmp_path

    # Create a target for the symlink
    target_path = tree / "target"
    target_path.touch()

    options = {
        "paths": [
            {
                "source": "target",
                "link": "tree:///link_to_target"
            },
            {
                "source": "/etc/os-release",
                "link": "tree:///abs_link"
            },
            {
                "source": "relative_target",
                "link": "relative_link"
            }
        ]
    }

    args = {
        "tree": os.fspath(tree),
    }

    stage_module.main(args, options)

    link_path = tree / "link_to_target"
    assert link_path.is_symlink()
    assert os.readlink(link_path) == "target"

    abs_link_path = tree / "abs_link"
    assert abs_link_path.is_symlink()
    assert os.readlink(abs_link_path) == "/etc/os-release"

    relative_link_path = tree / "relative_link"
    assert relative_link_path.is_symlink()
    assert os.readlink(relative_link_path) == "relative_target"