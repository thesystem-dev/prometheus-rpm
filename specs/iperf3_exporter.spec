%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           iperf3_exporter
Version:        1.3.1
Release:        1%{?dist}
Summary:        Prometheus exporter wrapping iPerf3 tests

License:        Apache-2.0
URL:            https://github.com/edgard/iperf3_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 1bc60ba3de68ed86e0d072ec769e02a7e171f7fea3cc77597fbfcf8c068395c1
%else
%global exporter_arch amd64
%global exporter_sha 6da99e95f93fa02809a24be748f2acced54462f1ec84f3659728b3094d77acb0
%endif

Source0: https://github.com/edgard/iperf3_exporter/releases/download/%{version}/iperf3_exporter-%{version}-linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: iperf3_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
iPerf3 exporter runs periodic iPerf3 tests and exposes the throughput/
jitter metrics to Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd iperf3_exporter-%{version}-linux-%{exporter_arch}
install -D -m 0755 iperf3_exporter %{buildroot}%{_bindir}/iperf3_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/iperf3_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/iperf3_exporter.conf << 'EOF'
u iperf3_exporter - "Prometheus iPerf3 Exporter"
EOF

%post
%systemd_post iperf3_exporter.service

%preun
%systemd_preun iperf3_exporter.service

%postun
%systemd_postun_with_restart iperf3_exporter.service

%files
%{_bindir}/iperf3_exporter
%{_unitdir}/iperf3_exporter.service
%{_sysusersdir}/iperf3_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.3.1-1
- Initial RPM package
