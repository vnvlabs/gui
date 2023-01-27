#Little script to build everything and launch a server
#(the script is little -- this thing takes fooooorever to build)

docker build -f docker/Dockerfile -t $1 .


