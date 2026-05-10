%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           mongodb_exporter
Version:        0.51.0
Release:        1%{?dist}
Summary:        Prometheus exporter for MongoDB metrics

License:        Apache-2.0
URL:            https://github.com/percona/mongodb_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha f2f023d2d632c3b9cdc873558f26a8940efc197c1b36bbf96da17416a60eead6
%else
%global exporter_arch amd64
%global exporter_sha 01dfae78c737fb48761a715d779cade464a84cce7a2a70357ac4af469bade198
%endif

Source0: https://github.com/percona/mongodb_exporter/releases/download/v%{version}/mongodb_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: mongodb_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
MongoDB exporter emits server status, replicaset, and cluster metrics so
Prometheus can monitor MongoDB/Percona Server deployments.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd mongodb_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 mongodb_exporter %{buildroot}%{_bindir}/mongodb_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/mongodb_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/mongodb_exporter.conf << 'EOF'
u mongodb_exporter - "Prometheus MongoDB Exporter"
EOF

%post
%systemd_post mongodb_exporter.service

%preun
%systemd_preun mongodb_exporter.service

%postun
%systemd_postun_with_restart mongodb_exporter.service

%files
%{_bindir}/mongodb_exporter
%{_unitdir}/mongodb_exporter.service
%{_sysusersdir}/mongodb_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sun May 10 2026 James Wilson <packages@thesystem.dev> - 0.51.0-1
- Rebase to upstream version 0.51.0

* Thu Apr 09 2026 James Wilson <packages@thesystem.dev> - 0.50.0-1
- Rebase to upstream version 0.50.0

* Tue Mar 03 2026 James Wilson <packages@thesystem.dev> - 0.49.0-1
- Rebase to upstream version 0.49.0

* Tue Feb 17 2026 James Wilson <packages@thesystem.dev> - 0.48.0-1
- Rebase to upstream version 0.48.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.47.2-1
- Initial RPM package
