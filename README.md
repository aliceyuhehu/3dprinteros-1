### Setting up the App
You will need both docker and docker compose installed

1. `docker-compose build`
2. `docker-compose up`
3. `docker-compose exec mongo bash`
4. `mongosh --username root --password` (password: example )
5.  `use development`
6. `db.sandbox.insertOne({"name": "init"});`
7. 
```
db.createUser({
  user: "colab",
  pwd: "example",
  roles: [
    { role: "dbOwner", db: "development" },
    { role: "readWrite", db: "development" }
  ]
});
```
8.`mongosh --username colab --password --authenticationDatabase development`



example of how to port foward to mongodb so you can connect with compass
`oc get pods | grep mongo` find the pod name
`oc port-forward mongodb-1-7nm2f 27017:27017`
