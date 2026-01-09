%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           kafka_exporter
Version:        1.9.0
Release:        1%{?dist}
Summary:        Prometheus exporter for Kafka brokers

License:        Apache-2.0
URL:            https://github.com/danielqsj/kafka_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha b6991fcb50d2dc87fde02e003dc8c1b742022ab3becf30e4bb9979b22c1d37d8
%else
%global exporter_arch amd64
%global exporter_sha c722518ad71c53b3988ea26ae2bd387bb596ce7a98fc639d08bf639a537699a1
%endif

Source0: https://github.com/danielqsj/kafka_exporter/releases/download/v%{version}/kafka_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: kafka_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Kafka exporter scrapes Kafka brokers for consumer lag, partition and broker
health, making those metrics available to Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd kafka_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 kafka_exporter %{buildroot}%{_bindir}/kafka_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/kafka_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/kafka_exporter.conf << 'EOF'
u kafka_exporter - "Prometheus Kafka Exporter"
EOF

%post
%systemd_post kafka_exporter.service

%preun
%systemd_preun kafka_exporter.service

%postun
%systemd_postun_with_restart kafka_exporter.service

%files
%{_bindir}/kafka_exporter
%{_unitdir}/kafka_exporter.service
%{_sysusersdir}/kafka_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.9.0-1
- Initial RPM package
