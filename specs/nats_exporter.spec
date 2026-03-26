%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           nats_exporter
Version:        0.19.1
Release:        1%{?dist}
Summary:        Prometheus exporter for NATS metrics

License:        Apache-2.0
URL:            https://github.com/nats-io/prometheus-nats-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha e9ad85ab2d2da7b28e076db35b010d1d3be38a50991abaf335940bbcefa6b9d6
%else
%global exporter_arch x86_64
%global exporter_sha 74c896a226d2b561daeae42f47110a535c9562b3ddbaafc04ea8092d0c4704ca
%endif

Source0: https://github.com/nats-io/prometheus-nats-exporter/releases/download/v%{version}/prometheus-nats-exporter-v%{version}-linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: nats_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The NATS exporter scrapes NATS monitoring endpoints and exposes them in
Prometheus format.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 prometheus-nats-exporter %{buildroot}%{_bindir}/nats_exporter
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

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/nats_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/nats_exporter.conf << 'EOF'
u nats_exporter - "Prometheus NATS Exporter"
EOF

%post
%systemd_post nats_exporter.service

%preun
%systemd_preun nats_exporter.service

%postun
%systemd_postun_with_restart nats_exporter.service

%files
%{_bindir}/nats_exporter
%{_unitdir}/nats_exporter.service
%{_sysusersdir}/nats_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.19.1-1
- Initial RPM package
