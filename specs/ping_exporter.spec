%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           ping_exporter
Version:        1.2.0
Release:        1%{?dist}
Summary:        Prometheus exporter for ICMP ping metrics

License:        MIT
URL:            https://github.com/czerwonk/ping_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha ac4786dc8b2448629e61708a61a57830d12f030d0112856d1be8f0621c2e4fee
%else
%global exporter_arch amd64
%global exporter_sha e876a1e6d7fa714676635bce6c7d63c1e6760917ae7ce2bb180c90cfae209615
%endif

Source0: https://github.com/czerwonk/ping_exporter/releases/download/v%{version}/ping_exporter_%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: ping_exporter.service
Source2: ping.yml

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
ping_exporter sends ICMP echo requests to configured targets and exposes
round-trip and loss metrics for Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 ping_exporter %{buildroot}%{_bindir}/ping_exporter
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

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/ping_exporter.service
install -d %{buildroot}%{_sysconfdir}/prometheus/ping_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/prometheus/ping_exporter/ping.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/ping_exporter.conf << 'EOF'
u ping_exporter - "Prometheus Ping Exporter"
EOF

%post
%systemd_post ping_exporter.service

%preun
%systemd_preun ping_exporter.service

%postun
%systemd_postun_with_restart ping_exporter.service

%files
%{_bindir}/ping_exporter
%{_unitdir}/ping_exporter.service
%{_sysusersdir}/ping_exporter.conf
%config(noreplace) %{_sysconfdir}/prometheus/ping_exporter/ping.yml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Thu Mar 26 2026 James Wilson <packages@thesystem.dev> - 1.2.0-1
- Initial RPM package
