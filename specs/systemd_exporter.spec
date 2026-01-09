%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           systemd_exporter
Version:        0.7.0
Release:        1%{?dist}
Summary:        Prometheus exporter for systemd metrics

License:        Apache-2.0
URL:            https://github.com/prometheus-community/systemd_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 7b80b5d3a29ca8658ed4ef4c05ead29fcc7dc03349cac72376178f9a94299918
%else
%global exporter_arch amd64
%global exporter_sha 2d995ca20249aeeac8f507173176ce5d162f17470a98ca66e289c85b388480c3
%endif

Source0: https://github.com/prometheus-community/systemd_exporter/releases/download/v%{version}/systemd_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: systemd_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The systemd exporter exposes unit status and cgroup metrics so Prometheus
can monitor systemd-managed services.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd systemd_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 systemd_exporter %{buildroot}%{_bindir}/systemd_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/systemd_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/systemd_exporter.conf << 'EOF'
u systemd_exporter - "Prometheus Systemd Exporter"
EOF

%post
%systemd_post systemd_exporter.service

%preun
%systemd_preun systemd_exporter.service

%postun
%systemd_postun_with_restart systemd_exporter.service

%files
%{_bindir}/systemd_exporter
%{_unitdir}/systemd_exporter.service
%{_sysusersdir}/systemd_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.7.0-1
- Initial RPM package
