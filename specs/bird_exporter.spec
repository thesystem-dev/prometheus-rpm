%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           bird_exporter
Version:        1.5.0
Release:        1%{?dist}
Summary:        Prometheus exporter for BIRD routing daemon metrics

License:        MIT
URL:            https://github.com/czerwonk/bird_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha cfbe0e32408bee3c3707fd46cfc15fe9a5fa8b51f1dad73c594af6bfe21155d0
%else
%global exporter_arch amd64
%global exporter_sha 1b7f7850d001f9aad4484ff4a74e68cfef9a578ed86a472b9574e4d3e2d12e20
%endif

Source0: https://github.com/czerwonk/bird_exporter/releases/download/v%{version}/bird_exporter_%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: bird_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
bird_exporter connects to BIRD control sockets and exposes routing metrics for
Prometheus scraping.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 bird_exporter %{buildroot}%{_bindir}/bird_exporter
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

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/bird_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/bird_exporter.conf << 'EOF'
u bird_exporter - "Prometheus BIRD Exporter"
EOF

%post
%systemd_post bird_exporter.service

%preun
%systemd_preun bird_exporter.service

%postun
%systemd_postun_with_restart bird_exporter.service

%files
%{_bindir}/bird_exporter
%{_unitdir}/bird_exporter.service
%{_sysusersdir}/bird_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Fri May 15 2026 James Wilson <packages@thesystem.dev> - 1.5.0-1
- Rebase to upstream version 1.5.0

* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 1.4.5-1
- Initial RPM package
