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

## 3. Overriding environment variables

Many exporters support environment variables (e.g., credentials). Use `Environment=` or `EnvironmentFile=` in a drop-in. `node_exporter` does not ship an `/etc/node_exporter` tree, so create it before referencing files there:

```bash
sudo install -d -m 0750 /etc/node_exporter
sudo install -d -m 0750 /etc/node_exporter.d
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

### node_exporter: listen address

```ini
# /etc/systemd/system/node_exporter.service.d/listen.conf
[Service]
ExecStart=
ExecStart=/usr/bin/node_exporter \
  --web.listen-address=0.0.0.0:9100 \
  --web.config.file=/etc/node_exporter/web.yml
```

### restic_exporter: repository credentials

`restic_exporter` reads its configuration from environment variables (the unit already references `/etc/restic_exporter.d/env`). Create the directory and env file with restricted permissions:

```bash
sudo install -d -m 0750 /etc/restic_exporter.d
sudo install -m 0640 /etc/restic_exporter.d/env
```

Populate `/etc/restic_exporter.d/env`:

```
RESTIC_REPOSITORY=s3:https://objects.example.com/backups
RESTIC_PASSWORD_FILE=/etc/restic_exporter.d/password
RESTIC_BIN=/usr/bin/restic
LISTEN_ADDRESS=0.0.0.0
LISTEN_PORT=8001
REFRESH_INTERVAL=600
```

If you keep secrets outside the env file, point the variables to those paths (for example, `RESTIC_PASSWORD_FILE` above). No additional drop-in is required—the vendor unit already includes `EnvironmentFile=-/etc/restic_exporter.d/env`. Reload and restart after editing as usual.

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
