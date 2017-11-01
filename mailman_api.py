# coding: utf-8
from __future__ import unicode_literals
from flask import Flask, request, jsonify, make_response
import logging
import sys
import re

from utils import get_mailing_list, parse_boolean, Member

sys.path.append('/usr/lib/mailman/')

try:
    from Mailman import Errors, mm_cfg, Post, Utils
except ImportError:
    logging.error('Could not import Mailman module')


def matches_regex(pattern, _string):
    return re.search(pattern, _string) is not None
    

app = Flask(__name__)
# app.config['DEBUG'] = True


@app.route('/lists/', methods=['GET'])
def list_lists_with_members():
    domain_name = request.args.get('domain__name')
    source_regex = request.args.get('source_regex')
    dest_regex = request.args.get('destination_regex')

    lists_w_members = []
    for list_name in Utils.list_names():
        if list_name == 'mailman':
            continue

        mlist = get_mailing_list(list_name, lock=False)
        source = mlist.GetListEmail()
        
        # Correct domain
        if domain_name and not source.split()[-1].endswith(domain_name):
            continue

        # Matching source
        if source_regex and not matches_regex(source_regex, source):
            continue
    
        destinations = mlist.getMembers()

        # Matching at least one destination
        if dest_regex and not matches_regex(dest_regex, "\n".join(destinations)):
            continue
        
        lists_w_members.append({
            'destinations': destinations,
            'name': source,
            'type': 'mailman',
            'admin_url': 'https://lists.neuf.no/admin/{}/'.format(list_name),
            'admin_type': 'selfservice',
            'num': len(destinations)
        })

    return jsonify({
        'lists': lists_w_members,
        'num': len(lists_w_members)
    })


@app.route('/', methods=['GET'])
def list_lists():
    """ List all lists

        ?address: an email address if provided will only return lists with the member on it
    """
    all_lists = Utils.list_names()
    address = request.args.get('address')
    if not address:
        return jsonify({'lists': all_lists})

    lists = []
    for list_name in all_lists:
        m_list = get_mailing_list(list_name, lock=False)
        members = m_list.getMembers()
        if address in members:
            lists.append(list_name)

    return jsonify({'lists': lists})


@app.route('/<list_name>', methods=['PUT'])
def subscribe(list_name):
    """ Adds a new subscriber to the list called 'list_name'

        ?address: email address that is to be subscribed to the list.
        ?fullname: full name of the person being subscribed to the list.
        ?digest: if this equals 'true', the new subscriber will receive digests instead of every mail sent to the list.
    """

    address = request.args.get('address')
    fullname = request.args.get('fullname')
    digest = parse_boolean(request.args.get('digest'))
    # TODO: Validate params

    mlist = get_mailing_list(list_name)
    userdesc = Member(fullname, address, digest)

    try:
        mlist.ApprovedAddMember(userdesc, ack=False, admin_notif=False)
    except Errors.MMAlreadyAMember:
        return make_response(jsonify("Address already a member."), 409)
    except Errors.MembershipIsBanned:
        return make_response(jsonify("Banned address."), 403)
    except (Errors.MMBadEmailError, Errors.MMHostileAddress):
        return make_response(jsonify("Invalid address."), 400)

    else:
        mlist.Save()
    finally:
        mlist.Unlock()

    return jsonify(True)


@app.route('/<list_name>', methods=['DELETE'])
def unsubscribe(list_name):
    """ Unsubsribe an email address from the mailing list.

        ?address: email address that is to be unsubscribed from the list
    """

    address = request.args.get('address')
    mlist = get_mailing_list(list_name)

    try:
        mlist.ApprovedDeleteMember(address)
        mlist.Save()
    except Errors.NotAMemberError:
        return make_response(jsonify("Not a member."), 404)
    finally:
        mlist.Unlock()

    return make_response('', 204)

if __name__ == '__main__':
    app.run()
