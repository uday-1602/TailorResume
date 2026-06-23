import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional

class S3Storage:
    def __init__(self):
        self.access_key = os.getenv("AWS_ACCESS_KEY")
        self.secret_key = os.getenv("AWS_SECRET_KEY")
        self.bucket_name = os.getenv("AWS_BUCKET_NAME")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        
        self.active = False
        if self.access_key and self.secret_key and self.bucket_name:
            try:
                self.client = boto3.client(
                    "s3",
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                self.active = True
                print(f"[S3] Storage initialized successfully. Target bucket: {self.bucket_name}")
            except Exception as e:
                print(f"[S3] Failed to initialize S3 client: {e}")
        else:
            print("[S3] AWS credentials or bucket name missing in .env. Falling back to local disk storage.")

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        if not self.active:
            return False
        try:
            with open(local_path, "rb") as f:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType="application/pdf"
                )
            print(f"[S3] Uploaded {local_path} to s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            print(f"[S3] Failed to upload file: {e}")
            return False

    def generate_presigned_url(self, s3_key: str, expiration: int = 900) -> str:
        if not self.active:
            raise ValueError("S3 storage client is not initialized.")
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"[S3] Failed to generate pre-signed URL: {e}")
            raise e

# Single shared instance
s3_storage = S3Storage()
