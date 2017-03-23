from core.itemtree import ItemTree
from jamaclient import JamaClient
import re
from commands import Macro



class Id_Handler:
    def __init__(self):
        self.macro = Macro()
        self.jama_client = JamaClient()
        self.items = []

    def execute(self, document_keys):
        for document_key in document_keys:
            self.execute_set(document_key)

    def execute_set(self, document_key):
        itemTree = ItemTree(document_key=document_key)
        self.items = itemTree.get_tree_list()

        if len(self.items) == 1:
            return

        iter_items = iter(self.items)
        next(iter_items)
        for item in iter_items:
            # print "loop"
            # self.macro.text_and_folder_converter.execute(item)
            self.macro.id_handler.execute(item)
            self.jama_client.put(item)
        self.jama_client.clean_up()
        print("done")