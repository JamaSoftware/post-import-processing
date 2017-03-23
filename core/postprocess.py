import time

from core.itemtree import ItemTree
from jamaclient import JamaClient
import re
from commands import Macro


class PostProcess:
    def __init__(self):
        self.macro = Macro()
        self.jama_client = JamaClient()
        self.items = []

    def process(self, document_keys):
        for document_key in document_keys:
            self.process_set(document_key)

    def process_set(self, document_key):
        # items = [item for item in ItemTree(document_key=document_key)]
        # items = [item for item in ItemSet(document_key=document_key)]

        itemTree = ItemTree(document_key=document_key)
        self.items = itemTree.get_tree_list()

        if len(self.items) == 1:
            return

        self.items = self.macro.run_list(self.items)

        iter_items = iter(self.items)
        next(iter_items)
        for item in iter_items:
            # print "loop"
            self.macro.run(item)
            self.jama_client.put(item)
        self.jama_client.clean_up()
        print("done")


    def establish_all_links(self, document_keys):
        for document_key in document_keys:
            self.establish_links(document_key)


    def establish_links(self, document_key):
        print "links"
        # time.sleep(60)
        print "resume"

        itemTree = ItemTree(document_key=document_key)
        processed_items = itemTree.get_tree_list()

        # processed_items = [item for item in ItemTree(document_key=document_key)]
        # processed_items = self.items
        if len(processed_items) == 1:
            return

        processed_items = self.macro.run_clean(processed_items)
        iter_items = iter(processed_items)
        next(iter_items)
        for item in iter_items:
            print "link_loop"
            try:
                del item["fields"]["id"]
            except KeyError:
                pass
            self.jama_client.put_item_raw(item)


