%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           nut_exporter
Version:        3.3.0
Release:        2%{?dist}
Summary:        Prometheus exporter for Network UPS Tools metrics

License:        Apache-2.0
URL:            https://github.com/DRuggeri/nut_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 863fc5fecac7176922a799476160afac0ccc2129302f545d3f8db56810c8bf68
%else
%global exporter_arch amd64
%global exporter_sha 8183da720ff547b7be56cc60505a3e0b731ccbf23aa18b3e297159b261500d8a
%endif

Source0: https://github.com/DRuggeri/nut_exporter/releases/download/v%{version}/nut_exporter-v%{version}-linux-%{exporter_arch}#/%{exporter_sha}
Source1: nut_exporter_LICENSE
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
* Wed May 27 2026 James Wilson <packages@thesystem.dev> - 3.3.0-2
- Vendor upstream licence file

* Fri May 15 2026 James Wilson <packages@thesystem.dev> - 3.3.0-1
- Rebase to upstream version 3.3.0

* Tue Mar 25 2026 James Wilson <packages@thesystem.dev> - 3.2.5-1
- Initial RPM package
