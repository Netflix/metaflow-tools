class MFBException(Exception):
    headline = "MetaflowBot error"
    traceback = False

    def __init__(self, msg):
        self.msg = msg


class MFBRulesParseException(MFBException):
    headline = "MetaflowBot rules file error"
    traceback = False
