import os
import logging

import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3Uploader:
    """Uploads files to an S3-compatible bucket.

    Configuration is read from environment variables:

    * AWS_ACCESS_KEY_ID
    * AWS_SECRET_ACCESS_KEY
    * S3_BUCKET_NAME
    * S3_ENDPOINT_URL (optional, for R2 or other compatible services)
    """

    def __init__(self):
        self.bucket = os.getenv("S3_BUCKET_NAME")
        if not self.bucket:
            raise ValueError("S3_BUCKET_NAME must be set in environment")

        # endpoint can be None; boto3 will default to AWS
        self.endpoint = os.getenv("S3_ENDPOINT_URL")

        # boto3 will pick up access key and secret from the environment
        try:
            self.client = boto3.client("s3", endpoint_url=self.endpoint)
        except (BotoCoreError, NoCredentialsError) as exc:
            logger.error("failed to create S3 client: %s", exc)
            raise

    def upload_file(self, file_path: str, key: str | None = None) -> str:
        """Upload a local file and return the public URL.

        If *key* is omitted, the basename of *file_path* is used as the object
        key.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"source file does not exist: {file_path}")

        if key is None:
            key = os.path.basename(file_path)

        try:
            self.client.upload_file(file_path, self.bucket, key)
        except Exception as exc:
            logger.error("upload to bucket %s failed: %s", self.bucket, exc)
            raise

        return self._build_url(key)

    def _build_url(self, key: str) -> str:
        # For a custom endpoint we simply concatenate; users can customise via
        # environment variable.
        if self.endpoint:
            ep = self.endpoint.rstrip("/")
            return f"{ep}/{self.bucket}/{key}"
        # default AWS URL
        return f"https://{self.bucket}.s3.amazonaws.com/{key}"
