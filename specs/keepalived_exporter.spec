%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0
%{!?_pkgdocdir:%global _pkgdocdir %{_docdir}/%{name}}

Name:           keepalived_exporter
Version:        1.7.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Keepalived metrics

License:        GPL-3.0-only
URL:            https://github.com/mehdy/keepalived-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 0c97ff5753f9172bbd6d28109114c75c1812c3fe6ef31bcf264c00216c1c0673
%else
%global exporter_arch amd64
%global exporter_sha 4e0045670392ffea9b324d935a62bbd7bc1537362ae1e8e71e3973611b7a5d9c
%endif

Source0: https://github.com/mehdy/keepalived-exporter/releases/download/v%{version}/keepalived-exporter_%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: keepalived_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Keepalived exporter surfaces VRRP/Keepalived metrics by parsing keepalived
state files or emitting JSON signals, allowing Prometheus to alert on VIP
health.

%prep
rm -rf %{name}-%{version}
mkdir -p %{name}-%{version}
tar -xf %{SOURCE0} -C %{name}-%{version}

%build
/bin/true

%install
cd %{name}-%{version}
install -D -m 0755 keepalived-exporter %{buildroot}%{_bindir}/keepalived-exporter
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

if [ -f README.md ]; then
  install -d %{buildroot}%{_pkgdocdir}
  install -m 0644 README.md %{buildroot}%{_pkgdocdir}/README.md
fi

cd ..
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/keepalived_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/keepalived_exporter.conf << 'EOF'
u keepalived_exporter - "Prometheus Keepalived Exporter"
EOF

%post
%systemd_post keepalived_exporter.service

%preun
%systemd_preun keepalived_exporter.service

%postun
%systemd_postun_with_restart keepalived_exporter.service

%files
%{_bindir}/keepalived-exporter
%{_unitdir}/keepalived_exporter.service
%{_sysusersdir}/keepalived_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE
%doc %{_pkgdocdir}/README.md

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.7.0-1
- Switch to mehdy/keepalived-exporter (GPLv3, multi-arch builds)
