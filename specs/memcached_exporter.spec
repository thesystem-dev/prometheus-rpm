%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           memcached_exporter
Version:        0.16.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Memcached metrics

License:        Apache-2.0
URL:            https://github.com/prometheus/memcached_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha c3ff12346f47e87b2f8ba35c0ddde5f557851a5a1886b3a2776f9a23209ce0db
%else
%global exporter_arch amd64
%global exporter_sha ec669cdce5258e48e0b3747719bb60c0f91d74a21fd4033ec259e80db6c0b0ed
%endif

Source0: https://github.com/prometheus/memcached_exporter/releases/download/v%{version}/memcached_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: memcached_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus exporter that collects metrics from a Memcached instance.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd memcached_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 memcached_exporter %{buildroot}%{_bindir}/memcached_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/memcached_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/memcached_exporter.conf << 'EOF'
u memcached_exporter - "Prometheus Memcached Exporter"
EOF

%post
%systemd_post memcached_exporter.service

%preun
%systemd_preun memcached_exporter.service

%postun
%systemd_postun_with_restart memcached_exporter.service

%files
%{_bindir}/memcached_exporter
%{_unitdir}/memcached_exporter.service
%{_sysusersdir}/memcached_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Thu Apr 09 2026 James Wilson <packages@thesystem.dev> - 0.16.0-1
- Rebase to upstream version 0.16.0

* Tue Jan 27 2026 James Wilson <packages@thesystem.dev> - 0.15.5-1
- Rebase to upstream version 0.15.5

* Tue Jan 13 2026 James Wilson <packages@thesystem.dev> - 0.15.4-1
- Rebase to upstream version 0.15.4

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.15.0-1
- Initial RPM package
