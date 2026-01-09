%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           consul_exporter
Version:        0.13.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Consul health and service metrics

License:        Apache-2.0
URL:            https://github.com/prometheus/consul_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha a5ecc969647cc67f171eff13468e25fe713f95a8af4135e1c0cf716a64c5474f
%else
%global exporter_arch amd64
%global exporter_sha 2a8da4147330c6e19c9665deca1c419d507e100de6c8b7c58c0715ff25453773
%endif

Source0: https://github.com/prometheus/consul_exporter/releases/download/v%{version}/consul_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: consul_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The Consul exporter exposes Consul service and health information for
scraping by Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd consul_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 consul_exporter %{buildroot}%{_bindir}/consul_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/consul_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/consul_exporter.conf << 'EOF'
u consul_exporter - "Prometheus Consul Exporter"
EOF

%post
%systemd_post consul_exporter.service

%preun
%systemd_preun consul_exporter.service

%postun
%systemd_postun_with_restart consul_exporter.service

%files
%{_bindir}/consul_exporter
%{_unitdir}/consul_exporter.service
%{_sysusersdir}/consul_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.13.0-1
- Initial RPM package
