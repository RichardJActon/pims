#!/usr/bin/env bash
MONGODB_HOST="127.0.0.1"
MONGODB_PORT="27017"
 
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
    })" \
  --eval "quit()" 

