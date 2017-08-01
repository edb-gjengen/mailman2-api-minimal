import logging

from flask import jsonify, make_response

try:
    from Mailman import MailList, Errors
except ImportError:
    logging.error('Could not import Mailman module')


def parse_boolean(value):
    if value and value.lower() == 'true':
        return True

    return False


def get_mailing_list(listname, lock=True):
    try:
        return MailList.MailList(listname, lock=lock)
    except Errors.MMUnknownListError:
        raise make_response(jsonify("Unknown Mailing List `{}`.".format(listname)), 404)


class Member(object):
    def __init__(self, fullname=None, address=None, digest=None):
        self.fullname = fullname
        self.address = address
        self.digest = digest
