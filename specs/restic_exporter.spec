%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           restic_exporter
Version:        2.0.1
Release:        1%{?dist}
Summary:        Prometheus exporter for Restic backup metrics

License:        MIT
URL:            https://github.com/ngosang/restic-exporter

Source0: https://github.com/ngosang/restic-exporter/archive/refs/tags/%{version}.tar.gz#/restic-exporter-%{version}.tar.gz
Source1: restic_exporter.service

BuildRequires:  systemd-rpm-macros
BuildRequires:  python3

BuildArch:      noarch

%{?systemd_requires}
%{?sysusers_requires_compat}

Requires:       (python3.12 or python3.11 or python3.10)
Requires:       python3dist(prometheus-client) >= 0.13.1
Requires:       restic

%description
Exports Restic backup metrics for Prometheus using the Restic CLI.

%prep
%setup -q -n restic-exporter-%{version}

%build
/bin/true

%install
SRC="%{_builddir}/restic-exporter-%{version}"
# Install Python script under libexec and provide a wrapper in /usr/bin
install -d %{buildroot}%{_libexecdir}/restic_exporter
install -D -m 0755 "$SRC/exporter/exporter.py" %{buildroot}%{_libexecdir}/restic_exporter/exporter.py
# Ensure shebang is explicit for RPM brp checks
sed -i '1s|^#!/usr/bin/env python$|#!/usr/bin/env python3|' %{buildroot}%{_libexecdir}/restic_exporter/exporter.py
install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/restic_exporter << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Pick the newest available Python >= 3.10 that has prometheus_client
for py in python3.12 python3.11 python3.10; do
  if command -v "$py" >/dev/null 2>&1; then
    if "$py" -c 'import prometheus_client' >/dev/null 2>&1; then
      exec "$py" /usr/libexec/restic_exporter/exporter.py "$@"
    fi
  fi
done

echo "Error: Python 3.10+ with prometheus_client is required. Install python3.12/3.11/3.10 and matching prometheus-client." >&2
exit 1
EOF
chmod 0755 %{buildroot}%{_bindir}/restic_exporter

# Licences
install -D -m 0644 "$SRC/LICENSE" %{buildroot}%{_licensedir}/%{name}/LICENSE
NOTICE_DST="%{buildroot}%{_licensedir}/%{name}/NOTICE"
if [ -f "$SRC/NOTICE" ]; then
  install -D -m 0644 "$SRC/NOTICE" "$NOTICE_DST"
else
  install -D -m 0644 /dev/null "$NOTICE_DST"
  cat > "$NOTICE_DST" <<'EOF'
NOTICE file not provided in upstream release %{version}; placeholder added to document the absence for compliance.
EOF
fi

# systemd unit
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/restic_exporter.service

# configuration directory for environment file
install -d -m 0750 %{buildroot}%{_sysconfdir}/restic_exporter.d

# sysusers (EL8+)
install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/restic_exporter.conf << 'EOF'
u restic_exporter - "Prometheus Restic Exporter"
EOF

%post
%systemd_post restic_exporter.service

%preun
%systemd_preun restic_exporter.service

%postun
%systemd_postun_with_restart restic_exporter.service

%files
%{_bindir}/restic_exporter
%{_libexecdir}/restic_exporter/exporter.py
%dir %attr(0750,root,root) %{_sysconfdir}/restic_exporter.d
%{_unitdir}/restic_exporter.service
%{_sysusersdir}/restic_exporter.conf
%license %{_licensedir}/%{name}/NOTICE
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Tue Feb 17 2026 James Wilson <git@thesystem.dev> - 2.0.1-1
- Rebase to upstream version 2.0.1

* Tue Jan 13 2026 James Wilson <packages@thesystem.dev> - 2.0.0-1
- Initial RPM package from source tarball; installs Python script with wrapper
