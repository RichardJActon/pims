# Mongodb setup

It does not appear possible to start mongodb with authentication pre-configured
It must be started, accessed over local host, have users and credentials defined,
then it can be restarted and authentication/authorisation can then be enforced based on the previously defined credentials and roles.

(This seems like bad design but I can't seem to find a way of doing this declaratively)

Note that Even after this is configured you still seem to be able to connect to the databse but are just not able to perform any actions as an unauthenticated user.

It is possible to provide `mongod` with some configureation from a file on startup:

```
mongod --config database/mongodb.conf
```

`mongodb.conf`:

```
# processManagement:
#     fork: true # background the process by default
net:
    bindIp: localhost # other interfaces can be listed here space seperated
    port: 27017
storage:
    dbPath: dbdata
systemLog:
    destination: file
    path: dbdata/mongod.log
    logAppend: true
security:
    authorization: enabled # Only connections on localhost *should* be able to perform any actions by default
```

`database/dbdata` should be in in the `.gititnore`

Scripts can also be executed on a mongodb instance via the `mongosh` cli client

```
mongosh --host 127.0.0.1 --file setup.js
```

Credentials should only be ephemorally available in environment variables in the shell from which this script is run

Variables expected to be defined:

```
MONGO_ROOT_USER=root
MONGO_ROOT_PWD=<>
MONGO_DATABASE=pims_database
MONGO_PIMS_USER=pimsuser
MONGO_PIMS_USER_PWD=<>
```

Create the the admin database and user with `setup.js`:

```
use admin
db.createUser({
  user: process.env.MONGO_ROOT_USER,
  pwd: process.env.MONGO_ROOT_PWD,
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"],
})
quit()
```

Create the pims user and database seperately using the root credentials `pims_db_setup.js`:

```
use process.env.MONGO_DATABASE
db.createUser({
  user: process.env.MONGO_PIMS_USER,
  pwd: process.env.MONGO_PIMS_USER_PWD,
  roles: ["dbAdmin", "readWrite"],
})
quit()
```

Subsequent mongodb actions should only need the pims user's permissions so configuring like this should mean that any attempts to perform mongodb actions which require other permissions will fail as they would in production.

bash script to clean and previous state and re-provision a clean database for development

- kill any running mongo processes
- clear old database files
- start mongod
- configure auth
  - May not need root user with these expansive permissions to exist, no user may need to exist with priviledges on databases other than the application database
- kill mongod
- start mongod in the background with auth enforced
- connect with root credentials
- create pims user, db, & set permissions

(NB use subprocess to & sigterm to improve portability when running the mondod commands from the script)

Note that collections created in mongodb need to have something in them for their namespace to persist, they cannot be empty or they disappear.



setup.sh

```
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
```
