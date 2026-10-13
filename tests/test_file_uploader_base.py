"""``FileUploaderBase.clear_after_submit``: clear the uploader after a submit, by default
(i2mint/front#24)."""

from dataclasses import fields

from front.elements import FileUploaderBase


def test_clear_after_submit_is_on_by_default():
    field = {f.name: f for f in fields(FileUploaderBase)}["clear_after_submit"]
    assert field.default is True
