Contributors' Guide
===================

[Translating to your own language](#translation) is perhaps the most useful thing you can do for the project currently,
as Amazon rolls out more and more language support for Alexa.

Developing
----------

### Where to start
Generally, have a look at tickets marked [help wanted](https://github.com/declension/squeeze-alexa/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
or [good first issue](https://github.com/declension/squeeze-alexa/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

Generally pull requests are accepted if they:
 * Address a Github issue where the approach has been discussed
 * Pass all automated tests and linting
 * Don't reduce the test coverage
 * Are clearly written, and in a Pythonic way
 * Use the current (ever changing...) best practices for Alexa skills
 * :new: use Python 3.5+ features where appropriate (in particular typing)
   3.6 features can't currently be used for mqtt-squeeze.


### Building

The project is now Python 3.6+ only, and we use ~~Tox~~ ~~Pipenv~~ [Poetry](https://poetry.eustace.io/docs/) (see [#114](https://github.com/declension/squeeze-alexa/issues/114)).


### Testing
We use PyTest and plugins for testing. You can run tests with

```bash
poetry run pytest
```

Testing is very important in this project, and coverage is high.
Please respect this!

Coverage is reported [in Coveralls](https://coveralls.io/github/declension/squeeze-alexa).


### Code Quality

```bash
poetry run flake8 --statistics .
```
No output / error code means everything is good...

### Releasing

This is mostly automated now:
```
bin/build.sh
bin/release.sh 3.0
```
will create `releases/squeeze-alexa-3.0.zip` (hopefully) suitable for upload to Github etc.



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
