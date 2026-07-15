%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           sql_exporter
Version:        0.24.3
Release:        1%{?dist}
Summary:        Configuration-driven SQL metrics exporter

License:        MIT
URL:            https://github.com/burningalchemist/sql_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha ca36fdd5b51e0dee6f63faeadbbb439bdb514befcfb8eec6823cc7eaf27b5c43
%else
%global exporter_arch amd64
%global exporter_sha c043f4b3723064721bd7ecaa6200a85e41790ecea057fcab48be5558dbe9ffe8
%endif

Source0: https://github.com/burningalchemist/sql_exporter/releases/download/%{version}/sql_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: sql_exporter.service
Source2: sql_exporter.yml
Source3: postgres_database.yml
Source4: postgres_server.yml

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
SQL exporter scrapes metrics from multiple SQL databases using collector
definitions provided via configuration files.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd sql_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 sql_exporter %{buildroot}%{_bindir}/sql_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/sql_exporter.service

install -d %{buildroot}/etc/sql_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}/etc/sql_exporter/sql_exporter.yml
install -D -m 0644 %{SOURCE3} %{buildroot}/etc/sql_exporter/postgres_database.yml
install -D -m 0644 %{SOURCE4} %{buildroot}/etc/sql_exporter/postgres_server.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/sql_exporter.conf << 'EOF'
u sql_exporter - "Prometheus SQL Exporter"
EOF

%post
%systemd_post sql_exporter.service

%preun
%systemd_preun sql_exporter.service

%postun
%systemd_postun_with_restart sql_exporter.service

%files
%{_bindir}/sql_exporter
%{_unitdir}/sql_exporter.service
%{_sysusersdir}/sql_exporter.conf
%dir /etc/sql_exporter
%config(noreplace) /etc/sql_exporter/sql_exporter.yml
%config(noreplace) /etc/sql_exporter/postgres_database.yml
%config(noreplace) /etc/sql_exporter/postgres_server.yml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Jul 15 2026 James Wilson <packages@thesystem.dev> - 0.24.3-1
- Rebase to upstream version 0.24.3

* Sun Jul 05 2026 James Wilson <packages@thesystem.dev> - 0.24.2-1
- Rebase to upstream version 0.24.2

* Thu Jun 11 2026 James Wilson <packages@thesystem.dev> - 0.24.1-1
- Rebase to upstream version 0.24.1

* Wed May 27 2026 James Wilson <packages@thesystem.dev> - 0.24.0-2
- Preserve local SQL exporter config changes on upgrade

* Wed May 20 2026 James Wilson <packages@thesystem.dev> - 0.24.0-1
- Rebase to upstream version 0.24.0

* Sun May 10 2026 James Wilson <packages@thesystem.dev> - 0.23.0-1
- Rebase to upstream version 0.23.0

* Thu Apr 16 2026 James Wilson <packages@thesystem.dev> - 0.22.3-1
- Rebase to upstream version 0.22.3

* Thu Apr 09 2026 James Wilson <packages@thesystem.dev> - 0.22.2-1
- Rebase to upstream version 0.22.2

* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.21.0-1
- Rebase to upstream version 0.21.0

* Wed Mar 25 2026 James Wilson <packages@thesystem.dev> - 0.20.0-1
- Rebase to upstream version 0.20.0

* Tue Feb 17 2026 James Wilson <packages@thesystem.dev> - 0.19.1-1
- Rebase to upstream version 0.19.1

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.18.6-1
- Initial RPM package
