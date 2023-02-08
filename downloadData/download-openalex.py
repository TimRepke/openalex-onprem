import os
import re
import json
import boto3
import local.config as conf


class OpenAlex:

    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket = "openalex"
        self.root_save_path = f"{conf.links.local_root}/openalex/"

    def read_s3_contents(self, prefix):
        bucket = self.bucket
        response = self.s3_client.get_object(Bucket=bucket, Key=prefix)
        return response['Body'].read()

    def get_manifest(self,  prefix):
        bucket = self.bucket
        keys = []
        next_token = ''
        base_kwargs = {
            'Bucket': bucket,
            'Prefix': prefix,
        }

        while next_token is not None:
            kwargs = base_kwargs.copy()

            if next_token != '':
                kwargs.update({'ContinuationToken': next_token})

            results = self.s3_client.list_objects_v2(**kwargs)
            contents = results.get('Contents')

            for i in contents:
                k = i.get('Key')
                if (k[-1] != '/') & (bool(re.search("\/manifest$", k))):
                    keys.append(k)

            next_token = results.get('NextContinuationToken')

        return [json.loads(self.read_s3_contents(prefix=k).decode("UTF-8")) for k in keys]

    def build_download_dict(self):
        manifest = self.get_manifest(prefix="data/")
        return [row["url"] for item in manifest for row in item["entries"]]

    def get_full_dataset(self, manifest=None):
        path = re.compile(f"s3://{self.bucket}/(.+)")

        if manifest is None:
            manifest = self.build_download_dict()

        for row in manifest:

            key = re.search(path, row).group(1)
            loc = self.root_save_path+key

            if not os.path.isdir(os.path.dirname(loc)):
                os.makedirs(os.path.dirname(loc))

            if not os.path.isfile(loc):
                print(f"downloading: {key}...")
                self.s3_client.download_file(self.bucket, key, loc)
            else:
                print(f"pass: {key}...")
