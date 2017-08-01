# coding: utf-8
from __future__ import unicode_literals
from flask import Flask, request, jsonify
import logging
import sys
import re

sys.path.append('/usr/lib/mailman/')

try:
    from Mailman import Errors, MailList, mm_cfg, Post, Utils
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

        m_list = MailList.MailList(list_name, lock=False)
        source = m_list.GetListEmail()
        
        # Correct domain
        if domain_name and not source.split()[-1].endswith(domain_name):
            continue

        # Matching source
        if source_regex and not matches_regex(source_regex, source):
            continue
    
        destinations = m_list.getMembers()

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
    all_lists = Utils.list_names()
    email = request.args.get('email')
    if not email:
        return jsonify({'lists': all_lists})

    lists = []
    for list_name in all_lists:
        m_list = MailList.MailList(list_name, lock=False)
        members = m_list.getMembers()
        if email in members:
            lists.append(list_name)

    return jsonify({'lists': lists})

if __name__ == '__main__':
    app.run()
