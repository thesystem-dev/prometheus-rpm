%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           bind_exporter
Version:        0.8.0
Release:        1%{?dist}
Summary:        Prometheus exporter for BIND statistics

License:        Apache-2.0
URL:            https://github.com/prometheus-community/bind_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha ba2515d87dd90b6e32f13a9f84d8cab2311b3e8315ad68b1780d746533f54b00
%else
%global exporter_arch amd64
%global exporter_sha 837c9ef62a8b960f9ebdd241991d46f7c7a26f2db510254993986e50d75d37a4
%endif

Source0: https://github.com/prometheus-community/bind_exporter/releases/download/v%{version}/bind_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: bind_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Bind exporter scrapes statistics from the BIND named statistics channel.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd bind_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 bind_exporter %{buildroot}%{_bindir}/bind_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/bind_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/bind_exporter.conf << 'EOF'
u bind_exporter - "Prometheus Bind Exporter"
EOF

%post
%systemd_post bind_exporter.service

%preun
%systemd_preun bind_exporter.service

%postun
%systemd_postun_with_restart bind_exporter.service

%files
%{_bindir}/bind_exporter
%{_unitdir}/bind_exporter.service
%{_sysusersdir}/bind_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.8.0-1
- Initial RPM package
