# CSE636 Week 1 — local lab environment
# A reproducible Ubuntu shell with the same DevOps tools as the cloud (EC2) path.
# Build:  docker build -t cse636-lab weeks/week-01/lab-env
# Run:    see weeks/week-01/week-01-lab.md, Step 1b.

FROM ubuntu:latest

# Non-interactive apt so the image builds without prompting for tzdata etc.
ENV DEBIAN_FRONTEND=noninteractive

# The same toolset the AWS path installs, plus the Docker CLI so this container
# can drive the host daemon via the mounted /var/run/docker.sock.
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      curl \
      ca-certificates \
      python3 \
      python3-pip \
      jq \
      docker.io \
    && rm -rf /var/lib/apt/lists/*

# Optional: trust an extra CA for networks behind a TLS-inspecting proxy (e.g.
# Zscaler). Drop the proxy's root CA at certs/corp-ca.pem (gitignored) — see the
# lab's Step 1b. Empty certs/ (only .gitkeep) => no-op, so the image still builds
# unchanged on an open network.
COPY certs/ /tmp/extra-ca/
RUN set -eu; \
    if ls /tmp/extra-ca/*.pem >/dev/null 2>&1 || ls /tmp/extra-ca/*.crt >/dev/null 2>&1; then \
      for bundle in /tmp/extra-ca/*.pem /tmp/extra-ca/*.crt; do \
        [ -e "$bundle" ] || continue; \
        # split a bundle into one cert per file (update-ca-certificates wants singles)
        awk -v d=/usr/local/share/ca-certificates \
          'BEGIN{n=0} /BEGIN CERTIFICATE/{n++} {print > (d"/extra-"n".crt")}' "$bundle"; \
      done; \
      update-ca-certificates; \
    fi; \
    rm -rf /tmp/extra-ca

# Node/npm (Claude Code's runtime) read their own TLS trust from this env var, so
# point it at the OS bundle that now includes any proxy CA added above.
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Your work lives here; mount a host folder onto it so it survives container resets.
WORKDIR /root/lab-data

# Drop the student into an interactive shell by default.
CMD ["bash"]
