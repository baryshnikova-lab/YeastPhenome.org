# YeastPhenome.org

## `yeastphenome/settings.py-template`

`yeastphenome/settings.py-template` needs to be copied to
`yeastphenome/settings.py` and edited to suit your needs.  Currently
there are two added items that isn't a Django standard.  Both are only
refered to in the `paper/models.py` file.

### `TITLE`

The title of the web site, to make it easy to distinguisg the
developement site from testing and production.

### `DATA_DIR`

Link to directory containing directoris of PubMed it's to be offered
as zip files.

### `DOWNLOAD_PREFIX`

The prefix to use when downloading a zip file.
