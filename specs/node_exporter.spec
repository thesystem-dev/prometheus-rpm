%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           node_exporter
Version:        1.10.2
Release:        1%{?dist}
Summary:        Prometheus Node Exporter

License:        Apache-2.0
URL:            https://github.com/prometheus/node_exporter

%ifarch aarch64
%global arch arm64
%global node_sha de69ec8341c8068b7c8e4cfe3eb85065d24d984a3b33007f575d307d13eb89a6
%else
%global arch amd64
%global node_sha c46e5b6f53948477ff3a19d97c58307394a29fe64a01905646f026ddc32cb65b
%endif

Source0: https://github.com/prometheus/node_exporter/releases/download/v%{version}/node_exporter-%{version}.linux-%{arch}.tar.gz#/%{node_sha}
Source1: node_exporter.service
Source2: node_exporter.tmpfiles.conf

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus exporter for host metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd node_exporter-%{version}.linux-%{arch}

install -D -m 0755 node_exporter %{buildroot}%{_bindir}/node_exporter

cd ..

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/node_exporter.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/node_exporter.conf
install -d -m 0750 %{buildroot}/var/lib/node_exporter

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/node_exporter.conf << 'EOF'
u node_exporter - "Prometheus Node Exporter" /var/lib/node_exporter
EOF

cd node_exporter-%{version}.linux-%{arch}
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


%post
%systemd_post node_exporter.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/node_exporter.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun node_exporter.service

%postun
%systemd_postun_with_restart node_exporter.service

%files
%{_bindir}/node_exporter
%{_unitdir}/node_exporter.service
%{_tmpfilesdir}/node_exporter.conf
%{_sysusersdir}/node_exporter.conf
%attr(0750,node_exporter,node_exporter) %dir /var/lib/node_exporter
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 1.10.2-1
- Initial RPM package
