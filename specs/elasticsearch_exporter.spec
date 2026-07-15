%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           elasticsearch_exporter
Version:        1.11.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Elasticsearch stats

License:        Apache-2.0
URL:            https://github.com/prometheus-community/elasticsearch_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 7020d10e29896d329cecc7bfe2e90dcc376d68fc0c75ac27014af3747870ce1f
%else
%global exporter_arch amd64
%global exporter_sha 2bebc50d6980578ad37a376000bc039485ceea129ae229f78baed3379db4f61c
%endif

Source0: https://github.com/prometheus-community/elasticsearch_exporter/releases/download/v%{version}/elasticsearch_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: elasticsearch_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Elasticsearch exporter transforms cluster health and index statistics into
Prometheus metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd elasticsearch_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 elasticsearch_exporter %{buildroot}%{_bindir}/elasticsearch_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/elasticsearch_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/elasticsearch_exporter.conf << 'EOF'
u elasticsearch_exporter - "Prometheus Elasticsearch Exporter"
EOF

%post
%systemd_post elasticsearch_exporter.service

%preun
%systemd_preun elasticsearch_exporter.service

%postun
%systemd_postun_with_restart elasticsearch_exporter.service

%files
%{_bindir}/elasticsearch_exporter
%{_unitdir}/elasticsearch_exporter.service
%{_sysusersdir}/elasticsearch_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Jul 15 2026 James Wilson <packages@thesystem.dev> - 1.11.0-1
- Rebase to upstream version 1.11.0

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.10.0-1
- Initial RPM package
