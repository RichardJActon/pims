#!/usr/bin/env bash
# MONGODB_HOST="127.0.0.1"
# MONGODB_PORT="27017"
if [[ -z "$MONGODB_HOST" ]]; then
  echo "MONGODB_HOST is not defined!"
  exit 1
fi

if [[ -z "$MONGODB_PORT" ]]; then
  echo "MONGODB_PORT is not defined!"
  exit 1
fi

if [[ -z "$MONGO_ROOT_USER" ]]; then
  echo "MONGO_ROOT_USER is not defined!"
  exit 1
fi

if [[ -z "$MONGO_ROOT_PWD" ]]; then
  echo "MONGO_ROOT_PWD is not defined!"
  exit 1
fi

if [[ -z "$MONGO_PIMS_USER" ]]; then
  echo "MONGO_PIMS_USER is not defined!"
  exit 1
fi

if [[ -z "$MONGO_PIMS_USER_PWD" ]]; then
  echo "MONGO_PIMS_USER_PWD is not defined!"
  exit 1
fi

if [[ $mongodpid ]]; then
  echo "'mongodpid' is defined - killing existing mongodb process"
  kill "$mongodpid"
fi
if [[ -d database ]]; then
  echo "moving into database dir"
  cd database || exit
else
  echo "database directory does not exist."
  echo "please run this script from the project parent directory!"
  echo "bash database/setup.sh"
  exit 1
fi
if [[ -d dbdata ]]; then
echo "removing exist dbdata"
rm -rf dbdata/
fi
echo "creating dbdata directory"
mkdir dbdata
echo "moving out of database dir"
cd ..
echo "initial database setup:"
echo "killing any process using port: $MONGODB_PORT"
fuser -k "$MONGODB_PORT/tcp"
echo "starting first MongoDB instance to configure auth"
# mongod --config mongodb.conf &
mongod \
  --bind_ip "$MONGODB_HOST" --port "$MONGODB_PORT" \
  --logappend --logpath database/dbdata/mongod.log \
  --dbpath database/dbdata \
  &
# mongodpid=$!

echo "config admin user"
mongosh \
  --host "$MONGODB_HOST" --port "$MONGODB_PORT" \
  --eval 'use admin' \
  --eval 'db.createUser({
    user: process.env.MONGO_ROOT_USER,
    pwd: process.env.MONGO_ROOT_PWD,
    roles: [
      {role: "userAdminAnyDatabase", db: "admin"},
      {role: "dbAdminAnyDatabase", db: "admin"},
      {role: "readWriteAnyDatabase", db: "admin"},
    ]
  })'
      # {role: "userAdmin", db: "admin"},
      # {role: "dbAdmin", db: "admin"},
      # {role: "readWrite", db: "admin"},
      # {role: "readWrite", db: "test"}
      # {role: "root", db: "admin"},
      # {role: "dbOwner", db: "admin"},
#  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]

# echo "config admin user"
# mongosh \
#   --host "$MONGODB_HOST" --port "$MONGODB_PORT" \
#   --file database/setup.js

# echo "kill first MongoDB instance PID $mongodpid"
# kill "$mongodpid"

# Initial MongoDB instance does not immediately relinquish the port so
# when starting a new instance it can fail as it cannot bind the port.
# To prevent this we firt make sure that the port is freed.
echo "killing any process still using port: $MONGODB_PORT"
fuser -k "$MONGODB_PORT/tcp"

echo "start with auth enforcement on"
nohup mongod \
  --bind_ip "$MONGODB_HOST" --port "$MONGODB_PORT" \
  --logappend --logpath database/dbdata/mongod.log \
  --dbpath database/dbdata \
  --setParameter enableLocalhostAuthBypass=false \
  --auth >/dev/null 2>&1 &

# nohup mongod --config mongodb.conf &

# export mongodpid=$!
# if [ -d "/proc/$mongodpid" ]; then
#   echo "persistent mongodb instance PID:"
#   echo "$mongodpid"
# fi
# 
disown
 
echo "logging in as root user to create pims user and DB"

mongosh \
  --host "$MONGODB_HOST" --port "$MONGODB_PORT" \
  -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PWD" \
  --authenticationDatabase admin \
  --eval "use $MONGO_DATABASE" \
  --eval "db.createUser({
      user: \"$MONGO_PIMS_USER\",
      pwd: \"$MONGO_PIMS_USER_PWD\",
      roles: ['dbAdmin', 'readWrite']
    })"
    
exit 1
