%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           snmp_exporter
Version:        0.30.1
Release:        1%{?dist}
Summary:        Prometheus exporter for SNMP targets

License:        Apache-2.0
URL:            https://github.com/prometheus/snmp_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha e590870ad2fcd39ea9c7d722d6e85aa6f1cc9e8671ff3f17feba12a6b5a3b47a
%else
%global exporter_arch amd64
%global exporter_sha fd7ded886180063a8f77e1ca18cc648e44b318b9c92bcb3867b817d93a5232d6
%endif

Source0: https://github.com/prometheus/snmp_exporter/releases/download/v%{version}/snmp_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: snmp_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The snmp_exporter translates SNMP responses into Prometheus metrics so
network devices can be monitored alongside native exporters.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd snmp_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 snmp_exporter %{buildroot}%{_bindir}/snmp_exporter
install -D -m 0644 snmp.yml %{buildroot}%{_sysconfdir}/prometheus/snmp_exporter/snmp.yml
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/snmp_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/snmp_exporter.conf << 'EOF'
u snmp_exporter - "Prometheus SNMP Exporter"
EOF

%post
%systemd_post snmp_exporter.service

%preun
%systemd_preun snmp_exporter.service

%postun
%systemd_postun_with_restart snmp_exporter.service

%files
%{_bindir}/snmp_exporter
%{_unitdir}/snmp_exporter.service
%{_sysusersdir}/snmp_exporter.conf
%config(noreplace) %{_sysconfdir}/prometheus/snmp_exporter/snmp.yml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Thu Jan 15 2026 James Wilson <packages@thesystem.dev> - 0.30.1-1
- Rebase to upstream version 0.30.1

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.29.0-1
- Initial RPM package
