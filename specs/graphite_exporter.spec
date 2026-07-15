%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           graphite_exporter
Version:        0.17.0
Release:        1%{?dist}
Summary:        Bridge Graphite metrics into Prometheus

License:        Apache-2.0
URL:            https://github.com/prometheus/graphite_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 95d49e7fa0117eb6a87d2e55409aa57e82ee6161154a6c63a9a3cfc603c3f435
%else
%global exporter_arch amd64
%global exporter_sha 109c1f946b1798fe1c9c697d1c6f5d939f5b3c21f43408c14be54b9f3e60c469
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
* Wed Jul 15 2026 James Wilson <packages@thesystem.dev> - 0.17.0-1
- Rebase to upstream version 0.17.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.16.0-1
- Initial RPM package
