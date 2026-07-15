# Docker Registry Tutorial

> A hands-on guide to storing and sharing Docker images — using a **local registry** on port `5000` and a **private repository on Docker Hub** (`hub.docker.com`).
>
> Companion to the Docker cheat sheets in this folder. Pairs with **Week 1 (Docker foundations)** of CSE636.

---

## 🎯 At a glance

| | |
|---|---|
| **You'll learn** | What a registry is, how to run one locally, and how to use a private repo on Docker Hub |
| **Core verbs** | `docker tag` → `docker push` → `docker pull` |
| **Prerequisites** | Docker installed and running (`docker version`); a free Docker Hub account for the Hub section |
| **Time** | ~30 minutes |

---

## 1. Concepts: image, repository, registry, tag

These four words get used interchangeably and cause endless confusion. Precise definitions:

- **Image** — a built, immutable filesystem + metadata (e.g. the thing `docker build` produces).
- **Repository** — a named collection of related images (usually different versions of one app), e.g. `myapp`.
- **Registry** — a *server* that hosts repositories. Docker Hub is a registry. So is a container you run locally on port 5000. So are GitHub Container Registry, Amazon ECR, Google Artifact Registry, etc.
- **Tag** — a human-readable pointer to a specific image inside a repository, e.g. `myapp:1.0`. If you omit the tag, Docker assumes `:latest`.

### How Docker parses an image name

A fully-qualified image reference looks like this:

```
[REGISTRY_HOST[:PORT]/]REPOSITORY[:TAG]
   └─────────────┘      └────────┘ └───┘
     where it lives      what it is  which version
```

Examples:

| Reference | Registry | Repository | Tag |
|---|---|---|---|
| `nginx` | Docker Hub (implied) | `library/nginx` | `latest` |
| `myuser/myapp:1.2` | Docker Hub (implied) | `myuser/myapp` | `1.2` |
| `localhost:5000/myapp:1.0` | `localhost:5000` (local registry) | `myapp` | `1.0` |
| `ghcr.io/org/tool:v3` | `ghcr.io` | `org/tool` | `v3` |

> 🔑 **The key rule:** if the name before the first `/` contains a `.`, a `:`, or is `localhost`, Docker treats it as a **registry host**. Otherwise it assumes **Docker Hub**. This is why `localhost:5000/myapp` goes to your local registry but `myuser/myapp` goes to Docker Hub.

---

## 2. Local registry on port 5000

Docker publishes an official registry image. You run it as a container, and it becomes a registry listening on `localhost:5000`.

### 2.1 Run the registry

```bash
docker run -d \
  -p 5000:5000 \
  --restart=always \
  --name local-registry \
  registry:2
```

- `-d` — run detached (in the background)
- `-p 5000:5000` — publish the registry's port 5000 to your host
- `--restart=always` — bring it back automatically after a reboot / Docker restart
- `--name local-registry` — a friendly name so you can `docker stop local-registry` later

Verify it's up:

```bash
docker ps --filter name=local-registry
curl http://localhost:5000/v2/_catalog       # -> {"repositories":[]}  (empty for now)
```

> 💾 **Where do the images go?** By default they live inside the container and vanish when it's removed. To persist them on your host, mount a volume:
>
> ```bash
> docker run -d -p 5000:5000 --restart=always \
>   --name local-registry \
>   -v "$PWD/registry-data:/var/lib/registry" \
>   registry:2
> ```

### 2.2 Tag an image for the local registry

You can't push an arbitrary image name to a registry — the name itself must point at the registry. Take any image you have (we'll grab `hello-world`) and give it a new tag that starts with `localhost:5000/`:

```bash
docker pull hello-world                                   # get something to push
docker tag hello-world localhost:5000/hello-world:1.0
```

`docker tag SOURCE TARGET` doesn't copy or rebuild anything — it just adds a second name pointing at the same image ID. Confirm:

```bash
docker images | grep hello-world
# hello-world                  latest   ...  <same IMAGE ID>
# localhost:5000/hello-world   1.0      ...  <same IMAGE ID>
```

### 2.3 Push the image to the local registry

```bash
docker push localhost:5000/hello-world:1.0
```

Confirm it landed:

```bash
curl http://localhost:5000/v2/_catalog
# {"repositories":["hello-world"]}

curl http://localhost:5000/v2/hello-world/tags/list
# {"name":"hello-world","tags":["1.0"]}
```

### 2.4 Pull the image from the local registry

To prove the pull works, first delete the local copies, then pull it back from the registry:

```bash
docker rmi localhost:5000/hello-world:1.0 hello-world     # remove local copies
docker pull localhost:5000/hello-world:1.0                # fetch it from the registry
docker run --rm localhost:5000/hello-world:1.0            # run it to prove it works
```

### 2.5 Tear down

```bash
docker stop local-registry && docker rm local-registry
# add: rm -rf registry-data   # if you mounted a volume and want the images gone too
```

---

## 3. Private repository on Docker Hub (`hub.docker.com`)

Docker Hub is the default public registry, but every account also gets **private repositories** (one free private repo on the free tier; unlimited on paid). A private repo requires authentication to push *and* pull.

> **Setup once:** create a free account at [hub.docker.com](https://hub.docker.com), then create a repository (**Repositories → Create repository**), name it e.g. `myapp`, and set its visibility to **Private**. Your username is your Docker Hub ID — we'll use `myuser` as a placeholder below.

### 3.1 Log in

```bash
docker login
# Username: myuser
# Password: <your password or, better, an access token>
```

> 🔐 **Use an access token, not your password.** In Docker Hub: **Account Settings → Personal access tokens → Generate**. Paste the token as the password. Tokens can be scoped and revoked without changing your account password — this is the recommended practice, especially in CI.

Credentials are cached in `~/.docker/config.json` so you only log in once per machine.

### 3.2 Tag the image for your Docker Hub repo

On Docker Hub, the repository name **must** be prefixed with your username: `USERNAME/REPOSITORY`.

```bash
docker tag hello-world myuser/myapp:1.0
```

### 3.3 Push to Docker Hub

```bash
docker push myuser/myapp:1.0
```

The image now appears under **Repositories → myapp** in the Hub UI with the `1.0` tag. Because the repo is private, no one can pull it without being logged in and authorized.

### 3.4 Pull from Docker Hub

From any machine that is logged in (`docker login`) with access to the repo:

```bash
docker pull myuser/myapp:1.0
docker run --rm myuser/myapp:1.0
```

If you try to pull a private image without authenticating, you'll get `pull access denied ... repository does not exist or may require 'docker login'`.

### 3.5 Log out (e.g. on a shared machine)

```bash
docker logout
```

---

## 4. Other common scenarios

### 4.1 Push multiple tags (versioned + `latest`)

A common release pattern is to publish both a specific version and move `latest` to point at it:

```bash
docker tag myapp:build myuser/myapp:1.4.0
docker tag myapp:build myuser/myapp:latest
docker push myuser/myapp:1.4.0
docker push myuser/myapp:latest
# or push every tag in the repo at once:
docker push --all-tags myuser/myapp
```

### 4.2 Promote an image between registries

You often build once, then copy the *same* image to different registries (e.g. from a local/dev registry to Docker Hub) — no rebuild, just retag and push:

```bash
docker pull localhost:5000/myapp:1.0        # get it from the local registry
docker tag  localhost:5000/myapp:1.0 myuser/myapp:1.0
docker push myuser/myapp:1.0                # publish to Docker Hub
```

### 4.3 Inspect a registry without pulling

The registry HTTP API (v2) lets you browse without downloading images:

```bash
# Local registry
curl http://localhost:5000/v2/_catalog                    # list repositories
curl http://localhost:5000/v2/myapp/tags/list             # list tags in a repo

# Docker Hub (public API, no client needed for public repos)
curl -s https://hub.docker.com/v2/repositories/library/nginx/tags/ | jq '.results[].name'
```

### 4.4 Delete images from a registry

- **Docker Hub:** delete a tag or repository from the web UI (**Repositories → … → Settings/Delete**), or via the Hub API.
- **Local registry:** deletion is disabled by default. Enable it, delete by *digest*, then garbage-collect to reclaim disk:

```bash
# 1. Run the registry with deletion enabled
docker run -d -p 5000:5000 --name local-registry \
  -e REGISTRY_STORAGE_DELETE_ENABLED=true \
  -v "$PWD/registry-data:/var/lib/registry" \
  registry:2

# 2. Find the digest of the tag
curl -sI -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  http://localhost:5000/v2/myapp/manifests/1.0 | grep -i Docker-Content-Digest
# -> Docker-Content-Digest: sha256:abc123...

# 3. Delete the manifest by digest
curl -X DELETE http://localhost:5000/v2/myapp/manifests/sha256:abc123...

# 4. Reclaim disk space
docker exec local-registry registry garbage-collect /etc/docker/registry/config.yml
```

### 4.5 Secure a local registry (TLS + basic auth)

The plain `registry:2` on port 5000 is fine for a laptop demo but is **insecure** (HTTP, no auth). For anything shared, add basic auth and TLS:

```bash
# Create a password file (htpasswd from the registry image itself)
mkdir -p auth
docker run --rm --entrypoint htpasswd httpd:2 -Bbn testuser testpass > auth/htpasswd

# Run with basic auth + TLS certs (place fullchain.pem / privkey.pem in ./certs)
docker run -d -p 5000:5000 --name secure-registry \
  -v "$PWD/auth:/auth" \
  -e "REGISTRY_AUTH=htpasswd" \
  -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
  -e "REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd" \
  -v "$PWD/certs:/certs" \
  -e "REGISTRY_HTTP_TLS_CERTIFICATE=/certs/fullchain.pem" \
  -e "REGISTRY_HTTP_TLS_KEY=/certs/privkey.pem" \
  registry:2
```

Clients then `docker login localhost:5000` before pushing/pulling.

> ⚠️ **"http: server gave HTTP response to HTTPS client"** — if you connect to a plain-HTTP registry that isn't `localhost`, Docker refuses it. For a trusted internal host, add it to `insecure-registries` in Docker's `daemon.json` (Docker Desktop → Settings → Docker Engine) and restart the daemon. Never do this for production.

### 4.6 Use a registry in CI (Jenkins / GitHub Actions)

The same three verbs, but the login uses a **token from a secret**, never a hard-coded password:

```bash
echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin
docker build -t myuser/myapp:"$GIT_SHA" .
docker push myuser/myapp:"$GIT_SHA"
```

In this repo's Jenkins setup (`project/Jenkins/`), store the token as a Jenkins **credential** and reference it in the pipeline rather than putting it in the `Jenkinsfile`.

### 4.7 Multi-architecture images (Apple Silicon ↔ x86)

If your image must run on both ARM and x86 hosts, build and push a multi-arch manifest with Buildx:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myuser/myapp:1.0 \
  --push .
```

---

## ✅ Recap — the mental model

1. A **registry** is a server that hosts **repositories** of **images**, each addressed by a **tag**.
2. The name you give an image *is* its address: `localhost:5000/...` → local registry; `myuser/...` → Docker Hub.
3. The universal workflow is always the same three verbs: **`tag` → `push` → `pull`**.
4. Public vs. private is about *authorization* (`docker login`), not about which commands you run.
5. For anything beyond a laptop demo: use **access tokens**, add **TLS + auth**, and keep credentials in **CI secrets**.

---

## 📚 References

- Docker registry (distribution) docs — <https://docs.docker.com/registry/>
- Deploy a local registry — <https://docs.docker.com/registry/deploying/>
- Docker Hub — <https://docs.docker.com/docker-hub/>
- Registry HTTP API v2 — <https://docs.docker.com/registry/spec/api/>
- `docker buildx` (multi-arch) — <https://docs.docker.com/build/building/multi-platform/>
