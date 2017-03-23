from core.jamaclient import JamaClient
import json
import re

class ItemTree(object):
    def __init__(self, document_key):
        jama_client = JamaClient()
        target_project = jama_client.get_item_for_documentkey(document_key)["project"]
        self.sequence_map = {}
        item_list = jama_client.get_all("items?project={}".format(target_project))
        item_list = self.sanitize_items(item_list, jama_client)
        self.true_root = None

        for item in item_list:
            if item["documentKey"] == document_key:
                self.true_root = item
            self.sequence_map[item["location"]["sequence"]] = item
            item["children"] = []
        roots = []
        for item in item_list:
            seq = item["location"]["sequence"]
            parent_seq = self.get_parent_sequence_number(seq)
            if parent_seq == "":
                roots.append(item)
            else:
                try:
                    self.get_iterable_children_list(self.sequence_map[parent_seq]).append(item)
                except KeyError:
                    print("couldn't find key for item " + json.dumps(item))
                    # exit()

        self.sort_forest(roots)
        print("done")

    def get_tree_list(self):
        flatList = self.to_depth_first(self.true_root)
        with open("itemTree.json", "w") as treeJson:
            json.dump(flatList, treeJson)
        return flatList
        # return self.to_depth_first(self.true_root)

    def sort_forest(self, root_list):
        root_list.sort(key=self.natural_keys)
        # root_list.sort(key=lambda item:item["location"]["sequence"])
        for item in root_list:
            self.sort_forest(self.get_iterable_children_list(item))

    def get_parent_sequence_number(self, seq):
        # seq = seq[:seq.rfind(".")]
        # if(self.sequence_map.has_key(seq)):
        #     return seq
        # else:
        #     return ""
        return seq[:seq.rfind(".")]

    def to_depth_first(self, root):
        result = [root]
        for child in self.get_iterable_children_list(root):
            result.extend(self.to_depth_first(child))
        return result

    def get_iterable_children_list(self, item):
        if item.get("children") is None:
            return []
        else:
            return item.get("children")


    def sanitize_items(self, item_list, jama_client):
        new_item_list = []
        item_hit = 0
        item_miss = 0
        total = 0
        for item in item_list:
            total = total + 1
            item = jama_client.get_item(item["id"])
            if item is not None:
                item_hit = item_hit + 1
                new_item_list.append(item[0])
                print("hit")
            else:
                item_miss = item_miss + 1
                print("miss")
        print("total items processed " + str(total) + ". Total misses were " + str(item_miss) + " while Total hits were " + str(item_hit))
        return new_item_list


    def atoi(self, item):
        return int(item) if item.isdigit() else item


    def natural_keys(self, item):
        return [self.atoi(c) for c in re.split('(\d+)', item["location"]["sequence"])]


#
# class JamaItem(object):
#     def __init__(self, item):
#         self.jama_client = JamaClient()
#         self.item_id = self.item["id"]


