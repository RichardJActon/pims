use process.env.MONGO_DATABASE
db.createUser({
  user: process.env.MONGO_PIMS_USER,
  pwd: process.env.MONGO_PIMS_USER_PWD,
  roles: ["dbAdmin", "readWrite"],
})
quit()
