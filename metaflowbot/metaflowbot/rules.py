import re

import yaml

from . import SUPPORTED_RULES
from .exceptions import MFBRulesParseException


class MFBRules(object):
    """MFBRules
    Object that runs the rule framework on the Bot.

    Currently Handled Events :
        # Internal Events
        - never match
        - lost_process
        # User Facing events:
        - new_thread
            - Publishes state
        - user_message
            - Some messsage Publishes state
        # Possible User Facing events in Future
            - slash_message : Possible in future
    """

    def __init__(self):
        # Changed the way rules are loaded here from Initial version.
        # Now every subpackage botaction needs toe expose a `RULES` object which
        # gets registered at init to make the bot actions more customizable.
        self.rules = SUPPORTED_RULES

    def __len__(self):
        return len(self.rules)

    @staticmethod
    def make_subpackage_rules(data):
        try:
            # Todo Run Rule Parsing here.
            # todo check for important keys heree
            rules = yaml.load(data,Loader=yaml.SafeLoader)
        except Exception as ex:
            raise MFBRulesParseException(str(ex))

        for i, rule in enumerate(rules):
            if not all(k in rule for k in ('name', 'event_type', 'action')):
                raise MFBRulesParseException("Rule #%d does not have name, "
                                            "event_type, and action "
                                            "specified." % (i + 1))
            msg = rule.get('message')
            if msg:
                rule['message'] = re.compile(msg, flags=re.IGNORECASE)
        return rules

    def match(self, event, state):
        for rule in self.rules:
            event_type = rule.get('event_type')
            # If event type of rule and event type of message don't match continue
            if event_type and event_type != event.type:
                continue

            ############################################################
            # Todo : Verify Why there lines are there when there is no is_mention,`is_im`,`is_direct` in Rules.
            is_mention = rule.get('is_mention')
            if is_mention is not None and is_mention != event.is_mention:
                continue
            is_im = rule.get('is_im')
            if is_im is not None and is_im != event.is_im:
                continue
            is_direct = rule.get('is_direct')
            if is_direct is not None and is_direct != event.is_direct:
                continue
            ###################################################################

            message = rule.get('message')
            re_match = None
            if message:
                re_match = message.match(event.msg.strip())
                # if Message didn't match the rule theen continue
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
