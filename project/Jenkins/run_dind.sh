docker run \
  --name jenkins-docker \
  --rm \
  --detach \
  --privileged \
  --network jenkins \
  --network-alias docker \
  --env DOCKER_TLS_CERTDIR=/certs \
  --volume $HOME/Docker/SharedData/Jenkins/Jenkins_Home:/var/jenkins_home \
  --volume $HOME/Docker/SharedData/Jenkins/Docker-certs:/certs/client:ro \
  --publish 2376:2376 \
  docker:dind \
  --storage-driver overlay2
