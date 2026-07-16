# Service Overrides

All Prometheus components in this repository ship with systemd unit files installed under `/usr/lib/systemd/system/`. Customisations should be applied via drop-in overrides rather than editing the vendor units directly. This ensures changes persist across package upgrades.

For package-specific requirements, credentials, permissions, and operational caveats, see [Service Guides](service-guides.md).

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

### node_exporter: listen address

```ini
# /etc/systemd/system/node_exporter.service.d/listen.conf
[Service]
ExecStart=
ExecStart=/usr/bin/node_exporter \
  --web.listen-address=0.0.0.0:9100 \
  --web.config.file=/etc/node_exporter/web.yml
```

## 5. Applying changes

After editing drop-ins:

```bash
sudo systemctl daemon-reload
sudo systemctl restart <unit>.service  # e.g. prometheus.service
```

Repeat for each service you customise. Document your overrides alongside infrastructure configuration so they can be recreated on new hosts.

Further reading:
- Red Hat Enterprise Linux documentation: Working with systemd unit files ([EL 8](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/using_systemd_unit_files_to_customize_and_optimize_your_system/assembly_working-with-systemd-unit-files_working-with-systemd), [EL 9](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_systemd_unit_files_to_customize_and_optimize_your_system/assembly_working-with-systemd-unit-files_working-with-systemd), [EL 10](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/using_systemd_unit_files_to_customize_and_optimize_your_system/working-with-systemd-unit-files))
- Man pages: systemd.unit(5), systemd.service(5), systemd.exec(5)
