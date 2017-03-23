from jamaclient import JamaClient

class ItemSet:
    def __init__(self, document_key=None, item=None):
        self.jama_client = JamaClient()
        if document_key is not None:
            self.document_key = document_key
            self.item = self.jama_client.get_item_for_documentkey(document_key)
            self.item_id = self.item["id"]
        elif item is not None:
            self.item = item
            self.item_id = item["id"]
        self.children = self.jama_client.get_children(self.item_id)
        self.item["hasChildren"] = len(self.children) != 0



    def __iter__(self):
        print "item"
        yield self.item
        for child in self.children:
            for item in ItemSet(item=child):
                yield item
