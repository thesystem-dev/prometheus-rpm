%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           influxdb_exporter
Version:        0.12.0
Release:        1%{?dist}
Summary:        Prometheus exporter that accepts InfluxDB writes

License:        Apache-2.0
URL:            https://github.com/prometheus/influxdb_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha c85982b1bc8443249de5ca44a900cd23a6ffa392cc4acd70b4b6ac58647de5b6
%else
%global exporter_arch amd64
%global exporter_sha 1b00556c5aebcf70654ef96a0e0fe301dd7867a1864004986188d966a27f4fa1
%endif

Source0: https://github.com/prometheus/influxdb_exporter/releases/download/v%{version}/influxdb_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: influxdb_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
InfluxDB exporter accepts InfluxDB HTTP writes and re-exports the metrics
in Prometheus exposition format.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd influxdb_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 influxdb_exporter %{buildroot}%{_bindir}/influxdb_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/influxdb_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/influxdb_exporter.conf << 'EOF'
u influxdb_exporter - "Prometheus InfluxDB Exporter"
EOF

%post
%systemd_post influxdb_exporter.service

%preun
%systemd_preun influxdb_exporter.service

%postun
%systemd_postun_with_restart influxdb_exporter.service

%files
%{_bindir}/influxdb_exporter
%{_unitdir}/influxdb_exporter.service
%{_sysusersdir}/influxdb_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.12.0-1
- Initial RPM package
