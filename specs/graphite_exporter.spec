%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           graphite_exporter
Version:        0.16.0
Release:        1%{?dist}
Summary:        Bridge Graphite metrics into Prometheus

License:        Apache-2.0
URL:            https://github.com/prometheus/graphite_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha bcdd1eb0ff0b974c93bc4d5c6b2c92140f63215c98aafb0379dff9bf82c776db
%else
%global exporter_arch amd64
%global exporter_sha 129acf14bb62dc32596ff8aed40a526a66260b2736801bc546be407436dd32d8
%endif

Source0: https://github.com/prometheus/graphite_exporter/releases/download/v%{version}/graphite_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: graphite_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The Prometheus Graphite exporter accepts metrics via the Graphite
plaintext protocol and exposes them for scraping by Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd graphite_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 graphite_exporter %{buildroot}%{_bindir}/graphite_exporter
install -D -m 0755 getool %{buildroot}%{_bindir}/graphite_getool
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/graphite_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/graphite_exporter.conf << 'EOF'
u graphite_exporter - "Prometheus Graphite Exporter"
EOF

%post
%systemd_post graphite_exporter.service

%preun
%systemd_preun graphite_exporter.service

%postun
%systemd_postun_with_restart graphite_exporter.service

%files
%{_bindir}/graphite_exporter
%{_bindir}/graphite_getool
%{_unitdir}/graphite_exporter.service
%{_sysusersdir}/graphite_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.16.0-1
- Initial RPM package
