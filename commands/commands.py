from commandconfig import CommandConfig
from bs4 import BeautifulSoup
import re
import json

from core.jamaconfig import JamaConfig


def get_commands():
    commands = []
    commands.append(FolderAndTextConverter())
    commands.append(StrikeThroughToPlain())
    commands.append(IDHandler())
    commands.append(TableBorder())
    commands.append(Paragraphs())
    commands.append(Indents())
    commands.append(FixedWidth())
    commands.append(Figures())
    commands.append(Tables())
    # TODO:
    return commands




def get_list_commands():
    list_commands = []
    list_commands.append(FootNotes())
    return list_commands

def get_clean_commands():
    clean_commands = []
    clean_commands.append(Hyperlinks())
    return clean_commands

def id_handler():
    return IDHandler()

class Command:
    def execute(self, item):
        raise StandardError("Base (Command) execute called")


class ListCommand(Command):
    def execute(self, items):
        raise StandardError("Base (ListCommand) execute called")


class FolderAndTextConverter(Command):
    def execute(self, item):
        id_regex = "(\s*REQ\d+[\.\d]+\s*)"
        name = item["fields"]["name"].encode("utf-8")
        requirement_id = re.search(id_regex, name)

        if len(item) <= 5:
            item["isFolder"] = not requirement_id and item["hasChildren"]
            item["isText"] = not requirement_id and not item["hasChildren"]

        else:
            item["isFolder"] = not requirement_id and (len(item["children"]) > 0)
        # item["isFolder"] = not requirement_id and item["hasChildren"]
        # item["isFolder"] = not requirement_id and item["children"]
            item["isText"] = not requirement_id and not item["children"]

        print("done")


class StrikeThroughToPlain(Command):
    def execute(self, item):
        description = item["fields"]["description"]
        id_regex = "\s*<\s*s style\s*=\s*\"\s*text-decoration:line-through\s*\"\s*>"
        found = re.search(id_regex, description)
        if found:
            description = re.sub(id_regex, "<span style=\"font-family:monospace\">", description)

        id_regex = "\s*<\s*span style\s*=\s*\"\s*text-decoration:line-through\s*\"\s*>"
        found = re.search(id_regex, description)
        if found:
            description = re.sub(id_regex, "<span style=\"font-family:monospace\">", description)
        item["fields"]["description"] = description


class IDHandler(Command):
    def execute(self, item):
        id_regex = "(\s*REQ\d+[\.\d]+\s*)"
        name = item["fields"]["name"].encode("utf-8")
        requirement_id = re.search(id_regex, name)
        if not requirement_id:
            return
        item["fields"]["name"] = name[:requirement_id.start()] + name[requirement_id.end():].strip()
        requirement_id = requirement_id.group().strip()
        requirement_id = "{}-{}".format(requirement_id[:3], requirement_id[3:])
        item["fields"][CommandConfig.legacy_id + "${}".format(item["itemType"])] = requirement_id
        item["globalId"] = requirement_id
        if "globalId" in item["fields"]:
            item["fields"]["globalId"] = requirement_id


class TableBorder(Command):
    def execute(self, item):
        description = BeautifulSoup(item["fields"]["description"], "html.parser")
        for table in description.find_all('table', recursive=True):
            self.fix_table(table)
        item["fields"]["description"] = str(description)

    def fix_table(self, table):
        for td in table.find_all('td', recursive=True):
            try:
                if 'border' in td['style']:
                    table['border'] = "1"
                    return
            except KeyError:
                pass
        table['border'] = "0"


class Paragraphs(Command):
    def execute(self, item):
        name = item["fields"]["name"]
        if '[p]' in name:
            # print("Found a name")
            item["fields"]["new_paragraph"] = True
            item["fields"]["new_paragraph$24"] = True
            item["fields"]["name"] = name.replace("[p]", "")


class Indents(Command):
    def execute(self, item):
        description = item["fields"]["description"]

        string_list = description.split("[t]")
        if len(string_list) == 1:
            return

        result = ""
        pixel_count = 0
        if len(string_list[0]) > 0:
            result += string_list[0]
        for i in range(1, len(string_list)):
            pixel_count += 40
            if len(string_list[i]) > 0 or (len(string_list[i]) == 0 and i == len(string_list) - 1):
                result += "<p style=\"margin-left:{}px\">{}".format(str(pixel_count), string_list[i])
                pixel_count = 0

        item["fields"]["description"] = result
        # t_count = description.count("[t]")
        # description = re.sub(r"\[t\]", "",)
        # description.replace("[t]", '<p style=\"margin-left:40px\">')
        # item["fields"]["description"] = description


class FixedWidth(Command):
    def execute(self, item):
        description = item["fields"]["description"]
        description.replace("[pre]", "<pre>")
        description.replace("[/pre]", "</pre>")


class Figures(Command):
    def execute(self, item):
        name = item["fields"]["name"]
        if '[fig]' in name:
            item["fields"]["figure"] = True
        item["fields"]["name"] = name.replace("[fig]", "")


class Tables(Command):
    def execute(self, item):
        name = item["fields"]["name"]
        if '[table]' in name:
            item["fields"]["table"] = True
        item["fields"]["name"] = name.replace("[table]", "")


class FootNotes(ListCommand):
    def execute(self, items):
        foot_note_item = items[-1]
        description = BeautifulSoup(foot_note_item["fields"]["description"], "html.parser")
        foot_notes = []
        for div in description.find_all('div', recursive=True):
            if div.has_attr("style") and div["style"] == "-aw-footnote-isauto:1":
                foot_notes.append(self.create_footnote_item(div, items[0]["id"]))
                div.extract()

        items.extend(foot_notes)
        return items

    def create_footnote_item(self, div, root_id):
        return {
            "isFootnote": True,
            "hasChildren": False,
            "fields": {
                "name": div.get_text()[:250],
                "description": str(div)
            },
            "location": {
                "parent": {
                    "item": root_id
                }
            }
        }


class Hyperlinks(ListCommand):
    def __init__(self):
        self.name_to_id = {}
        self.base_url = JamaConfig().base_url

    def execute(self, items):
        name_map = {}
        reference_map = {}
        name_map.update(self.get_name_map(items, "name"))
        name_map.update(self.get_name_map(items, "description"))
        reference_map.update(self.get_references_map(items, "Normative References"))
        reference_map.update(self.get_references_map(items, "Informative References"))

        self.set_links(name_map, items, "name")
        self.set_reference_links(reference_map, items, "description")
        self.set_links(name_map, items, "description")


        return items

    def get_name_map(self, items, field_name):
        name_map = {}
        for item in items:

            value, identifier_list = self.get_identifier_list(item["fields"][field_name])
            item["fields"][field_name] = value
            for identifier in identifier_list:
                name_map[identifier] = (item["id"], item["project"])
        return name_map

    def get_references_map(self, items, field_value):
        reference_map = {}
        for item in items:
            if item["fields"]["name"] == field_value:
                reference_item = item["children"][0]
                identifier_list = self.get_reference_identifier_list(reference_item)
                for identifier in identifier_list:
                    reference_map[identifier] = (reference_item["id"], reference_item["project"])
        return reference_map

    def set_links(self, name_map, items, field_name):
        for item in items:
            item["fields"][field_name] = self.set_targets(name_map, item["fields"][field_name])

    def set_targets(self, name_map, value):
        link_regex = "\[a.*?\/a\]"
        link_replacement = "<a href=\"{base_url}/perspective.req?docId={item_id}&projectId={project_id}\" target=\"blank\">{text}</a>"
        links = re.findall(link_regex, value)
        for link in links:
            to_replace = link
            plain_text = BeautifulSoup(link, "html.parser").getText()

            link_target = plain_text[plain_text.index("href=") + 5: plain_text.index("]")]
            link_text = plain_text[plain_text.index("]") + 1:]
            link_text = link_text[:link_text.index("[")]
            id_and_project = name_map.get(link_target)

            if id_and_project:
                try:
                    new_link = link_replacement.format(base_url=self.base_url, item_id=id_and_project[0], text=link_text, project_id=id_and_project[1])
                    value = value.replace(to_replace, new_link)
                    return value
                except UnicodeEncodeError:
                    pass
        return value

    def set_reference_links(self, name_map, items, field_name):
        for item in items:
            item["fields"][field_name] = self.set_reference_targets(name_map, item["fields"][field_name])

    def set_reference_targets(self, name_map, value):
        link_regex = "\[a.*?\/a\]"
        link_replacement = "<a href=\"{base_url}/perspective.req?docId={item_id}&projectId={project_id}\" target=\"blank\">{text}</a>"
        links = re.findall(link_regex, value)
        for link in links:
            to_replace = link
            plain_text = BeautifulSoup(link, "html.parser").getText()

            link_target = plain_text[plain_text.index("href=") + 5: plain_text.index("[/a]")]
            link_text = link_target[link_target.index("]") + 1 :]
            id_and_project = name_map.get(link_target)

            if id_and_project:
                new_link = link_replacement.format(base_url=self.base_url, item_id=id_and_project[0], text=link_text, project_id=id_and_project[1])
                value = value.replace(to_replace, new_link)
        return value



    def get_identifier_list(self, value):
        name_regex = "\[[^\]]*?name:[^\[]*]"
        names = re.findall(name_regex, value)
        #todo remove
        identifiers = []
        # identifiers = [name[name.index(":") + 1: -1] for name in
        #                         [BeautifulSoup(''.join(name), "html.parser").getText() for name in names]]
        for name in names:
            identifiers.append(BeautifulSoup(name[name.index(":") + 1: -1], "html.parser").getText())
            value = value.replace(name, "")

        return value, identifiers


    def recursively_get_reference_list(self, item, subString):
        reference_regex = "<a name=\".*\">.*\[.*\]"
        references = re.findall(reference_regex, subString)
        identifiers = []

        for reference in references:
            identifier_to_add = BeautifulSoup(reference[reference.index("name") : reference.index("]") + 1], "html.parser").getText()
            # identifiers.append(BeautifulSoup(reference[reference.index(":") + 1: -1], "html.parser").getText())
            identifier_to_add = identifier_to_add.replace("\"", "").replace(">", "]").replace("name=", "")
            identifiers.append(identifier_to_add)

            # identifiers.append(BeautifulSoup(reference[reference.index(":") + 1: -1], "html.parser").getText())
            identifiers.extend(self.recursively_get_reference_list(item, reference[reference.index("]") + 1 :]))
        if len(identifiers) > 0:
            return identifiers
        else:
            return []
        # return identifiers

    def get_reference_identifier_list(self, item):
        reference_regex = "<a name=\".*\">.*\[.*\]"
        references = re.findall(reference_regex, item["fields"]["description"])
        identifiers = []

        for reference in references:
            identifier_to_add = BeautifulSoup(reference[reference.index("name") : reference.index("]") + 1], "html.parser").getText()
            # identifiers.append(BeautifulSoup(reference[reference.index(":") + 1: -1], "html.parser").getText())
            identifier_to_add = identifier_to_add.replace("\"", "").replace(">", "]").replace("name=", "")
            identifiers.append(identifier_to_add)
            identifiers.extend(self.recursively_get_reference_list(item, reference[reference.index("]") + 1 :]))

        return identifiers



