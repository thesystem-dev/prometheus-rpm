%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           squid_exporter
Version:        1.13.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Squid proxy metrics

License:        MIT
URL:            https://github.com/boynux/squid-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 3f8b9be5d4b16d7973e9219997425995e9299e524ec80d89e20863af06f8962c
%else
%global exporter_arch amd64
%global exporter_sha 35a8902fdd81f47e88701e8528e84b017c61a8bb03792094455388240772cf90
%endif

Source0: https://github.com/boynux/squid-exporter/releases/download/v%{version}/squid-exporter-linux-%{exporter_arch}#/%{exporter_sha}
Source1: https://raw.githubusercontent.com/boynux/squid-exporter/v%{version}/LICENSE
Source2: squid_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Exports metrics from the Squid proxy cache in Prometheus format.

%prep
rm -rf %{name}-%{version}
mkdir -p %{name}-%{version}
install -pm 0755 %{SOURCE0} %{name}-%{version}/squid_exporter
install -pm 0644 %{SOURCE1} %{name}-%{version}/LICENSE

%build
/bin/true

%install
cd %{name}-%{version}
install -D -m 0755 squid_exporter %{buildroot}%{_bindir}/squid_exporter
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
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/squid_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/squid_exporter.conf << 'EOF'
u squid_exporter - "Prometheus Squid Exporter"
EOF

%post
%systemd_post squid_exporter.service

%preun
%systemd_preun squid_exporter.service

%postun
%systemd_postun_with_restart squid_exporter.service

%files
%{_bindir}/squid_exporter
%{_unitdir}/squid_exporter.service
%{_sysusersdir}/squid_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Tue Jan 13 2026 James Wilson <packages@thesystem.dev> - 1.13.0-1
- Rebase to upstream version 1.13.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.13.0-1
- Initial RPM package
