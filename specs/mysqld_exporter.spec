%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           mysqld_exporter
Version:        0.18.0
Release:        1%{?dist}
Summary:        Prometheus exporter for MySQL

License:        Apache-2.0
URL:            https://github.com/prometheus/mysqld_exporter

%ifarch aarch64
%global go_arch arm64
%global go_sha abdb452600ca086b68244aadf8045fbf0b6a48dcb76eed5576995806c176f6ce
%else
%global go_arch amd64
%global go_sha 46e8f45654352bdd42d162b2b4a68f00055d45acc168f9c068235b9e3acc39c1
%endif

Source0: https://github.com/prometheus/mysqld_exporter/releases/download/v%{version}/mysqld_exporter-%{version}.linux-%{go_arch}.tar.gz#/%{go_sha}
Source1: mysqld_exporter.service
Source2: mysqld_exporter.my.cnf

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus exporter for MySQL metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd mysqld_exporter-%{version}.linux-%{go_arch}

install -D -m 0755 mysqld_exporter %{buildroot}%{_bindir}/mysqld_exporter

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/mysqld_exporter.service

install -d %{buildroot}%{_sysconfdir}/mysqld_exporter
install -D -m 0600 %{SOURCE2} %{buildroot}%{_sysconfdir}/mysqld_exporter/.my.cnf

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/mysqld_exporter.conf << 'EOF'
u mysqld_exporter - "Prometheus MySQL exporter"
EOF

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


%post
%systemd_post mysqld_exporter.service

%preun
%systemd_preun mysqld_exporter.service

%postun
%systemd_postun_with_restart mysqld_exporter.service

%files
%{_bindir}/mysqld_exporter
%{_unitdir}/mysqld_exporter.service
%dir %{_sysconfdir}/mysqld_exporter
%config(noreplace) %{_sysconfdir}/mysqld_exporter/.my.cnf
%{_sysusersdir}/mysqld_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 0.18.0-1
- Initial RPM package
