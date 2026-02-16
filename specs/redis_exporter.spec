%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           redis_exporter
Version:        1.81.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Redis metrics

License:        MIT
URL:            https://github.com/oliver006/redis_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha a807907d413edb1c0aa88513e7c1570c302873bd1cfcbf36fb53a14629177882
%else
%global exporter_arch amd64
%global exporter_sha 1818cc2cbd3bac62a6f43054a2cc1596fc5f6148ce80112a6308bc3cad6d81fa
%endif

Source0: https://github.com/oliver006/redis_exporter/releases/download/v%{version}/redis_exporter-v%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: redis_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The redis_exporter bridges Redis metrics (command stats, replication,
memory, keyspace) into Prometheus format.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd redis_exporter-v%{version}.linux-%{exporter_arch}
install -D -m 0755 redis_exporter %{buildroot}%{_bindir}/redis_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/redis_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/redis_exporter.conf << 'EOF'
u redis_exporter - "Prometheus Redis Exporter"
EOF

%post
%systemd_post redis_exporter.service

%preun
%systemd_preun redis_exporter.service

%postun
%systemd_postun_with_restart redis_exporter.service

%files
%{_bindir}/redis_exporter
%{_unitdir}/redis_exporter.service
%{_sysusersdir}/redis_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Mon Feb 16 2026 James Wilson <git@thesystem.dev> - 1.81.0-1
- Rebase to upstream version 1.81.0

* Tue Jan 27 2026 James Wilson <git@thesystem.dev> - 1.80.2-1
- Rebase to upstream version 1.80.2

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.80.1-1
- Initial RPM package
