import docker  # type: ignore
import time

client = docker.from_env()

IMAGE_NAME = "my-custom-jenkins"
VOLUME_NAME = "jenkins_data_custom"
CONTAINER_NAME = "my-custom-jenkins"
DOCKERFILE_PATH = "." 

# Step 2: Build the custom Jenkins image
print(f"Building image '{IMAGE_NAME}'...")
image, build_logs = client.images.build(path=DOCKERFILE_PATH, tag=IMAGE_NAME)
print("Image built successfully.")

# Step 3: Create volume
try:
    volume = client.volumes.get(VOLUME_NAME)
    print(f"Volume '{VOLUME_NAME}' already exists.")
except docker.errors.NotFound:
    volume = client.volumes.create(name=VOLUME_NAME)
    print(f"Volume '{VOLUME_NAME}' created.")

# Step 4: Run the container
print(f"Running container '{CONTAINER_NAME}'...")
try:
    container = client.containers.run(
        IMAGE_NAME,
        name=CONTAINER_NAME,
        ports={"8080/tcp": 8080},
        volumes={VOLUME_NAME: {'bind': '/var/jenkins_home', 'mode': 'rw'}},
        detach=True
    )
except docker.errors.APIError as e:
    print(f"Error: {e}")
    print("Trying to remove existing container and retry...")
    try:
        old_container = client.containers.get(CONTAINER_NAME)
        old_container.stop()
        old_container.remove()
        container = client.containers.run(
            IMAGE_NAME,
            name=CONTAINER_NAME,
            ports={"8080/tcp": 8080},
            volumes={VOLUME_NAME: {'bind': '/var/jenkins_home', 'mode': 'rw'}},
            detach=True
        )
    except Exception as e2:
        print(f"Failed to recover: {e2}")
        exit(1)

print("Container is starting. Waiting 15 seconds for Jenkins to initialize...")
time.sleep(15)  # Wait for Jenkins to generate password

# Step 5: Get the initial admin password
exec_log = container.exec_run("cat /var/jenkins_home/secrets/initialAdminPassword")
admin_password = exec_log.output.decode().strip()
print(f"\n  Jenkins Initial Admin Password:\n{admin_password}\n")
