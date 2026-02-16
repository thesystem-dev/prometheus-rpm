%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           memcached_exporter
Version:        0.15.5
Release:        1%{?dist}
Summary:        Prometheus exporter for Memcached metrics

License:        Apache-2.0
URL:            https://github.com/prometheus/memcached_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 1ec401184ed207c40e8ab8323f46d116f6ff7654ea4040fe0d786af237c5df8d
%else
%global exporter_arch amd64
%global exporter_sha d628bd8119b8e69696f61bdf6736490962d5abd52d35207b58a547447aa4e74f
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
* Tue Jan 27 2026 James Wilson <packages@thesystem.dev> - 0.15.5-1
- Rebase to upstream version 0.15.5

* Tue Jan 13 2026 James Wilson <packages@thesystem.dev> - 0.15.4-1
- Rebase to upstream version 0.15.4

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.15.0-1
- Initial RPM package
