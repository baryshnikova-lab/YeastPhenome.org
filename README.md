# YeastPhenome.org

## `yeastphenome/settings.py-template`

`yeastphenome/settings.py-template` needs to be copied to
`yeastphenome/settings.py` and edited to suit your needs.  Currently
there are two added items that isn't a Django standard.  Both are only
refered to in the `paper/models.py` file.

### `METADATA_DIR`

Reads in all *.m files in this directory to associate papers to data.

### `DATASET_DIR`

Where to look for the data refered to in `METADATA_DIR` is located.
