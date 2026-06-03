# Repository Quickstart

These steps configure a host to consume the Prometheus RPM repository published at <https://rpms.thesystem.dev/>.

## 1. Enable standard dependencies

This repository is not self-contained. It expects the normal Enterprise Linux base repositories plus EPEL to be enabled. Some EPEL packages also require the distribution's builder repository:

| Platform | Repository to enable |
| --- | --- |
| EL8-compatible distributions | PowerTools, often named `powertools` |
| EL9/EL10-compatible distributions | CRB, usually named `crb` |
| RHEL | CodeReady Linux Builder |

Enable the builder repository, then install EPEL before installing packages from this repository.

For EL8-compatible systems:

```bash
sudo dnf config-manager --set-enabled powertools
sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
```

For EL9-compatible systems:

```bash
sudo dnf config-manager --set-enabled crb
sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
```

For EL10-compatible systems:

```bash
sudo dnf config-manager --set-enabled crb
sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-10.noarch.rpm
```

On RHEL, enable the matching CodeReady Linux Builder repository instead of `powertools` or `crb`.

## 2. Install the repository package

Install the repository package for your Enterprise Linux major version:

```bash
sudo dnf install https://rpms.thesystem.dev/thesystem-release-latest-10.noarch.rpm
```

Use `latest-8`, `latest-9`, or `latest-10` to match the host. DNF may ask you to trust the package signing key on first install; this is expected for a signed third-party repository package.

The repository package installs the GPG public key under `/etc/pki/rpm-gpg/` and creates `/etc/yum.repos.d/prometheus-rpm.repo`.

## 3. Manual repository configuration

Use this fallback for air-gapped hosts or automation that manages repository files directly.

Import the GPG public key:

```bash
sudo rpm --import https://rpms.thesystem.dev/RPM-GPG-KEY-thesystem-dev
```

Create the repository file:

```bash
sudo tee /etc/yum.repos.d/prometheus-rpm.repo > /dev/null <<'EOF'
# Repository: https://rpms.thesystem.dev/
# Project:    https://github.com/thesystem-dev/prometheus-rpm

[prometheus-rpm]
name=thesystem Prometheus RPM Repository for Enterprise Linux $releasever - $basearch
baseurl=https://rpms.thesystem.dev/prometheus-rpm/el$releasever/$basearch/
enabled=1
gpgcheck=1
gpgkey=https://rpms.thesystem.dev/RPM-GPG-KEY-thesystem-dev
priority=50
EOF
```

In DNF, lower priority numbers take precedence. The default priority is `99`; `priority=50` makes this repository preferred over default-priority repositories such as EPEL when package names overlap. Remove or raise this value if you want the distribution or EPEL package to be preferred.

## 4. Refresh metadata and install packages

```bash
sudo dnf clean all
sudo dnf makecache --repo prometheus-rpm
sudo dnf install prometheus
```

Replace `prometheus` with any package listed in [`docs/exporters.md`](exporters.md).

## 5. Service overrides (optional)

All services ship with systemd units. Customise flags or environment variables using drop-in overrides under `/etc/systemd/system/<service>.d/*.conf`. See [`docs/service-overrides.md`](service-overrides.md) for examples.
