%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           logstash_exporter
Version:        1.9.1
Release:        1%{?dist}
Summary:        Prometheus exporter for Logstash metrics

License:        MIT
URL:            https://github.com/kuskoman/logstash-exporter

%ifarch aarch64
%global exporter_arch linux-arm
%global exporter_sha 15736b94a3faf600768bec41b798091761114988ae3afe035aff20bbe2db87b7
%else
%global exporter_arch linux
%global exporter_sha c6e45d08b997650039e5061a3415d0098bba22fa296e6caf916b8980a0faa8a1
%endif

Source0: https://github.com/kuskoman/logstash-exporter/releases/download/v%{version}/logstash-exporter-%{exporter_arch}#/%{exporter_sha}
Source1: logstash_exporter.service
Source2: logstash_exporter.yml

BuildRequires: systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Logstash exporter scrapes Logstash monitoring APIs and exposes Prometheus metrics.

%prep
mkdir -p src
install -m 0755 %{SOURCE0} src/logstash-exporter

%build
/bin/true

%install
install -D -m 0755 src/logstash-exporter %{buildroot}%{_bindir}/logstash-exporter

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/logstash_exporter.service
install -D -m 0644 %{SOURCE2} %{buildroot}/etc/logstash-exporter/config.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/logstash_exporter.conf << 'EOF'
u logstash_exporter - "Logstash Exporter"
EOF

%post
%systemd_post logstash_exporter.service

%preun
%systemd_preun logstash_exporter.service

%postun
%systemd_postun_with_restart logstash_exporter.service

%files
%{_bindir}/logstash-exporter
%{_unitdir}/logstash_exporter.service
%dir /etc/logstash-exporter
%config(noreplace) /etc/logstash-exporter/config.yml
%{_sysusersdir}/logstash_exporter.conf

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.9.1-1
- Initial RPM package
