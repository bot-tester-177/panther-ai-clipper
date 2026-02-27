import os
import sys
import tempfile
from unittest import mock

# ensure root of agent package is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from agent.storage.uploader import S3Uploader


@mock.patch("boto3.client")
def test_upload_file_success(mock_client):
    # create a temporary file to upload
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"hello")
        local_path = f.name

    os.environ["S3_BUCKET_NAME"] = "bucket"
    os.environ["AWS_ACCESS_KEY_ID"] = "key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "secret"
    os.environ["S3_ENDPOINT_URL"] = "https://example.com"

    mock_instance = mock.Mock()
    mock_client.return_value = mock_instance

    uploader = S3Uploader()
    url = uploader.upload_file(local_path, key="test.mp4")

    mock_instance.upload_file.assert_called_once_with(local_path, "bucket", "test.mp4")
    assert url.endswith("bucket/test.mp4")


def test_missing_bucket():
    # bucket name required
    if "S3_BUCKET_NAME" in os.environ:
        del os.environ["S3_BUCKET_NAME"]
    with pytest.raises(ValueError):
        S3Uploader()
