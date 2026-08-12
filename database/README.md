# Mongodb setup

## quickstart

To get a local mongodb instance running for development purposes run the
`setup.sh` script in this directory **from** the project root directory.

NB port 27017 needs to be available and the script will attempt to kill
anything that is using it.

````
./database/setup.sh
````

This will start up a mongodb instance, configure auth,
restart it with auth enabled (apparently the only way to do this),
and create a PIMS user and db.

Variables expected to be defined:

```
PIMS__MONGO__HOST="127.0.0.1"
PIMS__MONGO__PORT="27017"

MONGO_ROOT_USER=root
MONGO_ROOT_PWD=<>
PIMS__MONGO__DATABASE=pims_database
PIMS__MONGO__USER=pimsuser
PIMS__MONGO__PWD=<>
```

I store these in a `.env` file that is sourced when I enter my development shell

To connect to a running instance with the root user:

```
mongosh \
  --host "$PIMS__MONGO__HOST" --port "$PIMS__MONGO__PORT" \
  -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PWD" \
  --authenticationDatabase admin
```

## Notes

It does not appear possible to start mongodb with authentication pre-configured
It must be started, accessed over local host, have users and credentials defined,
then it can be restarted and authentication/authorisation can then be enforced based on the previously defined credentials and roles.

(This seems like bad design but I can't seem to find a way of doing this declaratively)

Note that Even after this is configured you still seem to be able to connect to the databse but are just not able to perform any actions as an unauthenticated user.

NB `database/dbdata` & `database/nohup.out` should be in in the `.gititnore`

Scripts can be executed on a mongodb instance via the `mongosh` cli client

```
mongosh --host 127.0.0.1 --file example.js
```

Or executed directly:

```
mongosh --host 127.0.0.1 --eval 'use admin'
```

I was having issue with reading environment variables in scripts passed as files to mongosh.

Credentials should only be ephemorally available in environment variables in the shell from which this script is run

Create the the admin database and user:

```
use admin
db.createUser({
  user: process.env.MONGO_ROOT_USER,
  pwd: process.env.MONGO_ROOT_PWD,
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"],
})
quit()
```

Create the pims user and database seperately using the root credentials:

```
use process.env.PIMS__MONGO__DATABASE
db.createUser({
  user: process.env.PIMS__MONGO__USER,
  pwd: process.env.PIMS__MONGO__PWD,
  roles: ["dbAdmin", "readWrite"],
})
quit()
```

Subsequent mongodb actions should only need the pims user's permissions.
So configuring like this should mean that any attempts to perform mongodb
actions which require other permissions will fail as they would in production.

bash script to clean and previous state and re-provision a clean database for development:

- kill any running mongo processes
- clear old database files
- start mongod
- configure auth
  - Note: May not need root user with these expansive permissions to exist,
    no user may need to exist with priviledges on databases other than the application database
- kill mongod
- start mongod in the background with auth enforced
- connect with root credentials
- create pims user, db, & set permissions

(NB use subprocess to & sigterm to improve portability when running the mongod commands from the script)

Note that collections created in mongodb need to have something in them for their namespace to persist,
they cannot be empty or they disappear.


