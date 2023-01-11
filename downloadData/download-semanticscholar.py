import os
import re
import gzip
import json
import shutil
import requests
from datetime import datetime
from ratelimit import limits, sleep_and_retry
import local.config as conf


class SemanticScholar:

    def __init__(self, release_id=None):

        api_key = conf.semanticScholar.api_key

        self.headers = {"X-API-KEY": api_key}
        self.release_id = release_id
        self.query_date = datetime.today().strftime('%Y-%m-%d')
        self.path_root = conf.links.local_root

        if release_id is None:
            print("no release id provided, using latest")
            self.release_id = max(self.query_dataset_api())

    @sleep_and_retry
    @limits(calls=10, period=32)
    def query_dataset_api(self, dataset=None):

        base_url = "https://api.semanticscholar.org/datasets/v1/release/"

        if self.release_id is None:
            url = base_url
        elif dataset is None:
            url = f"{base_url}{self.release_id}"
        else:
            url = f"{base_url}{self.release_id}/dataset/{dataset}"

        response = requests.get(f"{url}", headers=self.headers).json()

        return response

    def loop_api(self):

        results = []
        datasets = self.query_dataset_api()

        for r in datasets["datasets"]:
            result = self.query_dataset_api(dataset=r["name"])
            results.append(result)

        return results

    def results_to_json(self, results):

        path = f"{self.path_root}/s2/metadata/release_id={self.release_id}/query_date={self.query_date}"

        if not os.path.exists(f"{path}"):
            os.makedirs(f"{path}")

        with open(f"{path}/results.json", "w") as f:
            f.write(json.dumps(results, indent=2))

    def download_files(self, results):

        local_file_locations = []

        for dataset in results:
            dataset_name = dataset["name"]

            path = f"{self.path_root}/data/input/release_id={self.release_id}/{dataset_name}"
            if not os.path.exists(f"{path}"):
                os.makedirs(f"{path}")

            for file in dataset["files"]:

                filename = re.search(r"\/([^\/]+)\?", file).group(1)
                save_location = f"{path}/{filename}"
                if os.path.isfile(save_location):
                    pass
                else:
                    with requests.get(file, stream=True) as r:
                        r.raise_for_status()

                        with open(save_location, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=50000000):
                                f.write(chunk)

                local_file_locations.append(save_location)

        return local_file_locations

    @staticmethod
    def extract_files(local_file_locations):

        for file in local_file_locations:
            try:
                with gzip.open(file, 'rb') as f_in:
                    with open(re.sub(r'.gz$', '.json', file), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(file)
            except:
                # todo : write better exception clause
                pass

    def get_newest_data(self):

        results = self.loop_api()
        self.results_to_json(results=results)
        local = self.download_files(results=results)
        self.extract_files(local_file_locations=local)