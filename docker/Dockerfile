# syntax=docker/dockerfile:1

FROM almalinux:10

LABEL org.opencontainers.image.title="Prometheus RPM Builder" \
      org.opencontainers.image.description="Mock-based build environment for Prometheus/exporter RPMs" \
      org.opencontainers.image.authors="James Wilson <containers@thesystem.dev>" \
      org.opencontainers.image.vendor="thesystem.dev" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://github.com/thesystem-dev/prometheus-rpm" \
      org.opencontainers.image.source="https://github.com/thesystem-dev/prometheus-rpm/docker/Dockerfile"

RUN dnf install -y --setopt=install_weak_deps=0 --nodocs \
        dnf-plugins-core \
        epel-release && \
    dnf config-manager --set-enabled crb && \
    dnf install -y --setopt=install_weak_deps=0 --nodocs \
        mock \
        mock-core-configs \
        mock-filesystem \
        rpm-build \
        rpmdevtools \
        createrepo_c \
        systemd-rpm-macros \
        rpm-sign \
        expect \
        git \
        gnupg2 \
        curl-minimal \
        sudo \
        tar \
        gzip \
        pigz \
        xz \
        findutils \
        which && \
    dnf clean all && \
    rm -rf /var/cache/dnf/* /var/lib/dnf/history.* /var/log/*.log

RUN useradd \
      --uid 1000 \
      --create-home \
      --home-dir /home/builder \
      --shell /bin/bash \
      builder && \
    usermod -aG mock builder

COPY --chown=builder:builder --chmod=0755 docker/entrypoint.sh /entrypoint.sh
COPY --chown=builder:builder --chmod=0755 scripts/build.sh /home/builder/build.sh


# Set working directory and switch to non-root user for builds
WORKDIR /home/builder
USER builder

ENTRYPOINT ["/entrypoint.sh"]
CMD ["--help"]
