%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           nats_exporter
Version:        0.20.1
Release:        1%{?dist}
Summary:        Prometheus exporter for NATS metrics

License:        Apache-2.0
URL:            https://github.com/nats-io/prometheus-nats-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha ab9af0a192c0845ab96f85bc0637f359a168ecfb2894128ea227ae47b4b83855
%else
%global exporter_arch x86_64
%global exporter_sha a8798bee71effc2473e48f6b166e63e207a7bb7a7e93ffbb643a1d840607b8ae
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
* Mon Jun 01 2026 James Wilson <packages@thesystem.dev> - 0.20.1-1
- Rebase to upstream version 0.20.1

* Wed May 20 2026 James Wilson <packages@thesystem.dev> - 0.20.0-1
- Rebase to upstream version 0.20.0

* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.19.2-1
- Rebase to upstream version 0.19.2

* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 0.19.1-1
- Initial RPM package
