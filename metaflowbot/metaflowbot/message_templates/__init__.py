from collections import defaultdict, namedtuple


class Section:
    def __init__(self,section_type,text) -> None:
        self.type=section_type
        self.text=text

class MarkdownSection(Section):
    def __init__(self, text) -> None:
        super().__init__('mrkdwn', text)

class Message:
    def __init__(self) -> None:
        self.blocks = []

    def add_section(self,block:Section):
        self.blocks.append(block)
