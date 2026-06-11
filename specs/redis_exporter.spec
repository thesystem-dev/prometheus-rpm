%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           redis_exporter
Version:        1.86.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Redis metrics

License:        MIT
URL:            https://github.com/oliver006/redis_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha a4ecc3bc631713835c1016ad5d6fb3dee8a05a9fbd7a90d4f0e00655bce6d5f3
%else
%global exporter_arch amd64
%global exporter_sha 20a97421cabceb8156aad227002ee813781e318d7c2192a439c86a91b5ef70ea
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
* Thu Jun 11 2026 James Wilson <packages@thesystem.dev> - 1.86.0-1
- Rebase to upstream version 1.86.0

* Fri Jun 05 2026 James Wilson <packages@thesystem.dev> - 1.85.0-1
- Rebase to upstream version 1.85.0

* Mon May 25 2026 James Wilson <packages@thesystem.dev> - 1.84.0-1
- Rebase to upstream version 1.84.0

* Sun May 10 2026 James Wilson <packages@thesystem.dev> - 1.83.0-1
- Rebase to upstream version 1.83.0

* Tue Mar 10 2026 James Wilson <packages@thesystem.dev> - 1.82.0-1
- Rebase to upstream version 1.82.0

* Mon Feb 16 2026 James Wilson <packages@thesystem.dev> - 1.81.0-1
- Rebase to upstream version 1.81.0

* Tue Jan 27 2026 James Wilson <packages@thesystem.dev> - 1.80.2-1
- Rebase to upstream version 1.80.2

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.80.1-1
- Initial RPM package
