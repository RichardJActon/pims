#!/usr/bin/env bash
if [[ -z "$PIMS__MONGO__HOST" ]]; then
  echo "PIMS__MONGO__HOST is not defined!"
  exit 1
fi

if [[ -z "$PIMS__MONGO__PORT" ]]; then
  echo "PIMS__MONGO__PORT is not defined!"
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

if [[ -z "$PIMS__MONGO__USER" ]]; then
  echo "PIMS__MONGO__USER is not defined!"
  exit 1
fi

if [[ -z "$PIMS__MONGO__PWD" ]]; then
  echo "PIMS__MONGO__PWD is not defined!"
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
echo "killing any process using port: $PIMS__MONGO__PORT"
fuser -k "$PIMS__MONGO__PORT/tcp"
echo "starting first MongoDB instance to configure auth"
# mongod --config mongodb.conf &
mongod \
  --bind_ip "$PIMS__MONGO__HOST" --port "$PIMS__MONGO__PORT" \
  --logappend --logpath database/dbdata/mongod.log \
  --dbpath database/dbdata \
  &
# mongodpid=$!

echo "config admin user"
mongosh \
  --host "$PIMS__MONGO__HOST" --port "$PIMS__MONGO__PORT" \
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
#   --host "$PIMS__MONGO__HOST" --port "$PIMS__MONGO__PORT" \
#   --file database/setup.js

# echo "kill first MongoDB instance PID $mongodpid"
# kill "$mongodpid"

# Initial MongoDB instance does not immediately relinquish the port so
# when starting a new instance it can fail as it cannot bind the port.
# To prevent this we firt make sure that the port is freed.
echo "killing any process still using port: $PIMS__MONGO__PORT"
fuser -k "$PIMS__MONGO__PORT/tcp"

echo "start with auth enforcement on"
nohup mongod \
  --bind_ip "$PIMS__MONGO__HOST" --port "$PIMS__MONGO__PORT" \
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
  --host "$PIMS__MONGO__HOST" --port "$PIMS__MONGO__PORT" \
  -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PWD" \
  --authenticationDatabase admin \
  --eval "use admin" \
  --eval "db.createUser({
      user: \"$PIMS__MONGO__USER\",
      pwd: \"$PIMS__MONGO__PWD\",
      roles: [
        {role: 'dbAdmin', db: \"$PIMS__MONGO__DATABASE\"},
        {role: 'readWrite', db: \"$PIMS__MONGO__DATABASE\"}
      ]
    })"

echo "Create test users"

# NB add validator to people collection:
# https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema/#std-label-schema-validation-json
# better examples than in the docs:
# https://jsonic.io/guides/json-schema-mongodb

mongosh \
  --host "$PIMS__MONGO__HOST" --port "$PIMS__MONGO__PORT" \
  -u "$PIMS__MONGO__USER" -p "$PIMS__MONGO__PWD" \
  --authenticationDatabase admin \
  --eval "use $PIMS__MONGO__DATABASE" \
  --eval "db.createCollection('people_collection', {
      validator: {
        \$jsonSchema: {
          bsonType: 'object',
          title: 'Person',
          required: ['name', 'username', 'is_admin', 'email', 'disabled'],
          properties: {
            name: {
              bsonType: 'string',
              description: ''
            },
            username: {
              bsonType: 'string',
            },
            is_admin: {
              bsonType: 'bool'
              
            },
            email: {
              bsonType: 'string',
              
            },
            disabled: {
              bsonType: 'bool'
              
            }
          },
          additionalProperties: true
        }
      },
      validationLevel: 'strict',
      validationAction: 'error'
    }
  )" \
  --eval "db.people_collection.insertOne({
    'name': 'admin',
    'username': 'admin',
    'is_admin': true,
    'email': 'admin@test.com',
    'disabled': false,
    'failed_logins': []
  })" \
  --eval "db.people_collection.insertOne({
    'name': 'test',
    'username': 'test',
    'is_admin': false,
    'email': 'test@test.com',
    'disabled': false,
    'failed_logins': []
  })"
  
exit 1

