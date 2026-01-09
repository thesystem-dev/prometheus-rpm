%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           ssl_exporter
Version:        2.4.3
Release:        1%{?dist}
Summary:        Prometheus exporter for SSL/TLS certificates

License:        Apache-2.0
URL:            https://github.com/ribbybibby/ssl_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 20d0108fd23735725c5cad29a7b782e873edda56e77a8bcb5f8cd799109b6d5c
%else
%global exporter_arch amd64
%global exporter_sha 98cacfc66a87069b451fb4cda303fcd151cbcd0a9f2fca600432950bf4fb286f
%endif

Source0: https://github.com/ribbybibby/ssl_exporter/releases/download/v%{version}/ssl_exporter_%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: ssl_exporter.service
Source2: ssl_exporter.yml

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
SSL exporter probes TLS endpoints and exposes certificate metadata and
expiry metrics to Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 ssl_exporter %{buildroot}%{_bindir}/ssl_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/ssl_exporter.service

install -d %{buildroot}%{_sysconfdir}/prometheus/ssl_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/prometheus/ssl_exporter/ssl_exporter.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/ssl_exporter.conf << 'EOF'
u ssl_exporter - "Prometheus SSL Exporter"
EOF

%post
%systemd_post ssl_exporter.service

%preun
%systemd_preun ssl_exporter.service

%postun
%systemd_postun_with_restart ssl_exporter.service

%files
%{_bindir}/ssl_exporter
%{_unitdir}/ssl_exporter.service
%{_sysusersdir}/ssl_exporter.conf
%config(noreplace) %{_sysconfdir}/prometheus/ssl_exporter/ssl_exporter.yml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 2.4.3-1
- Initial RPM package
