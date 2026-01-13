%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           prometheus
Version:        3.9.1
Release:        1%{?dist}
Summary:        Prometheus monitoring system and time series database

License:        Apache-2.0
URL:            https://prometheus.io/

%ifarch aarch64
%global prom_arch arm64
%global prom_sha 8d95804e692bba65a48d32ecdfb3d4acd8e1560d440c8cc08f48167cb838ec4b
%else
%global prom_arch amd64
%global prom_sha a09972ced892cd298e353eb9559f1a90f499da3fb4ff0845be352fc138780ee7
%endif

Source0: https://github.com/prometheus/prometheus/releases/download/v%{version}/prometheus-%{version}.linux-%{prom_arch}.tar.gz#/%{prom_sha}
Source1: prometheus.service
Source2: prometheus.tmpfiles.conf

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus is a systems and service monitoring system. It collects metrics
from configured targets at given intervals, evaluates rule expressions,
displays the results, and can trigger alerts if some condition is observed
to be true.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd prometheus-%{version}.linux-%{prom_arch}

install -D -m 0755 prometheus %{buildroot}%{_bindir}/prometheus
install -D -m 0755 promtool   %{buildroot}%{_bindir}/promtool

# Configuration (ship upstream example config)
install -D -m 0644 prometheus.yml %{buildroot}%{_sysconfdir}/prometheus/prometheus.yml

# Runtime data directory
install -d -m 0750 %{buildroot}/var/lib/prometheus

# systemd unit
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/prometheus.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/prometheus.conf

# sysusers (EL8+)
install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/prometheus.conf << 'EOF'
u prometheus - "Prometheus monitoring system" /var/lib/prometheus
EOF

# License
install -D -m 0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE
NOTICE_DST="%{buildroot}%{_licensedir}/%{name}/NOTICE"
if [ -f NOTICE ]; then
  install -D -m 0644 NOTICE "$NOTICE_DST"
else
  install -D -m 0644 /dev/null "$NOTICE_DST"
  cat > "$NOTICE_DST" <<'EOF'
NOTICE file not provided in upstream release %{version}; placeholder added to document the absence for compliance.
EOF
fi


%post
%systemd_post prometheus.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/prometheus.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun prometheus.service

%postun
%systemd_postun_with_restart prometheus.service

%files
%{_bindir}/prometheus
%{_bindir}/promtool
%config(noreplace) %{_sysconfdir}/prometheus/prometheus.yml
%{_unitdir}/prometheus.service
%{_tmpfilesdir}/prometheus.conf
%{_sysusersdir}/prometheus.conf
%attr(0750,prometheus,prometheus) %dir /var/lib/prometheus
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Tue Jan 13 2026 James Wilson <git@thesystem.dev> - 3.9.1-1
- Rebase to upstream version 3.9.1

* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 3.8.1-1
- Initial RPM package
