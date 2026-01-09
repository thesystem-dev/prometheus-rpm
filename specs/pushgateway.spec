%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           pushgateway
Version:        1.11.0
Release:        1%{?dist}
Summary:        Prometheus push acceptor for batch and ephemeral jobs

License:        Apache-2.0
URL:            https://github.com/prometheus/pushgateway

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 4d6faa82083513d60d7450e6867cc6f4f78a892e7f698500ea97772677690b55
%else
%global exporter_arch amd64
%global exporter_sha 5888b0c36d1b8e85950b6eb81ad168ff485a139807896a8727f877813690170c
%endif

Source0: https://github.com/prometheus/pushgateway/releases/download/v%{version}/pushgateway-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: pushgateway.service
Source2: pushgateway.tmpfiles.conf

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus Pushgateway allows ephemeral and batch jobs to push metrics,
which are then exposed for scraping by Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd pushgateway-%{version}.linux-%{exporter_arch}
install -D -m 0755 pushgateway %{buildroot}%{_bindir}/pushgateway
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/pushgateway.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/pushgateway.conf

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/pushgateway.conf << 'EOF'
u pushgateway - "Prometheus Pushgateway" /var/lib/pushgateway
EOF

install -d -m 0750 %{buildroot}/var/lib/pushgateway

%post
%systemd_post pushgateway.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/pushgateway.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun pushgateway.service

%postun
%systemd_postun_with_restart pushgateway.service

%files
%{_bindir}/pushgateway
%{_unitdir}/pushgateway.service
%{_tmpfilesdir}/pushgateway.conf
%{_sysusersdir}/pushgateway.conf
%attr(0750,pushgateway,pushgateway) %dir /var/lib/pushgateway
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.11.0-1
- Initial RPM package
