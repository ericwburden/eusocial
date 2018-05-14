#! /bin/sh
rm nohup.out
touch nohup.out
echo "$(date) $line" >> nohup.out

nohup npm start --prefix ~/Projects/eusocial/gui/ &

python3 ~/Projects/eusocial/tools/test_db.py

export FLASK_APP=../api/api.py
export FLASK_DEBUG=1
nohup flask run &
