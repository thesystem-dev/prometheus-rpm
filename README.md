# Prometheus RPM Build

This repository provides Prometheus and exporter RPM packages for Enterprise Linux systems. The long-running [lest/prometheus-rpm](https://github.com/lest/prometheus-rpm/) project appears unmaintained, so this project serves as an actively maintained successor that tracks upstream releases, verifies the artifacts we publish, and provides signed package repositories.

## Goals

This project improves on previous Prometheus RPM packaging efforts by providing:

- **Reproducible builds** using `mock` for consistent, isolated build environments
- **Multi-EL support** for Enterprise Linux 8, 9, and 10
- **Multi-architecture support** for x86_64 and aarch64
- **Signed RPMs** with GPG signatures to ensure package integrity

## Current Status

**This is a work in progress.** The repository currently contains:

- `specs/` - RPM spec files for Prometheus and various exporters
- `sources/` - systemd unit files, configuration files, and other package assets referenced by the specs, organised per package (`sources/<package_name>/...`)
- `runtime/` - placeholder directories to be populated by future runtime scripts

Configuration files are vendored from upstream projects whenever they publish them. When no upstream example exists, hardened minimal defaults are provided alongside notes documenting any intentional divergence.

Build automation, Docker tooling, and more detailed documentation will be added in subsequent commits as the project matures.

## Non-Goals

This project is focused on building and distributing high-quality RPM packages for Prometheus and related exporters. It does not aim to:

- Carry downstream patches or modify upstream Prometheus or exporter behaviour
- Provide heavily opinionated defaults or distribution-specific tuning beyond upstream guidance
- Replace upstream release artefacts outside RPM-based systems
- Support end-of-life Enterprise Linux releases
- Manage Prometheus topology, scrape configuration, or deployment design
- Act as a turnkey or fully integrated monitoring stack

## Roadmap

- [ ] Python helpers for tracking upstream releases and maintaining an exporter inventory
- [ ] Build and signing scripts with mock/Docker support
- [ ] Documentation covering build, signing, publishing, and divergence notes
- [ ] Continuous integration and container image publishing

## Contributing

Bug reports, feature requests, and pull requests are welcome. The project is under active development, and community contributions help shape its direction, including support for additional exporters.
