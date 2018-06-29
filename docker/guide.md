docker build -t mycontainer .
docker run --name mycontainer -p 5000:5000 mycontainer --network host
