#Little script to build everything and launch a server
#(the script is little -- this thing takes fooooorever to build)

docker build -f docker/Dockerfile --build-arg FROM_IMAGE=$1 -t $2 .


