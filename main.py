from Models import Note, User

from email_mapping import mapping as user_map

import diff_match_patch as dmp_module
from git import Repo, Actor
from orator import DatabaseManager, Model

from argparse import ArgumentParser
from os.path import exists
from pathlib import Path
import re

many_user_commit_message_template = """Change by many user

%s"""


def write_patch(note_repo_dir, patches_text):
    md_path = Path(note_repo_dir).joinpath('README.md')
    content = ''

    if exists(md_path):
        # Read current content
        with open(md_path, 'r') as md_file:
            content = md_file.read()

    # Apply diff to File
    dmp = dmp_module.diff_match_patch()
    patches = dmp.patch_fromText(patches_text)
    new_content, _ = dmp.patch_apply(patches, content)

    # Write new content
    with open(Path(note_repo_dir).joinpath('README.md'), 'w') as md_file:
        md_file.write(new_content)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '--db_type', help='database driver. default is postgres', type=str)
    parser.add_argument(
        '--host', help='database host. default is localhost', type=str)
    parser.add_argument('database', help='name of database.', type=str)
    parser.add_argument('username', help='username to connection', type=str)
    parser.add_argument('password', help='password to connection', type=str)
    parser.add_argument(
        '--prefix', help='prefix of table name. default is \'\'', type=str)
    parser.add_argument('path', help='path to saving exported notes', type=str)

    args = parser.parse_args()

    root_path = Path(args.path).resolve()

    config = {
        'hackmd': {
            'driver': args.db_type if args.db_type else 'postgres',
            'host': args.host if args.host else 'localhost',
            'database': args.database,
            'user': args.username,
            'password': args.password,
            'prefix': args.prefix if args.prefix else ''
        }
    }

    db = DatabaseManager(config)
    Model.set_connection_resolver(db)

    committer = Actor('CodiMD2Git', 'CodiMD2Git@pdis.tw')

    for note in Note.has('owner').with_('owner', {
        'revisions': lambda q: q.order_by('createdAt', 'asc')
    }).get():
        note_repo_dir = Path(root_path).joinpath('%s_%s' %
                                                 (re.sub('[\t\n\r \/]+', '_', note.title), note.owner.email.replace('@', '[at]')))
        note_repo = Repo.init(note_repo_dir)
        index = note_repo.index

        # Write revision

        for revision in note.revisions:
            commit_author = None
            commit_message = None
            # Write change
            write_patch(note_repo_dir, revision.patch)

            # Set author
            authors = [user_map(user.email) for user in revision.authors]
            if len(authors) == 1:
                commit_author = Actor(authors[0][1], authors[0][0])
                commit_message = """Change by %s """ % (authors[0][1])
            else:
                commit_author = committer
                commit_message = many_user_commit_message_template % ('\n'.join(
                    ['Change by %s (%s)' % (author[1], author[0]) for author in authors]))

            # Commit it
            index.add(['README.md'])
            index.commit(commit_message, author=commit_author,
                         committer=committer)
