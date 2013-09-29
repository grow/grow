printf '\n --- \n'

curl \
-H 'content-type:application/json' \
-d '{}' \
http://localhost:8080/_api/protorpc.services

printf '\n --- \n'

curl \
-H 'content-type:application/json' \
-d '{"names": ["/_api/pods.*"]}' \
http://localhost:8080/_api/protorpc.get_file_set


curl \
-H 'content-type:application/json' \
-d '{"names": ["/_api/pods.*"]}' \
http://localhost:8080/_api/protorpc.get_file_set

printf '\n --- \n'
