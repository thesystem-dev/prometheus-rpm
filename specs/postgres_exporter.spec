%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           postgres_exporter
Version:        0.21.1
Release:        1%{?dist}
Summary:        Prometheus exporter for PostgreSQL metrics

License:        Apache-2.0
URL:            https://github.com/prometheus-community/postgres_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha a52fb28b0ae9975b75fb7eb55458941a5960ff05b16d9375816f9c7266c89828
%else
%global exporter_arch amd64
%global exporter_sha 02f316da4e9e409749d6f3b25102d3561cb408023110f3653f6514548926ff0c
%endif

Source0: https://github.com/prometheus-community/postgres_exporter/releases/download/v%{version}/postgres_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: postgres_exporter.service
Source2: postgres_exporter_queries.yaml

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The postgres_exporter exposes PostgreSQL metrics (connections, replication,
statistics) for scraping by Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd postgres_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 postgres_exporter %{buildroot}%{_bindir}/postgres_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/postgres_exporter.service

install -d %{buildroot}%{_sysconfdir}/prometheus/postgres_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/prometheus/postgres_exporter/queries.yaml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/postgres_exporter.conf << 'EOF'
u postgres_exporter - "Prometheus Postgres Exporter"
EOF

%post
%systemd_post postgres_exporter.service

%preun
%systemd_preun postgres_exporter.service

%postun
%systemd_postun_with_restart postgres_exporter.service

%files
%{_bindir}/postgres_exporter
%{_unitdir}/postgres_exporter.service
%{_sysusersdir}/postgres_exporter.conf
%config(noreplace) %{_sysconfdir}/prometheus/postgres_exporter/queries.yaml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Nov 18 2026 James Wilson <packages@thesystem.dev> - 0.21.1-1
- Rebase to upstream version 0.21.1

* Wed Nov 18 2026 James Wilson <packages@thesystem.dev> - 0.21.0-1
- Rebase to upstream version 0.21.0

* Wed Jul 08 2026 James Wilson <packages@thesystem.dev> - 0.20.1-1
- Rebase to upstream version 0.20.1

* Wed Jul 01 2026 James Wilson <packages@thesystem.dev> - 0.20.0-1
- Rebase to upstream version 0.20.0

* Wed May 27 2026 James Wilson <packages@thesystem.dev> - 0.19.1-2
- Vendor upstream queries config

* Sun Mar 01 2026 James Wilson <packages@thesystem.dev> - 0.19.1-1
- Rebase to upstream version 0.19.1

* Mon Feb 16 2026 James Wilson <packages@thesystem.dev> - 0.19.0-1
- Rebase to upstream version 0.19.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.18.1-1
- Initial RPM package
