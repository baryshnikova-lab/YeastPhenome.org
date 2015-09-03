# YeastPhenome.org

## `yeastphenome/settings.py-template`

`yeastphenome/settings.py-template` needs to be copied to
`yeastphenome/settings.py` and edited to suit your needs.  Currently
there are a few added items that isn't a Django standard.

### Options

#### `DATA_DIR`

Link to directory containing directoris of PubMed IDs to be offered
as zip files.

#### `DOWNLOAD_PREFIX`

The prefix to use when downloading a zip file.

### PostgreSQL

The `migrate` option doesn't seem to work in one step when using
PostgreSQL, so you will need to comment out part of the
`INSTALLED_APPS` section the first time you run it:

```
INSTALLED_APPS = (
    # For some odd reason when we first migrate with postgres we need
    # to do only these three first.
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',

    # # Then add the rest when the first three are successful.
    # 'django.contrib.admin',
    # 'django.contrib.sessions',
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',
    # 'google_analytics',
    # 'mptt',

    # 'papers',
    # 'phenotypes',
    # 'conditions',
)
```

Then `migrate` the database.  After that, uncomment out the bottom
part of the block and `migrate` again.
