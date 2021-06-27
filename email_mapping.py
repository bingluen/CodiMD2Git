import json


def mapping(email):
    with open('email_mapping.json', 'r') as f:
        mapping = json.load(f)

        return email, mapping[email] if email in mapping.keys() else None
