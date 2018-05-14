#! /bin/sh

workon eusocial-pyramid
python ~/Projects/eusocial/api/setup.py test -q -v
