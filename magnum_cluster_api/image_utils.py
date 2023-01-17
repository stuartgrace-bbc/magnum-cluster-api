import yaml


def update_manifest_images(cluster_uuid: str, file, repository=None, replacements=[]):
    with open(file) as fd:
        data = fd.read()

    docs = []
    for doc in yaml.safe_load_all(data):
        # Fix container image paths
        if doc["kind"] in ("DaemonSet", "Deployment"):
            for container in doc["spec"]["template"]["spec"]["containers"]:
                for src, dst in replacements:
                    container["image"] = container["image"].replace(src, dst)
                if repository:
                    container["image"] = get_image(container["image"], repository)

        # Fix CCM cluster-name
        if (
            doc["kind"] == "DaemonSet"
            and doc["metadata"]["name"] == "openstack-cloud-controller-manager"
        ):
            for env in doc["spec"]["template"]["spec"]["containers"][0]["env"]:
                if env["name"] == "CLUSTER_NAME":
                    env["value"] = cluster_uuid

        docs.append(doc)

    return yaml.safe_dump_all(docs, default_flow_style=False)


def get_image(name: str, repository: str = None):
    """
    Get the image name from the target registry given a full image name.
    """

    if repository is None:
        return repository

    new_image_name = name
    if name.startswith("docker.io/calico"):
        new_image_name = name.replace("docker.io/calico/", f"{repository}/calico-")
    if name.startswith("docker.io/k8scloudprovider"):
        new_image_name = name.replace("docker.io/k8scloudprovider", repository)
    if name.startswith("k8s.gcr.io/sig-storage"):
        new_image_name = name.replace("k8s.gcr.io/sig-storage", repository)
    if new_image_name.startswith(f"{repository}/livenessprobe"):
        return new_image_name.replace("livenessprobe", "csi-livenessprobe")
    if new_image_name.startswith("k8s.gcr.io/coredns"):
        return new_image_name.replace("k8s.gcr.io/coredns", repository)
    if (
        new_image_name.startswith("k8s.gcr.io/etcd")
        or new_image_name.startswith("k8s.gcr.io/kube-")
        or new_image_name.startswith("k8s.gcr.io/pause")
    ):
        return new_image_name.replace("k8s.gcr.io", repository)

    assert new_image_name.startswith(repository) is True
    return new_image_name