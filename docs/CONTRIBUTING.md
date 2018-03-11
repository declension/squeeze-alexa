Contributors' Guide
===================

Developing
----------

### Testing
Testing is very important in this project, and coverage is high.
Please respect this!

For tooling, we use [tox](https://tox.readthedocs.io/en/latest/). Just run `tox`.



Translation
-----------

squeeze-alexa uses [GNU gettext](https://www.gnu.org/software/gettext/).
It's a little old-fashioned / troublesome at first, but it serves its purposes well.

### I want to translate
Great! I wrote a script to help with that:

#### Update translations from source
This re-scans the source and recreates the master `.pot` file, before then updating the translations files (`.po`s).

```bash
bin/update-translations
```

### Compile translations
This takes the `.po`s and makes binary `.mo`s that are necessary for gettext to work.
```bash
bin/update-translations
```


### I have a new language
Great! Follow these steps (imagine you are choosing Brazilian Portuguese, `pt_BR`):

#### Create a directory

```bash
cd locales
LOCALE=pt_BR
mkdir -p $LOCALE/LC_MESSAGES
```

#### Generate a blank PO file with `xgettext`
```bash
DOMAIN=squeeze-alexa
LOCALE=pt_BR
find squeezealexa -iname '*.py' | xargs xgettext --omit-header --package-name $DOMAIN -o locale/$LOCALE/LC_MESSAGES/$DOMAIN.po -d $DOMAIN
```

#### Update the translations
(see above)

