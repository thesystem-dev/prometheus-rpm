%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           pgbouncer_exporter
Version:        0.11.1
Release:        1%{?dist}
Summary:        Prometheus exporter for PgBouncer

License:        MIT
URL:            https://github.com/prometheus-community/pgbouncer_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha f29fa44523bd872fd136d947998055754d9492f130e008ae316ec1f8984063a0
%else
%global exporter_arch amd64
%global exporter_sha de95a3d22141c0f84ac33de07e793c4993410f43d7c10e8ba281559381e031da
%endif

Source0: https://github.com/prometheus-community/pgbouncer_exporter/releases/download/v%{version}/pgbouncer_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: pgbouncer_exporter.service

BuildRequires: systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
PgBouncer exporter provides Prometheus metrics about PgBouncer pooler
statistics and health.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd pgbouncer_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 pgbouncer_exporter %{buildroot}%{_bindir}/pgbouncer_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/pgbouncer_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/pgbouncer_exporter.conf << 'EOF'
u pgbouncer_exporter - "Prometheus PgBouncer Exporter"
EOF

%post
%systemd_post pgbouncer_exporter.service

%preun
%systemd_preun pgbouncer_exporter.service

%postun
%systemd_postun_with_restart pgbouncer_exporter.service

%files
%{_bindir}/pgbouncer_exporter
%{_unitdir}/pgbouncer_exporter.service
%{_sysusersdir}/pgbouncer_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Tue Feb 17 2026 James Wilson <git@thesystem.dev> - 0.11.1-1
- Rebase to upstream version 0.11.1

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.11.0-1
- Initial RPM package
