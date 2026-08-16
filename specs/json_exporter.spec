%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           json_exporter
Version:        0.8.0
Release:        1%{?dist}
Summary:        Prometheus exporter for arbitrary JSON endpoints

License:        Apache-2.0
URL:            https://github.com/prometheus-community/json_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 69341074badc20963e4698f34d2c94b759bc278160f0bf4639b9e7ed15afd02e
%else
%global exporter_arch amd64
%global exporter_sha bd25fe58f62cec131b2ecbe859358990bb07f0266439ddcdef501fdd182a4fe1
%endif

Source0: https://github.com/prometheus-community/json_exporter/releases/download/v%{version}/json_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: json_exporter.service
Source2: json_exporter.yml

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
JSON exporter fetches arbitrary HTTP/JSON payloads and maps them into
Prometheus metrics using configurable JSONPath expressions.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd json_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 json_exporter %{buildroot}%{_bindir}/json_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/json_exporter.service

install -d %{buildroot}%{_sysconfdir}/prometheus/json_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/prometheus/json_exporter/config.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/json_exporter.conf << 'EOF'
u json_exporter - "Prometheus JSON Exporter"
EOF

%post
%systemd_post json_exporter.service

%preun
%systemd_preun json_exporter.service

%postun
%systemd_postun_with_restart json_exporter.service

%files
%{_bindir}/json_exporter
%{_unitdir}/json_exporter.service
%{_sysusersdir}/json_exporter.conf
%config(noreplace) %{_sysconfdir}/prometheus/json_exporter/config.yml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Aug 15 2026 James Wilson <packages@thesystem.dev> - 0.8.0-1
- Rebase to upstream version 0.8.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.7.0-1
- Initial RPM package
