%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           process_exporter
Version:        0.8.7
Release:        1%{?dist}
Summary:        Prometheus exporter for process metrics

License:        MIT
URL:            https://github.com/ncabatoff/process-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 4a2502f290323e57eeeb070fc10e64047ad0cd838ae5a1b347868f75667b5ab0
%else
%global exporter_arch amd64
%global exporter_sha 6d274cca5e94c6a25e55ec05762a472561859ce0a05b984aaedb67dd857ceee2
%endif

Source0: https://github.com/ncabatoff/process-exporter/releases/download/v%{version}/process-exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: process_exporter.service
Source2: process_exporter.yml

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Process exporter mines /proc and exports per-process metrics (CPU, memory,
count) based on configurable matchers.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd process-exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 process-exporter %{buildroot}%{_bindir}/process_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/process_exporter.service

install -d %{buildroot}%{_sysconfdir}/prometheus/process_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/prometheus/process_exporter/process_exporter.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/process_exporter.conf << 'EOF'
u process_exporter - "Prometheus Process Exporter"
EOF

%post
%systemd_post process_exporter.service

%preun
%systemd_preun process_exporter.service

%postun
%systemd_postun_with_restart process_exporter.service

%files
%{_bindir}/process_exporter
%{_unitdir}/process_exporter.service
%{_sysusersdir}/process_exporter.conf
%config(noreplace) %{_sysconfdir}/prometheus/process_exporter/process_exporter.yml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.8.7-1
- Initial RPM package
