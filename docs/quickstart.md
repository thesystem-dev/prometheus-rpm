# Repository Quickstart

These steps configure a host to consume the Prometheus RPM repository published at <https://rpms.thesystem.dev/>.

## 1. Import the signing key

Import the GPG public key to verify package signatures and ensure packages haven't been tampered with:

```bash
sudo rpm --import https://rpms.thesystem.dev/RPM-GPG-KEY-thesystem-dev
```

## 2. Add the repository configuration

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

DNF repository priorities use lower numbers as higher priority. The default is `99`; `priority=50` makes this repository win over default-priority repositories such as EPEL when the same package exists in both places. Remove or adjust this value if you want the distribution or EPEL package to be preferred for overlapping package names.

## 3. Refresh metadata and install packages

```bash
sudo dnf clean all
sudo dnf makecache --repo prometheus-rpm
sudo dnf install prometheus
```

Replace `prometheus` with any package listed in [`docs/exporters.md`](exporters.md).

## 4. Service overrides (optional)

All services ship with systemd units. Customise flags or environment variables using drop-in overrides under `/etc/systemd/system/<service>.d/*.conf`. See [`docs/service-overrides.md`](service-overrides.md) for examples.
