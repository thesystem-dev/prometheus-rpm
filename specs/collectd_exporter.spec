%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           collectd_exporter
Version:        0.7.1
Release:        1%{?dist}
Summary:        Prometheus exporter for collectd metrics

License:        Apache-2.0
URL:            https://github.com/prometheus/collectd_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 1a96a19392bb8f4f4175563ea57a933acd51323bcd10b4a623a2584e126be65d
%else
%global exporter_arch amd64
%global exporter_sha 734bc83d67b3a8f2eba0b6a9b089078387509f1c5e74136b6a6d2ef5567401b6
%endif

Source0: https://github.com/prometheus/collectd_exporter/releases/download/v%{version}/collectd_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: collectd_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
collectd_exporter accepts collectd metrics via the binary network protocol or
HTTP POST and exposes them for Prometheus scraping.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd collectd_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 collectd_exporter %{buildroot}%{_bindir}/collectd_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/collectd_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/collectd_exporter.conf << 'EOF'
u collectd_exporter - "Prometheus Collectd Exporter"
EOF

%post
%systemd_post collectd_exporter.service

%preun
%systemd_preun collectd_exporter.service

%postun
%systemd_postun_with_restart collectd_exporter.service

%files
%{_bindir}/collectd_exporter
%{_unitdir}/collectd_exporter.service
%{_sysusersdir}/collectd_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.7.1-1
- Initial RPM package
