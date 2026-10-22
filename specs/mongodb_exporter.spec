%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           mongodb_exporter
Version:        0.54.0
Release:        1%{?dist}
Summary:        Prometheus exporter for MongoDB metrics

License:        Apache-2.0
URL:            https://github.com/percona/mongodb_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 79cb0d5137cc439d9ad385fe23667273d4f9c5a960c33141ed99b85e28172552
%else
%global exporter_arch amd64
%global exporter_sha 84e5c8145f4e78df2915f5aa8f3ccddbfd1b817d6a29db5a27525bb68b4095b4
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
* Thu Oct 22 2026 James Wilson <packages@thesystem.dev> - 0.54.0-1
- Rebase to upstream version 0.54.0

* Fri Aug 21 2026 James Wilson <packages@thesystem.dev> - 0.53.0-1
- Rebase to upstream version 0.53.0

* Mon Aug 03 2026 James Wilson <packages@thesystem.dev> - 0.52.0-1
- Rebase to upstream version 0.52.0

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
