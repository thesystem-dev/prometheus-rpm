%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           blackbox_exporter
Version:        0.28.0
Release:        1%{?dist}
Summary:        Prometheus blackbox prober

License:        Apache-2.0
URL:            https://github.com/prometheus/blackbox_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha afb5581b1d4ea45078eebc96e4f989f912d1144d2cc131db8a6c0963bcc6a654
%else
%global exporter_arch amd64
%global exporter_sha 4b1bb299c685ecff75d41e55e90aae8e02a658395fb14092c7f9c5c9d75016c7
%endif

Source0: https://github.com/prometheus/blackbox_exporter/releases/download/v%{version}/blackbox_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: blackbox_exporter.service
Source2: blackbox_exporter.yml

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
The blackbox exporter allows blackbox probing of endpoints over HTTP(S),
TCP, ICMP, and DNS and exposes the probe results as Prometheus metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd blackbox_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 blackbox_exporter %{buildroot}%{_bindir}/blackbox_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/blackbox_exporter.service

install -d %{buildroot}%{_sysconfdir}/prometheus/blackbox_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/prometheus/blackbox_exporter/blackbox.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/blackbox_exporter.conf << 'EOF'
u blackbox_exporter - "Prometheus Blackbox Exporter"
EOF

%post
%systemd_post blackbox_exporter.service

%preun
%systemd_preun blackbox_exporter.service

%postun
%systemd_postun_with_restart blackbox_exporter.service

%files
%{_bindir}/blackbox_exporter
%{_unitdir}/blackbox_exporter.service
%{_sysusersdir}/blackbox_exporter.conf
%config(noreplace) %{_sysconfdir}/prometheus/blackbox_exporter/blackbox.yml
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Tue Jan 13 2026 James Wilson <git@thesystem.dev> - 0.28.0-1
- Rebase to upstream version 0.28.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.26.0-1
- Initial RPM package
