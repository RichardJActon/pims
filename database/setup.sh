#!/usr/bin/env bash
kill $mongodbpid
cd database
rm -rf dbdata/
mkdir dbdata
mongod --config mongodb.conf &
mongodpid=$!
mongosh --host 127.0.0.1 --file setup.js
kill $mongodpid
nohup mongod --config mongodb.conf &
export mongodpid=$!
echo $mongodpid
mongosh --host 127.0.0.1 -u $MONGO_ROOT_USER -p $MONGO_ROOT_PWD --file pims_db_setup.js
