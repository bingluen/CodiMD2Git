from Models import Note
from orator import DatabaseManager, Model

from argparse import ArgumentParser

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

    args = parser.parse_args()

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

    for note in Note.has('owner').with_('owner', {
        'revisions': lambda q: q.order_by('createdAt', 'asc')
    }).get():
        print(note.title)
