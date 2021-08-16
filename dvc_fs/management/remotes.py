import os
from abc import ABCMeta, abstractmethod
from typing import Optional, Dict

from dvc_fs.logs import LOGS


class DVCRemoteStorage(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def init_storage(self):
        raise Exception(
            "Operation is not supported: init_storage() invoked on abstract base class - DVCRemoteStorage"
        )

    @abstractmethod
    def remove(self) -> str:
        raise Exception(
            "Operation is not supported: remove() invoked on abstract base class - DVCRemoteStorage"
        )

    @abstractmethod
    def get_url(self) -> str:
        raise Exception(
            "Operation is not supported: get_url() invoked on abstract base class - DVCRemoteStorage"
        )

    @abstractmethod
    def get_storage_conf(self) -> Optional[Dict[str, str]]:
        raise Exception(
            "Operation is not supported: get_conf() invoked on abstract base class - DVCRemoteStorage"
        )


class DVCS3RemoteStorage(DVCRemoteStorage):
    bucket_name: str
    create_bucket: bool
    default_region: str

    def __init__(
        self,
        bucket_name: str,
        create_bucket: bool = True,
        default_region: str = "eu-central-1",
    ):
        super().__init__()
        self.bucket_name = bucket_name
        self.create_bucket = create_bucket
        self.default_region = default_region

    def init_storage(self):
        import boto3

        if self.create_bucket:
            s3 = boto3.resource("s3")
            bucket = s3.Bucket(self.bucket_name)
            if not bucket.creation_date:
                LOGS.dvc_s3_remote_storage.debug(
                    f"Create DVC S3 bucket for storage: {self.bucket_name}"
                )
                s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration=dict(
                        LocationConstraint=self.default_region,
                    ),
                )

    def get_storage_conf(self) -> Optional[Dict[str, str]]:
        conf: Dict[str, str] = dict()
        if "AWS_ACCESS_KEY_ID" in os.environ:
            conf["access_key_id"] = os.environ["AWS_ACCESS_KEY_ID"]
        if "AWS_SECRET_ACCESS_KEY" in os.environ:
            conf["secret_access_key"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        return conf

    def remove(self):
        import boto3

        s3 = boto3.resource("s3")
        bucket = s3.Bucket(self.bucket_name)
        bucket.objects.all().delete()
        bucket.delete()

    def get_url(self) -> str:
        return f"s3://{self.bucket_name}/dvc"


class DVCExternalRemoteStorage(DVCRemoteStorage):

    url: str

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def init_storage(self):
        pass

    def remove(self):
        pass

    def get_url(self) -> str:
        return self.url

    def get_storage_conf(self) -> Optional[Dict[str, str]]:
        return None

