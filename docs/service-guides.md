# Service Guides

This page records package-specific requirements, configuration, permissions, and operational caveats for services shipped by this repository. For the generic systemd drop-in mechanism used to change packaged units, see [Service Overrides](service-overrides.md).

## Prometheus: user-supplied console templates

Prometheus still supports console templates, but Prometheus 3.x no longer ships the example `consoles/` and `console_libraries/` assets. The upstream [console templates documentation](https://prometheus.io/docs/visualization/consoles/) covers this behaviour and notes that the historical Prometheus 2.x libraries are no longer maintained. This repository does not reintroduce those removed assets.

For normal dashboards, use Grafana. If you maintain your own console templates, create local directories for them:

```bash
sudo install -d -m 0755 /etc/prometheus/consoles
sudo install -d -m 0755 /etc/prometheus/console_libraries
```

Then add the console paths with a systemd drop-in:

```ini
# /etc/systemd/system/prometheus.service.d/consoles.conf
[Service]
ExecStart=
ExecStart=/usr/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries
```

The empty `ExecStart=` line clears the vendor command, so preserve the existing packaged arguments when adding the console flags. The same pattern applies to `prometheus-lts`.

If the console templates or libraries contain site-private content, use tighter permissions such as `root:prometheus` ownership, `0750` directories, and group-readable files.

## ipmi_exporter: opt-in sudo scraping

`ipmi_exporter` ships the upstream local IPMI config as the active default and keeps the unit hardened. The package also ships the upstream sudo example as `/etc/ipmi_exporter/ipmi_local_sudo.yml.example`, but it is not enabled by default and the RPM does not install sudoers rules.

If your hardware requires sudo for local IPMI scraping, copy and review the example first:

```bash
sudo cp /etc/ipmi_exporter/ipmi_local_sudo.yml.example /etc/ipmi_exporter/ipmi_local_sudo.yml
```

Create sudoers rules that match the collector commands in the config you actually use. The upstream sudo example calls `/usr/sbin/ipmimonitoring` and `/usr/sbin/ipmi-sel`; adjust the rules if you change those paths.

Sudo mode also requires relaxing the default service hardening. Start with a drop-in like this, then tighten it again for your hardware if possible:

```ini
# /etc/systemd/system/ipmi_exporter.service.d/local-sudo.conf
[Service]
ExecStart=
ExecStart=/usr/bin/ipmi_exporter \
  --config.file=/etc/ipmi_exporter/ipmi_local_sudo.yml \
  --web.listen-address=0.0.0.0:9290
NoNewPrivileges=no
ProtectKernelTunables=no
ProtectKernelModules=no
PrivateDevices=no
LockPersonality=no
MemoryDenyWriteExecute=no
RestrictRealtime=no
```

This privileged mode is intentionally opt-in. Test it on the target host and keep the sudoers rules limited to the exact commands used by the selected collectors.

## thanos-sidecar: TSDB ownership

In this package, `thanos-sidecar.service` runs as `prometheus:prometheus` with `SupplementaryGroups=thanos`.

The packaged unit requires write access to the local Prometheus TSDB directory in order to create and maintain Thanos shipper metadata.

When using this package set:

- Install the `prometheus` RPM before enabling `thanos-sidecar`, or
- Provide an equivalent `prometheus` user and group, and ensure the TSDB directory exists with appropriate ownership and permissions.

If the `--tsdb.path` option is overridden, the specified directory must:

- Exist prior to service start
- Be owned by, or writable by, the `prometheus` user

If the systemd service user or group is modified via a drop-in override, the administrator must ensure that:

- The TSDB directory ownership and permissions are updated accordingly
- Any referenced Thanos configuration files are readable by the configured service user or an assigned supplementary group

Failure to meet these requirements will prevent `thanos-sidecar` from starting or from correctly shipping blocks.

## restic_exporter: repository credentials

`restic_exporter` is configured through environment variables, so the vendor unit includes `EnvironmentFile=-/etc/restic_exporter.d/env`. The file is optional at install time, but the service needs a populated env file before it can read a real repository.

Create the env file and password file with restricted permissions. The directory and files must be readable by the `restic_exporter` group because the exporter runs as the `restic_exporter` user and the `restic` child process reads `RESTIC_PASSWORD_FILE` directly:

```bash
sudo install -d -m 0750 -o root -g restic_exporter /etc/restic_exporter.d
sudo install -m 0640 -o root -g restic_exporter /dev/null /etc/restic_exporter.d/env
sudo install -m 0640 -o root -g restic_exporter /dev/null /etc/restic_exporter.d/password
```

Populate `/etc/restic_exporter.d/env` with the repository location, restic password file, and cache path:

```
RESTIC_REPOSITORY=/srv/restic
RESTIC_PASSWORD_FILE=/etc/restic_exporter.d/password
RESTIC_CACHE_DIR=/var/cache/restic_exporter
```

Use `RESTIC_PASSWORD_FILE` instead of `RESTIC_PASSWORD` so the restic repository password is not stored directly in the systemd environment file. Other exporter settings use the upstream `restic-exporter` environment variables.

`RESTIC_CACHE_DIR` is a restic setting rather than a restic-exporter setting. It provides the package equivalent of upstream's Docker cache-volume recommendation. The unit uses `CacheDirectory=restic_exporter`, so `/var/cache/restic_exporter` is writable by the service even with systemd filesystem hardening enabled.

Prefer separate credentials for monitoring:

- Create a separate restic repository key for the exporter with `restic key add`. This avoids reusing the backup job password, but it is not a read-only role; a valid restic key can decrypt repository data.
- For remote backends, use a separate backend credential for the exporter where the backend supports it. Start with read/list-style access for monitoring and only broaden it if your chosen exporter options require more access.

For remote object-storage repositories, exporter refreshes can create storage transactions and retrieval traffic. If backups run daily, consider using a higher refresh interval and disabling expensive optional collectors:

```
REFRESH_INTERVAL=86400
NO_CHECK=True
NO_GLOBAL_STATS=True
NO_LEGACY_STATS=True
NO_LOCKS=True
INCLUDE_PATHS=False
```

These options are intentionally not the baseline example. They trade metric depth and freshness for lower cost.

Reload and restart after editing:

```bash
sudo systemctl daemon-reload
sudo systemctl restart restic_exporter.service
```

## restic_repo_exporter: multi-repo scanning

`restic_repo_exporter` requires an environment file at `/etc/restic_repo_exporter.d/env` (referenced by the vendor unit). Create it with restricted permissions:

```bash
sudo install -d -m 0750 -o root -g restic_repo_exporter /etc/restic_repo_exporter.d
sudo install -m 0640 -o root -g restic_repo_exporter /dev/null /etc/restic_repo_exporter.d/env
```

Populate `/etc/restic_repo_exporter.d/env` with at least the base repo path and a default password. You can supply per-repo overrides by appending the directory name:

```
RESTIC_REPO_PATH=/srv/restic
RESTIC_PASSWORD=default-password
RESTIC_PASSWORD_repo1=secret1
RESTIC_PASSWORD_repo2=secret2
MAX_SIMULTANEOUS_RESTIC_PROCESSES=4
RESTIC_REPO_EXPORTER_ARGS=--listen-address=:9200 --scrape-interval=60
```

If you place separate credential files under `/etc/restic_repo_exporter.d`, make them readable by the `restic_repo_exporter` group, for example `0640 root:restic_repo_exporter`.

The vendor unit passes `RESTIC_REPO_PATH` as the single `--repo-path` argument and expands `RESTIC_REPO_EXPORTER_ARGS` as optional additional arguments. If `/etc/restic_repo_exporter.d/env` is missing, the service will fail to start until configured. Restart the service after editing.

## prometheus-paperless-exporter: credentials and collectors

`prometheus-paperless-exporter` requires a Paperless-ngx URL before it can start and normally needs credentials to collect metrics. The vendor unit references `/etc/prometheus-paperless-exporter/service.conf` as a required service configuration file; the RPM creates the containing directory but does not install a configuration file, token, or example URL.

Create the environment and token files with restricted permissions:

```bash
sudo install -d -m 0750 -o root -g prometheus-paperless-exporter /etc/prometheus-paperless-exporter
sudo install -m 0640 -o root -g prometheus-paperless-exporter /dev/null /etc/prometheus-paperless-exporter/service.conf
sudo install -m 0640 -o root -g prometheus-paperless-exporter /dev/null /etc/prometheus-paperless-exporter/token
```

Populate the service configuration file with the Paperless-ngx base URL and a file-backed API token using systemd `EnvironmentFile=` syntax:

```text
PAPERLESS_URL=https://paperless.example.com
PAPERLESS_AUTH_TOKEN_FILE=/etc/prometheus-paperless-exporter/token
```

Place only the token value in `/etc/prometheus-paperless-exporter/token`. File-backed credentials are preferable to storing `PAPERLESS_AUTH_TOKEN` directly in the systemd environment. For Paperless installations using a private certificate authority, the exporter also supports `PAPERLESS_TRUSTED_CA_FILE`.

The exporter interprets Paperless timestamps using the local timezone by default. Set an IANA timezone when the service host and Paperless server do not use the same timezone, for example:

```text
PAPERLESS_SERVER_TIMEZONE=Europe/London
```

### Paperless permissions

Use a dedicated Paperless account and token for monitoring. Upstream documents view permissions for Admin, Correspondent, Document, DocumentType, Group, PaperlessTask, StoragePath, Tag, and User. Admin access is used for log analysis. Paperless API behavior may require broader Admin or Superuser access for whole-system status and statistics; [upstream issue #127](https://github.com/hansmi/prometheus-paperless-exporter/issues/127) tracks work to reduce those requirements.

Grant only the permissions needed by the collectors you enable, and verify the resulting metrics against the Paperless version you run. Do not assume the token is read-only merely because it belongs to a monitoring account.

### Collector selection

When `--collectors` is omitted, all standard collectors are enabled. The available collector IDs are `tag`, `correspondent`, `document_type`, `storage_path`, `task`, `log`, `group`, `user`, `document`, `status`, `statistics`, and `remote_version`. Remote version checks remain disabled unless `--enable-remote-network` is also set.

The `task` collector can create a large number of series on installations with substantial task history; [upstream issue #100](https://github.com/hansmi/prometheus-paperless-exporter/issues/100) documents this behavior. Select only the collectors you need when cardinality or API load is a concern:

```ini
# /etc/systemd/system/prometheus-paperless-exporter.service.d/collectors.conf
[Service]
ExecStart=
ExecStart=/usr/bin/prometheus-paperless-exporter \
  --collectors=status,statistics,document,tag
```

### Listener security

The exporter follows its upstream default and listens on all interfaces on port `8081`. Its metrics can contain Paperless-derived names, identifiers, and document or task metadata, so restrict access to trusted monitoring networks with host or network firewall policy.

To bind only to loopback, replace `ExecStart` with a systemd drop-in:

```ini
# /etc/systemd/system/prometheus-paperless-exporter.service.d/listen.conf
[Service]
ExecStart=
ExecStart=/usr/bin/prometheus-paperless-exporter \
  --web.listen-address=127.0.0.1:8081
```

The exporter also supports TLS and HTTP basic authentication through the Prometheus exporter toolkit using `--web.config.file`. Keep that configuration under `/etc/prometheus-paperless-exporter` with `root:prometheus-paperless-exporter` ownership and group-readable permissions.

After creating the required files or changing a drop-in, reload systemd and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart prometheus-paperless-exporter.service
```
