%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           smokeping_prober
Version:        0.11.0
Release:        1%{?dist}
Summary:        Prometheus smokeping-style prober

License:        Apache-2.0
URL:            https://github.com/SuperQ/smokeping_prober

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 9a2389d6ff1b9d15c7843561a1855e067dad58e382eaf8f9b0d0ac4e03a1cf89
%else
%global exporter_arch amd64
%global exporter_sha 92dcefd7d0da8c58f46e0466e34c455234bee18355824be1bff1707b1d6e8e66
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
* Tue Mar 10 2026 James Wilson <packages@thesystem.dev> - 0.11.0-1
- Rebase to upstream version 0.11.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.10.0-1
- Initial RPM package
