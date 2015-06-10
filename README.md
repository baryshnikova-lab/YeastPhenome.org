# YeastPhenome.org

## `yeastphenome/settings.py-template`

`yeastphenome/settings.py-template` needs to be copied to
`yeastphenome/settings.py` and edited to suit your needs.  Currently
there are two added items that isn't a Django standard.  Both are only
refered to in the `paper/models.py` file.

### `METADATA_FILES`

Files that match a paper to its dataset.

### `DATASET_DIR`

Path where to where files pointed to by `METADATA_FILES` are.
