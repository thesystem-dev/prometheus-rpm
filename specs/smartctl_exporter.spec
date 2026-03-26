%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           smartctl_exporter
Version:        0.14.0
Release:        1%{?dist}
Summary:        Prometheus exporter for smartctl metrics

License:        Apache-2.0
URL:            https://github.com/prometheus-community/smartctl_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 27353b3adca7f54dd486417412041a17260709c724ea63f5138df2612ecf4299
%else
%global exporter_arch amd64
%global exporter_sha 875983cd27affc5a682401930e5a8eea3f06c325fe6d6a7228c5547d882685b3
%endif

Source0: https://github.com/prometheus-community/smartctl_exporter/releases/download/v%{version}/smartctl_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: smartctl_exporter.service

BuildRequires:  systemd-rpm-macros

Requires:       smartmontools >= 7.0

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}

%description
smartctl_exporter runs smartctl and exposes SMART metrics for Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd smartctl_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 smartctl_exporter %{buildroot}%{_bindir}/smartctl_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/smartctl_exporter.service

%post
%systemd_post smartctl_exporter.service

%preun
%systemd_preun smartctl_exporter.service

%postun
%systemd_postun_with_restart smartctl_exporter.service

%files
%{_bindir}/smartctl_exporter
%{_unitdir}/smartctl_exporter.service
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.14.0-1
- Initial RPM package
