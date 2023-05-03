#Little script to build everything and launch a server
#(the script is little -- this thing takes fooooorever to build)

#Build a heavyweight version
docker build -f docker/Dockerfile -t $1 --build-arg FROM_IMAGE=$2 .

#Build the lightweight version
docker build -f docker/Dockerfile -t $3 . 


