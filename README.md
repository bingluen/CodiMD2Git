# CodiMD2Git

Export notes as git repositories from self-hosting CodiMD

## Usage

### Install dependency

```
pipenv install
```

### Modify email_mapping.json
```
{
    "[User Email]": "User Name"
}
```

### Exporting

```
python main.py [-h] [--db_type DB_TYPE] [--host HOST] [--prefix PREFIX] database username password path
```

```
positional arguments:
  database           name of database.
  username           username to connection
  password           password to connection
  path               path to saving exported notes

optional arguments:
  -h, --help         show this help message and exit
  --db_type DB_TYPE  database driver. default is postgres
  --host HOST        database host. default is localhost
  --prefix PREFIX    prefix of table name. default is ''
```

# LICENSE
MPL-2.0