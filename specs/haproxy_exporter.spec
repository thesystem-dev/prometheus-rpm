%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           haproxy_exporter
Version:        0.15.0
Release:        1%{?dist}
Summary:        Prometheus exporter for HAProxy stats

License:        Apache-2.0
URL:            https://github.com/prometheus/haproxy_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 58dfc17236c8a6f74ccdc290de976a0aa79d50e47a8d1b35bde038190391ce5d
%else
%global exporter_arch amd64
%global exporter_sha ac200872b734e2f9c0211997f7f9c0ca5ad6522996c37aed39a732d5f3c0de16
%endif

Source0: https://github.com/prometheus/haproxy_exporter/releases/download/v%{version}/haproxy_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: haproxy_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
HAProxy exporter exposes HAProxy stats (frontend/backend health, sessions,
errors) to Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd haproxy_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 haproxy_exporter %{buildroot}%{_bindir}/haproxy_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/haproxy_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/haproxy_exporter.conf << 'EOF'
u haproxy_exporter - "Prometheus HAProxy Exporter"
EOF

%post
%systemd_post haproxy_exporter.service

%preun
%systemd_preun haproxy_exporter.service

%postun
%systemd_postun_with_restart haproxy_exporter.service

%files
%{_bindir}/haproxy_exporter
%{_unitdir}/haproxy_exporter.service
%{_sysusersdir}/haproxy_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.15.0-1
- Initial RPM package
