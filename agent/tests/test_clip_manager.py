import os
import sys
import tempfile
import time
from unittest import mock

# make sure the agent package can be imported (add repo root to path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from agent.clip_manager import ClipManager


def test_get_latest_clip(tmp_path):
    # clip manager will try to instantiate an uploader during __init__, so
    # satisfy its environment requirement even though we won't actually
    # upload anything for this test.
    os.environ["S3_BUCKET_NAME"] = "dummy"

    # create a couple of dummy files with different modification times
    file1 = tmp_path / "a.mp4"
    file1.write_text("foo")
    time.sleep(0.01)
    file2 = tmp_path / "b.mp4"
    file2.write_text("bar")

    mgr = ClipManager(watch_dir=str(tmp_path))
    latest = mgr.get_latest_clip()
    assert latest.endswith("b.mp4")

    del os.environ["S3_BUCKET_NAME"]


@mock.patch("agent.clip_manager.S3Uploader")
def test_process_clip(mock_uploader_class, tmp_path):
    os.environ["S3_BUCKET_NAME"] = "bucket"
    os.environ["AWS_ACCESS_KEY_ID"] = "key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "secret"
    os.environ["S3_ENDPOINT_URL"] = "https://example.com"

    file = tmp_path / "clip.mp4"
    file.write_text("data")

    mock_uploader = mock.Mock()
    mock_uploader.upload_file.return_value = "https://example.com/bucket/clip.mp4"
    mock_uploader_class.return_value = mock_uploader

    mgr = ClipManager(watch_dir=str(tmp_path))
    # bypass socket connection
    mgr._sio = mock.Mock(connected=False)
    metadata = mgr.process_clip(str(file), hype_score=42)

    assert metadata["fileName"] == "clip.mp4"
    assert metadata["url"].endswith("clip.mp4")
    assert metadata["hypeScore"] == 42
