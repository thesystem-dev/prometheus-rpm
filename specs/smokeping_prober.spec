%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           smokeping_prober
Version:        0.10.0
Release:        1%{?dist}
Summary:        Prometheus smokeping-style prober

License:        Apache-2.0
URL:            https://github.com/SuperQ/smokeping_prober

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 7c0e7311206a578327f00428c9dd917ec85b40dbf04f1917b9efed5a76b13524
%else
%global exporter_arch amd64
%global exporter_sha d17b0ed4a0e75a957ef96aeb085da8df6db5209d3b8aaca1f56ad3d571dfc22b
%endif

Source0: https://github.com/SuperQ/smokeping_prober/releases/download/v%{version}/smokeping_prober-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: smokeping_prober.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Smokeping prober sends ICMP/UDP probes like SmokePing and exports the
latency histograms for Prometheus scraping.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd smokeping_prober-%{version}.linux-%{exporter_arch}
install -D -m 0755 smokeping_prober %{buildroot}%{_bindir}/smokeping_prober
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/smokeping_prober.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/smokeping_prober.conf << 'EOF'
u smokeping_prober - "Prometheus Smokeping Prober"
EOF

%post
%systemd_post smokeping_prober.service

%preun
%systemd_preun smokeping_prober.service

%postun
%systemd_postun_with_restart smokeping_prober.service

%files
%{_bindir}/smokeping_prober
%{_unitdir}/smokeping_prober.service
%{_sysusersdir}/smokeping_prober.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.10.0-1
- Initial RPM package
