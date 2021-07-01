import re

import yaml

from .exceptions import MFBRulesParseException

class MFBRules(object):

    def __init__(self, path):
        with open(path) as f:
            try:
                self.rules = yaml.load(f,Loader=yaml.SafeLoader)
            except Exception as ex:
                raise MFBRulesParseException(str(ex))

        for i, rule in enumerate(self.rules):
            if not all(k in rule for k in ('name', 'event_type', 'action')):
                raise MFBRulesParseException("Rule #%d does not have name, "
                                             "event_type, and action "
                                             "specified." % (i + 1))
            msg = rule.get('message')
            if msg:
                rule['message'] = re.compile(msg, flags=re.IGNORECASE)

    def __len__(self):
        return len(self.rules)

    def match(self, event, state):
        for rule in self.rules:
            event_type = rule.get('event_type')
            if event_type and event_type != event.type:
                continue
            is_mention = rule.get('is_mention')
            if is_mention is not None and is_mention != event.is_mention:
                continue
            is_im = rule.get('is_im')
            if is_im is not None and is_im != event.is_im:
                continue
            is_direct = rule.get('is_direct')
            if is_direct is not None and is_direct != event.is_direct:
                continue
            message = rule.get('message')
            re_match = None
            if message:
                re_match = message.match(event.msg.strip())
                if not re_match:
                    continue
            if event.type == 'state_change' and\
               not state.is_event_match(event, rule.get('state_change', {})):
                continue
            context = rule.get('context')
            if context and not state.is_state_match(context, event):
                continue
            return rule['name'],\
                   rule['action'],\
                   re_match.groups() if re_match else [],\
                   rule.get('ephemeral_context_update')
