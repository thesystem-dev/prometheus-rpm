%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           nut_exporter
Version:        3.2.5
Release:        1%{?dist}
Summary:        Prometheus exporter for Network UPS Tools metrics

License:        Apache-2.0
URL:            https://github.com/DRuggeri/nut_exporter

%global license_sha256 ecaa994a1672a71d6511ab8686c1452ef9e3114f08f6355e36640dc66ae3ced9

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha f5fa05294427f154ece133facc23c54a1fdb8ac34765f332f70dad4a3c83280c
%else
%global exporter_arch amd64
%global exporter_sha ee2929c43a910bc16bb0c3cc505c40c7d285fefa8717f4d08895e0c087f52cdf
%endif

Source0: https://github.com/DRuggeri/nut_exporter/releases/download/v%{version}/nut_exporter-v%{version}-linux-%{exporter_arch}#/%{exporter_sha}
Source1: https://raw.githubusercontent.com/DRuggeri/nut_exporter/v%{version}/LICENSE#/%{license_sha256}
Source2: nut_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
nut_exporter scrapes Network UPS Tools servers and exposes UPS metrics for
Prometheus.

%prep
mkdir -p src
install -m 0755 %{SOURCE0} src/nut_exporter

%build
/bin/true

%install
install -D -m 0755 src/nut_exporter %{buildroot}%{_bindir}/nut_exporter
install -D -m 0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
NOTICE_DST="%{buildroot}%{_licensedir}/%{name}/NOTICE"
if [ -f NOTICE ]; then
  install -D -m 0644 NOTICE "$NOTICE_DST"
else
  install -D -m 0644 /dev/null "$NOTICE_DST"
  cat > "$NOTICE_DST" <<'EOF'
NOTICE file not provided in upstream release %{version}; placeholder added to document the absence for compliance.
EOF
fi

install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/nut_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/nut_exporter.conf << 'EOF'
u nut_exporter - "Prometheus NUT Exporter"
EOF

%post
%systemd_post nut_exporter.service

%preun
%systemd_preun nut_exporter.service

%postun
%systemd_postun_with_restart nut_exporter.service

%files
%{_bindir}/nut_exporter
%{_unitdir}/nut_exporter.service
%{_sysusersdir}/nut_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Tue Mar 25 2026 James Wilson <packages@thesystem.dev> - 3.2.5-1
- Initial RPM package
