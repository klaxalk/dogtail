#!/usr/bin/python

import docker
import os
import multiprocessing
import time
import datetime

def log_container(container_name, container_id, service_name, log_folder, since_time):

    client = docker.from_env()

    container = client.containers.get(container_id)

    print("starting logging of {}, {}, {}", container_name, container_id, service_name)

    file_path="{}/{}.txt".format(log_folder, service_name)

    with open(file_path, 'a') as outfile:

        os.chmod(file_path, 0o666)

        for line in container.logs(stream=True, follow=True, since=int(since_time)-1):

            ascii_line = line.decode('ASCII')

            outfile.write("[{:.6f}]: {}".format(time.time(), ascii_line))

            outfile.flush()

def get_container_id():
    """Retrieve the container ID from /proc/self/cgroup."""
    with open('/proc/self/cgroup', 'r') as f:
        for line in f:
            if 'docker' in line:
                return line.strip().split('/')[-1]
    return None

def get_container_name():
    container_id = get_container_id()  # Get the container ID
    if container_id:
        client = docker.from_env()  # Create a Docker client
        try:
            container = client.containers.get(container_id)  # Get the container by its ID
            return container.name  # Return the container's name
        except docker.errors.NotFound:
            return None  # Handle if the container is not found
    return None

def is_part_of_compose():
    """Check if the container is part of a Docker Compose session using labels."""
    container_id = get_container_id()
    if container_id:
        client = docker.from_env()
        try:
            container = client.containers.get(container_id)
            labels = container.labels  # Get the container's labels
            project_name = labels.get('com.docker.compose.project')
            service_name = labels.get('com.docker.compose.service')
            if project_name and service_name:
                return True, project_name, service_name
        except docker.errors.NotFound:
            return False, None, None
    return False, None, None

def get_compose_project_name():
    """Get the Docker Compose project name from the container's labels."""
    container_id = get_container_id()
    if container_id:
        client = docker.from_env()
        try:
            container = client.containers.get(container_id)
            project_name = container.labels.get('com.docker.compose.project')
            return project_name
        except docker.errors.NotFound:
            return None
    return None

def list_containers_in_compose_project():
    """List all containers in the same Docker Compose project."""
    project_name = get_compose_project_name()  # Get the current container's project name
    if not project_name:
        print("This container is not part of a Docker Compose session.")
        return []

    client = docker.from_env()
    containers_in_project = client.containers.list(
        filters={"label": f"com.docker.compose.project={project_name}"}
    )

    return containers_in_project

if __name__ == "__main__":

    print("[Info]: starting")

    since_time=time.time()

    try:
        client = docker.from_env()
    except:
        print("[Error]: can not connect to docker daemon. Have you monted the docker sock?")
        exit()

    in_compose, project_name, service_name = is_part_of_compose()

    my_container_name = get_container_name()

    if not os.path.exists("/etc/logs"):
        print("[Error]: the directory '/etc/logs' does not exist. Please mount it as a docker volume from outside.")
        exit()

    log_folder = "/etc/logs/"+datetime.datetime.now().replace(microsecond=0).isoformat()

    if not os.path.exists(log_folder):

        os.makedirs(log_folder)

        os.chmod(log_folder, 0o777)

    print("my_container_name: {}".format(my_container_name))

    container_map = {}

    while True:

        time.sleep(1.0)

        containers = list_containers_in_compose_project()

        if containers:

            for container in containers:

                if container.name != my_container_name:

                    name=container.name
                    container_id=container.id
                    service_name=container.labels.get('com.docker.compose.service')

                    if container_id not in container_map.keys():

                        print("New container detected: {}, {}, {}".format(name, container_id, service_name))

                        process = multiprocessing.Process(target=log_container, args=(name, container_id, service_name, log_folder, since_time))

                        container_map[container_id] = process

                        process.start()

        else:
            print("No other containers found in the same Compose project.")
