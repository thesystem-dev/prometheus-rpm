# Prometheus RPM Build

This repository provides Prometheus and exporter RPM packages for Enterprise Linux systems. It tracks upstream releases, verifies release artefacts and publishes repositories of signed RPMs.

The project started to meet our own packaging requirements during a period of limited activity in the long-running [lest/prometheus-rpm](https://github.com/lest/prometheus-rpm/) project.

---

💡 **Just want to install the packages?** See [`docs/quickstart.md`](docs/quickstart.md) for repository setup and installation instructions.

## Goals

This project contributes to the community's Prometheus RPM packaging efforts by providing:

- **Consistent, isolated RPM builds** using `mock`; see [build guarantees](docs/build-and-stage.md#build-guarantees)
- **Verified release artefacts** checked against pinned SHA-256 checksums before packaging
- **Multi-EL support** for Enterprise Linux 8, 9, and 10
- **Multi-architecture support** for x86_64 and aarch64
- **Systemd integration** with packaged service units and local customisation through drop-in overrides
- **Signed RPMs** with GPG signatures to ensure package integrity

## Current Status

**This is a work in progress.** The repository currently contains:

- `specs/` - RPM spec files for Prometheus and various exporters
- `sources/` - systemd unit files, configuration files, and other package assets referenced by the specs, organised per package (`sources/<package_name>/...`)
- `scripts/` - helper utilities for version discovery, runtime staging, mock builds, and RPM signing
- `scripts/sign-rpms.sh` - GPG-based RPM/SRPM signing with interactive and automated modes
- `templates/` - baseline `rpmmacros` used by `scripts/stage-runtime.sh`
- `docker/` - builder image (`prometheus-rpm-builder:1.0`), entrypoint, and compose file for running mock inside a container
- `runtime/` - transient workspace prepared by `scripts/stage-runtime.sh` (artefacts, SOURCES cache, repo metadata, and GPG material)

Configuration files are vendored from upstream projects whenever they publish them. When no upstream example exists, hardened minimal defaults are provided alongside notes documenting any intentional divergence.

Build, signing and repository metadata helpers are implemented. Publishing remains a manual workflow; CI and container image publishing are roadmap items.

## Documentation

- [`docs/quickstart.md`](docs/quickstart.md) - consumer setup guide (install the repository package or configure the repo manually).
- [`docs/exporters.md`](docs/exporters.md) - auto-generated exporter inventory with upstream links, licences, and supported architectures.
- [`docs/service-overrides.md`](docs/service-overrides.md) - describes how to adjust systemd units via drop-in overrides.
- [`docs/service-guides.md`](docs/service-guides.md) - package-specific service requirements, configuration, permissions, and operational caveats.
- [`docs/workflows.md`](docs/workflows.md) - short maintainer commands for version refresh, build, signing, verification, and repository metadata.
- [`docs/version-tracking.md`](docs/version-tracking.md) - explains how `upstreams.yaml` is maintained and how the helper scripts are used to track upstream releases.
- [`docs/runtime.md`](docs/runtime.md) - describes `scripts/stage-runtime.sh`, the runtime directory layout, and how to prepare GPG material safely.
- [`docs/build-and-stage.md`](docs/build-and-stage.md) - covers running `docker compose`, invoking `scripts/build.sh`, and staging artefacts for signing.
- [`docs/signing.md`](docs/signing.md) - covers exporting GPG keys, running `scripts/sign-rpms.sh`, and verifying signed artefacts.
- [`docs/publishing.md`](docs/publishing.md) - describes creating repository metadata, syncing to remote hosts, and making packages available to consumers.

## Non-Goals

This project is focused on building and distributing high-quality RPM packages for Prometheus and related exporters. It does not aim to:

- Carry downstream patches or modify upstream Prometheus or exporter behaviour
- Provide heavily opinionated defaults or distribution-specific tuning beyond upstream guidance
- Replace upstream release artefacts outside RPM-based systems
- Support end-of-life Enterprise Linux releases
- Manage Prometheus topology, scrape configuration, or deployment design
- Act as a turnkey or fully integrated monitoring stack

## Roadmap

- [x] Python helpers for tracking upstream releases and maintaining an exporter inventory
- [x] Build and signing scripts with mock/Docker support
- [x] Documentation covering build and signing workflows
- [x] Documentation covering publishing workflows
- [ ] Continuous integration and container image publishing

## Contributing

Bug reports, feature requests and pull requests are welcome, including suggestions for additional exporters.
