# Service Overrides

All Prometheus components in this repository ship with systemd unit files installed under `/usr/lib/systemd/system/`. Customisations should be applied via drop-in overrides rather than editing the vendor units directly. This ensures changes persist across package upgrades.

## 1. Override directory layout

systemd looks for drop-in files under `/etc/systemd/system/<unit>.d/`. For example, to override `prometheus.service` create:

```
/etc/systemd/system/prometheus.service.d/
└── override.conf
```

After creating or modifying drop-ins, reload systemd:

```bash
sudo systemctl daemon-reload
```

## 2. Overriding ExecStart flags

Most units expose command-line flags. To append or replace flags, use the `[Service]` section with `ExecStart=`. For example:

```ini
# /etc/systemd/system/prometheus.service.d/execstart.conf
[Service]
ExecStart=
ExecStart=/usr/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --web.config.file=/etc/prometheus/web.yml \
  --web.enable-lifecycle
```

The first `ExecStart=` line clears the vendor definition; the second defines the full command. Copy the original arguments from `/usr/lib/systemd/system/prometheus.service` and append your changes.

Files referenced by service flags are opened by the service process, not by systemd. If a unit runs as a non-root user, make private configuration files readable by that user or its group, for example `root:<service-group>` with `0640` files and `0750` containing directories.

## 3. Overriding environment variables

Many exporters support environment variables (e.g., credentials). Use `Environment=` or `EnvironmentFile=` in a drop-in. `node_exporter` does not ship an `/etc/node_exporter` tree, so create it before referencing files there:

```bash
sudo install -d -m 0750 -o root -g node_exporter /etc/node_exporter
sudo install -d -m 0750 -o root -g node_exporter /etc/node_exporter.d
sudo install -m 0640 -o root -g node_exporter web.yml /etc/node_exporter/web.yml
```

Create the drop-in:

```ini
# /etc/systemd/system/node_exporter.service.d/env.conf
[Service]
Environment="NODE_EXPORTER_WEB_CONFIG=/etc/node_exporter/web.yml"
```

For larger sets, supply a file:

```ini
[Service]
EnvironmentFile=/etc/node_exporter.d/env
```

and create `/etc/node_exporter.d/env` with `VAR=value` lines.

## 4. Examples

### Prometheus: custom TSDB path

```ini
# /etc/systemd/system/prometheus.service.d/storage.conf
[Service]
ExecStart=
ExecStart=/usr/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/srv/prometheus \
  --web.config.file=/etc/prometheus/web.yml
```

If `web.yml` references TLS keys or other private files, ensure they are readable by the `prometheus` service user or group, for example `root:prometheus` with `0640` files and `0750` containing directories.

### Prometheus: user-supplied console templates

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

### node_exporter: listen address

```ini
# /etc/systemd/system/node_exporter.service.d/listen.conf
[Service]
ExecStart=
ExecStart=/usr/bin/node_exporter \
  --web.listen-address=0.0.0.0:9100 \
  --web.config.file=/etc/node_exporter/web.yml
```

### ipmi_exporter: opt-in sudo scraping

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

### thanos-sidecar: TSDB ownership

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

### restic_exporter: repository credentials

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

### restic_repo_exporter: multi-repo scanning

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

## 5. Applying changes

After editing drop-ins:

```bash
sudo systemctl daemon-reload
sudo systemctl restart <unit>.service  # e.g. prometheus.service
```

Repeat for each service you customise. Document your overrides alongside infrastructure configuration so they can be recreated on new hosts.

Further reading:
- [Red Hat Enterprise Linux 9 documentation: Managing systemd unit files](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_basic_system_settings/managing-systemd-unit-files_configuring-basic_system_settings) (applies to EL 8/9/10)
- Man pages: systemd.unit(5), systemd.service(5), systemd.exec(5)
