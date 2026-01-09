%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           statsd_exporter
Version:        0.28.0
Release:        1%{?dist}
Summary:        Export StatsD metrics in Prometheus format

License:        Apache-2.0
URL:            https://github.com/prometheus/statsd_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 7d361ebbd77b8cd51d03ad2e1c6fab727b9ae1b8322a5a855c1072dfd4491088
%else
%global exporter_arch amd64
%global exporter_sha 6951081e3115669e4353975f897dda1cefddef5a5d16addc908485d9be16b72b
%endif

Source0: https://github.com/prometheus/statsd_exporter/releases/download/v%{version}/statsd_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: statsd_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The Prometheus StatsD exporter bridges existing StatsD metrics into
Prometheus by listening on UDP/TCP and translating updates into Prometheus
metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd statsd_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 statsd_exporter %{buildroot}%{_bindir}/statsd_exporter
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


cd ..
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/statsd_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/statsd_exporter.conf << 'EOF'
u statsd_exporter - "Prometheus StatsD Exporter"
EOF

%post
%systemd_post statsd_exporter.service

%preun
%systemd_preun statsd_exporter.service

%postun
%systemd_postun_with_restart statsd_exporter.service

%files
%{_bindir}/statsd_exporter
%{_unitdir}/statsd_exporter.service
%{_sysusersdir}/statsd_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.28.0-1
- Initial RPM package
