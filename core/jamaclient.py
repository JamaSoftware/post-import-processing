import time

from jamaconfig import JamaConfig
import requests
import json
import warnings
from requests import HTTPError


class JamaClient:
    def __init__(self):
        self.jama_config = JamaConfig()
        self.id_map = {}
        self.delete_list = []
        self.auth = self.jama_config.auth
        self.verify = self.jama_config.verify_ssl
        self.gid = self.jama_config.system_gid_prefix
        self.seconds = 2

    def extract_id(self, response):
        json_response = json.loads(response)
        location = json_response["meta"]["location"].split('/')[-1]
        return location

    def update_location(self, item):
        parent = item["location"]["parent"]
        if "item" not in parent:
            raise StandardError("Parent must be item: {}".format(item))

        if parent["item"] not in self.id_map:
            return item

        new_parent = self.id_map[parent["item"]]
        item["location"]["parent"]["item"] = new_parent
        return item

    def remove_read_only(self, item, response):
        message = response.text
        if "You cannot set read-only fields. fields:" not in message:
            raise StandardError("Error {} in item: {}".format(response.text, item))
        fields = message[message.index("fields: ") + 8:]
        fields = fields[:len(fields) - 3]
        fields = [field.strip() for field in fields.split(',')]
        for field in fields:
            if field in item:
                del item[field]
            if field in item["fields"]:
                del item["fields"][field]

    def get(self, url):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return requests.get(url, auth=self.auth, verify=self.verify)


    def get_item(self, item_id):
        url = self.jama_config.rest_url + "items/" + str(item_id)
        response = self.get(url=url)
        json_response = json.loads(response.text)
        if json_response["meta"]["status"] == "Not Found":
            print json_response
            print("Item not found with id " + str(item_id))
        else:
            return [json_response["data"]]


    def get_children(self, item_id):
        return self.get_all("items/{}/children".format(item_id))

    def get_item_for_documentkey(self, document_key):
        items = self.get_all("abstractitems?documentKey={}".format(document_key))
        if len(items) > 1:
            raise StandardError("Multiple items with ID: {}".format(document_key))
        if len(items) < 1:
            raise StandardError("No items found with ID: {}".format(document_key))
        return items[0]

    def get_all(self, resource):
        all_results = []
        results_remaining = True
        current_start_index = 0
        delim = '&' if '?' in resource else '?'
        while results_remaining:
            start_at = delim + "startAt={}".format(current_start_index)
            url = self.jama_config.rest_url + resource + start_at
            print url
            response = self.get(url)
            json_response = json.loads(response.text)
            if "pageInfo" not in json_response["meta"]:
                print json_response
                return [json_response["data"]]
            result_count = json_response["meta"]["pageInfo"]["resultCount"]
            total_results = json_response["meta"]["pageInfo"]["totalResults"]
            results_remaining = current_start_index + result_count != total_results
            current_start_index += 20
            all_results.extend(json_response["data"])

        return all_results

    def put(self, item):
        self.delay()
        if "isFootnote" in item:
            item["itemType"] = self.jama_config.text_type_id
            self.post_item(item)
            return item
        try:
            if not item["isFolder"] and not item["isText"]:
                self.put_item(item)
                return item
        except KeyError:
            if item["itemType"] == self.jama_config.text_type_id:
                item["isText"] = True
                item["isFolder"] = False
            elif item["itemType"] == self.jama_config.folder_type_id:
                item["isText"] = False
                item["isFolder"] = True
        try:
            # if both of these are set, folder should win
            if item["isFolder"]:
                item["childItemType"] = item["itemType"]
                item["itemType"] = self.jama_config.folder_type_id
            elif item["isText"]:
                item["itemType"] = self.jama_config.text_type_id

            self.replace_item(item)

        except KeyError:
            pass


    def put_item(self, item):
        self.delay()
        url = self.jama_config.rest_url + "items/{}?setGlobalIdManually=true".format(item["id"])
        # if "globalId" in item and self.gid not in item["globalId"]:
        #     url += "?setGlobalIdManually=true"
        item = self.update_location(item)

        try:
            response = requests.put(url, auth=self.auth, verify=self.verify, json=item)
            response.raise_for_status()
        except HTTPError as e:
            self.remove_read_only(item, e.response)
            self.put_item(item)

    def put_item_raw(self, item):
        self.delay()
        url = self.jama_config.rest_url + "items/{}?setGlobalIdManually=true".format(item["id"])
        try:
            response = requests.put(url, auth=self.auth, verify=self.verify, json=item)
            response.raise_for_status()
        except HTTPError as e:
            self.remove_read_only(item, e.response)
            self.put_item_raw(item)

    def post_item(self, item):
        self.delay()
        url = self.jama_config.rest_url + "items"
        try:
            response = requests.post(url, auth=self.auth, verify=self.verify, json=item)
            response.raise_for_status()
        except HTTPError as e:
            self.remove_read_only(item, e.response)
            self.post_item(item)

    def replace_item(self, item):
        self.delay()
        post_url = self.jama_config.rest_url + "items?project={}".format(item["project"])
        if "globalId" in item and self.gid not in item["globalId"]:
            post_url += "&setGlobalIdManually=true"
        delete_id = item["id"]
        item = self.update_location(item)
        try:
            response = requests.post(post_url, auth=self.auth, verify=self.verify, json=item)
            response.raise_for_status()
            if item["isFolder"]:
                self.id_map[item["id"]] = self.extract_id(response.text)
            self.delete_list.append(delete_id)
        except HTTPError as e:
            self.remove_read_only(item, e.response)
            self.replace_item(item)
        return item

    def clean_up(self):
        delete_url = self.jama_config.rest_url + "items/{}"
        for url in [delete_url.format(url) for url in self.delete_list]:
            self.delay()
            requests.delete(url, auth=self.auth, verify=self.verify)

    def delay(self):
        time.sleep(self.seconds)



    def putAttachment(self):
        file = "itemtree.py"
        url = self.jama_config.rest_url + "attachments/2129057/" + file
        try:
            response = requests.put(url, auth=self.auth, verify=self.verify, json=json.load(file))
            response.raise_for_status()
        except HTTPError as e:
            print ("DOne")
