#!/usr/bin/python

import docker
import os
import multiprocessing
import time
import datetime

def log_container(container_name, container_id, service_name, log_folder):

    client = docker.from_env()

    container = client.containers.get(container_id)

    print("[Info]: Process has started for logging the container {}".format(container_name))

    file_path="{}/{}.txt".format(log_folder, container_name)

    with open(file_path, 'a') as outfile:

        os.chmod(file_path, 0o666)

        for line in container.logs(stream=True, follow=True, timestamps=True, since=int(time.time())-1):

            ascii_line = line.decode('ASCII')

            outfile.write("{}".format(ascii_line))

            outfile.flush()

    print("[Info]: Container {} has stopped".format(container_name))

def get_container_id():

    client = docker.from_env()

    hostname = os.uname()[1]  # Get the hostname (which is usually the container ID)

    try:
        # Find the container by its hostname (which matches its ID in most cases)
        container = client.containers.get(hostname)
        return container.id

    except docker.errors.NotFound:

        print("[Error]: Container with hostname {hostname} not found.")
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
        return []

    client = docker.from_env()
    containers_in_project = client.containers.list(
        filters={"label": f"com.docker.compose.project={project_name}"}
    )

    return containers_in_project

if __name__ == "__main__":

    print("[Info]: Starting")

    since_time=time.time()

    try:
        client = docker.from_env()
    except:
        print("[Error]: Can not connect to docker daemon. Have you mounted /var/run/docker.sock ?")
        exit()

    in_compose, project_name, service_name = is_part_of_compose()

    my_container_name = get_container_name()

    if not my_container_name:
        print("[Error]: Could not get my container id. Have you mounted /var/run/docker.sock ?")
        exit()

    if not os.path.exists("/etc/logs"):
        print("[Error]: The directory '/etc/logs' does not exist. Please mount it from outside.")
        exit()

    log_folder = "/etc/logs/"+datetime.datetime.now().replace(microsecond=0).isoformat()

    if not os.path.exists(log_folder):

        os.makedirs(log_folder)

        os.chmod(log_folder, 0o777)

    container_map = {}

    while True:

        time.sleep(1.0)

        containers = list_containers_in_compose_project()

        if containers:

            for container in containers:

                name=container.name
                container_id=container.id
                service_name=container.labels.get('com.docker.compose.service')

                if container_id not in container_map.keys():

                    print("[Info]: New container detected: name={}, id={}, service_name={}".format(name, container_id, service_name))

                    process = multiprocessing.Process(target=log_container, args=(name, container_id, service_name, log_folder))

                    container_map[container_id] = process

                    process.start()

        # marking the processes to be removed for stopped containers

        keys_to_remove = []

        for proc in container_map.keys():

            if not container_map[proc].is_alive():

                print("[Info]: The main process detected that the container {} has died.".format(proc))

                keys_to_remove.append(proc)

        # remove the processes

        for key in keys_to_remove:

            container_map.pop(key)
