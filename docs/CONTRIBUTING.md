Contributors' Guide
===================

Developing
----------

### Building

The project is now Python 3.6+ only, and we use Pipenv (not Tox).


### Testing
We use PyTest and plugins for testing. You can run tests with

```bash
pipenv run pytest
```

Testing is very important in this project, and coverage is high.
Please respect this!

Coverage is reported [in Coveralls](https://coveralls.io/github/declension/squeeze-alexa).


### Code Quality

```bash
pipenv run flake8 --statistics .
```
No output / error code means everything is good...

### Releasing

This is crudely semi-automated now:
```
bin/create_zip.sh release 1.3
```
will create `squeeze-alexa-1.3.zip` (hopefully) suitable for upload to Github etc.



Translation
-----------

squeeze-alexa uses [GNU gettext](https://www.gnu.org/software/gettext/) for its _output_.
It's a little old-fashioned / troublesome at first, but it serves its purposes well.


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

#### Update translations from source
This re-scans the source and recreates a master `.pot` file, before then updating the translations files (`.po`s).

```bash
bin/update-translations
```

#### Translate your .po
You can edit the using any text editor, or use PoEdit, or any other gettext tools e.g.

 * [PoEdit](https://poedit.net/)
 * [GTranslator](https://wiki.gnome.org/Apps/Gtranslator)
 * [Virtaal](http://virtaal.translatehouse.org/download.html)

### Compile translations
This takes the `.po`s and makes binary `.mo`s that are necessary for gettext to work.
```bash
bin/compile-translations
```

### Add utterances and slots
Amazon changed the way they handle interaction. The original way (v0) used separate input for slots and utterances.
In [interaction model v1](https://developer.amazon.com/docs/smapi/interaction-model-schema.html#sample-interaction-model-schema), among other changes, they've merged this into one big JSON which is probably easier in the long run.

squeeze-alexa (documentation) now "supports" both

#### v0 schema
 * Refer to the v0 [intents.json](../metadata/intents/v0/intents.json).
 * Add an `utterances.txt` in the right locale directory e.g. `metadata/intents/v0/locale/pt_BR/utterances.txt` (see [German example](https://github.com/declension/squeeze-alexa/blob/master/metadata/intents/v0/locale/de_DE/utterances.txt))
 * Optional: do the same for the SLOT (genres, playlist names, player names etc)

#### ...or v1 schema
 * Create a new locale directory, e.g. `pt_BR` under `metadata/v1/locale`.
 * Translate the whole English file [v1 intents.json](../metadata/intents/v1/locale/en_US) to a copy of the same name under that new directory.


#### Submit the translations
 * Hopefully you opened a Github issue - if not, do this.
 * Either
   * attach the updated `.po` and utterances / intents files, or
   * create a fork in Github, branch, commit your new file(s) in Git, then make a Pull Request, mentioning the ticket number.


### Translation FAQ

#### Everything's still in US English
 * Make sure you've set `LOCALE` in `settings.py`.
 * Make sure the directory is setup as above and you've definitely compiled it (i.e. there's a `.mo` file)
 * New versions of `squeeze-alexa` default to the source language (`en_US`) if there is no translation found.

#### What if I don't translate some strings?
No problem. They'll come out in the source language (`en` here).

#### I'm getting "invalid multibyte sequence" errors
This `.po` header is probably missing:

    msgid ""
    msgstr ""
    "Content-Type: text/plain; charset=UTF-8\n"

#### There are newlines I didn't expect
`xgettext` reformats source files to a maximum line width according to its settings.
See [`update-translations`](../bin/update-translations) for the setup.
