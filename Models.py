from orator import Model
from orator.orm import has_one, has_many, belongs_to

import json


class User(Model):
    __table__ = 'Users'

    @has_many('id', 'ownerId')
    def notes(self):
        return Note


class Revision(Model):
    __table__ = 'Revisions'

    @belongs_to('noteId')
    def note(self):
        return Note

    @property
    def authors(self):
        return User.where_in('id', [author[0] for author in json.loads(self.authorship)]).get()


class Note(Model):
    __table__ = 'Notes'

    @belongs_to('ownerId')
    def owner(self):
        return User

    @has_many('noteId')
    def revisions(self):
        return Revision
