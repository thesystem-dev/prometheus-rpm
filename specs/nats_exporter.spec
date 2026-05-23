%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           nats_exporter
Version:        0.20.0
Release:        1%{?dist}
Summary:        Prometheus exporter for NATS metrics

License:        Apache-2.0
URL:            https://github.com/nats-io/prometheus-nats-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha aec0f1d4ceeb99f5d2a40b6a2eb1802c14eb536dc1c644e161ae02a94b4cf488
%else
%global exporter_arch x86_64
%global exporter_sha cacb1215b65b807242dafc1ac097923246dce72b35e829117849ad88f5b5201f
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
* Wed May 20 2026 James Wilson <packages@thesystem.dev> - 0.20.0-1
- Rebase to upstream version 0.20.0

* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.19.2-1
- Rebase to upstream version 0.19.2

* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.19.1-1
- Initial RPM package
