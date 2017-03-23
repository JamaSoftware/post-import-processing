from commands import get_commands
from commands import get_list_commands
from commands import get_clean_commands
from commands import id_handler
from commands import FolderAndTextConverter


class Macro:
    def __init__(self):
        self.list_commands = get_list_commands()
        self.commands = get_commands()
        self.clean_commands = get_clean_commands()
        self.id_handler = id_handler()
        self.text_and_folder_converter = FolderAndTextConverter()

    def run(self, item):
        for command in self.commands:
            command.execute(item)

    def run_list(self, items):
        return self.list_commands[0].execute(items)

    def run_clean(self, items):
        return self.clean_commands[0].execute(items)

    def run_id_handler(self, item):
        return self.id_handler.execute(item)

