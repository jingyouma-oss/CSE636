docker run \
  --name jenkins_blueocean-docker \
  --restart=on-failure \
  --detach \
  --network jenkins \
  --env DOCKER_HOST=tcp://docker:2376 \
  --env DOCKER_CERT_PATH=/certs/client \
  --env DOCKER_TLS_VERIFY=1 \
  --publish 8080:8080 \
  --publish 50000:50000 \
  --volume $HOME/Docker/SharedData/Jenkins/Jenkins_Home:/var/jenkins_home \
  --volume $HOME/Docker/SharedData/Jenkins/Docker-certs:/certs/client:ro \
  cstu-jenkins
