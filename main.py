from Models import Note

from email_mapping import mapping as user_map

import diff_match_patch as dmp_module
from git import Repo, Actor
from orator import DatabaseManager, Model

from argparse import ArgumentParser
from os.path import exists
from os import mkdir
from pathlib import Path
import re
import shutil
import sys

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
    patches = dmp.patch_fromText(
        re.sub(r'\/uploads', 'uploads', patches_text) if patches_text is not None else patches_text)
    new_content, _ = dmp.patch_apply(patches, content)

    # Write new content
    with open(Path(note_repo_dir).joinpath('README.md'), 'w') as md_file:
        md_file.write(new_content)


def track_image(note_repo_dir, local_image_upload, index, patch_text):
    images = re.findall(r'\/uploads\/([A-Za-z0-9_]+\.(jpe?g|png|gif))',
                        patch_text, flags=re.I)

    if not exists(Path(note_repo_dir).joinpath('uploads')):
        mkdir(Path(note_repo_dir).joinpath('uploads'))

    for img in images:
        try:
            shutil.copyfile(Path(local_image_upload).joinpath(
                img[0]), Path(note_repo_dir).joinpath('uploads').joinpath(img[0]))
            index.add('uploads/%s' % img[0])
        except Exception as e:
            print('%s image not exists skip it' % e.filename, file=sys.stderr)


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
    parser.add_argument('--local_image_upload',
                        help='path which saving upload image', type=str)

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
                                                 (note.shortid, re.sub('[\t\n\r \/]+', '_', note.title)))
        note_repo = Repo.init(note_repo_dir)
        index = note_repo.index

        # Write revision

        for revision in note.revisions:
            commit_author = None
            commit_message = None

            # Write change
            write_patch(note_repo_dir, revision.patch)

            # Track image used in revision
            if revision.patch is not None and args.local_image_upload is not None:
                track_image(note_repo_dir, args.local_image_upload,
                            index, revision.patch)

            # Set author
            authors = [user_map(user.email) for user in revision.authors]
            if len(authors) == 1:
                commit_author = Actor(authors[0][1], authors[0][0])
                commit_message = """Change by %s """ % (authors[0][1])
            else:
                commit_author = committer
                commit_message = many_user_commit_message_template % ('\n'.join(
                    ['Change by %s (%s)' % ('Anonymous' if author[1] is None else author[1], author[0]) for author in authors]))

            # Commit it
            index.add(['README.md'])
            index.commit(commit_message, author=commit_author,
                         committer=committer)
