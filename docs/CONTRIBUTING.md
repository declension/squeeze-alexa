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
This re-scans the source and recreates a master `.pot` file, before then updating the translations files (`.po`s).

```bash
bin/update-translations
```

### Compile translations
This takes the `.po`s and makes binary `.mo`s that are necessary for gettext to work.
```bash
bin/compile-translations
```


### I have a new language
Great! Follow these steps (imagine you are choosing Brazilian Portuguese, `pt_BR`):

#### Create a directory

```bash
cd locale
LOCALE=pt_BR
mkdir -p $LOCALE/LC_MESSAGES
```

#### Generate a blank PO file
```bash
DOMAIN=squeeze-alexa
touch $LOCALE/LC_MESSAGES/$DOMAIN.po
```

#### Update the translations from source
(see above)

#### Translate your .po
You can edit the using any text editor, or use PoEdit, or any other gettext tools e.g.

 * [PoEdit](https://poedit.net/)
 * [GTranslator](https://wiki.gnome.org/Apps/Gtranslator)
 * [Virtaal](http://virtaal.translatehouse.org/download.html)

#### Submit the translation
 * Hopefully you opened a Github issue - if not, do this.
 * Either attach the updated `.po`, or create a fork in Gibhut, branch, commit your new file(s) in Git, then make a Pull Request, mentioning the ticket number.
