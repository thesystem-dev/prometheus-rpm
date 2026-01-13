%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           apache_exporter
Version:        1.0.12
Release:        1%{?dist}
Summary:        Prometheus exporter for Apache HTTP Server

License:        Apache-2.0
URL:            https://github.com/Lusitaniae/apache_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha bf7eaebb4ba2c251fa4b6f8661e3204a11df8933415c4c1307010ff976be42b8
%else
%global exporter_arch amd64
%global exporter_sha 565993bd506d3342c51d3868a0c5bf200766c569b8ed86816b8ae5ac4245c026
%endif

Source0: https://github.com/Lusitaniae/apache_exporter/releases/download/v%{version}/apache_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: apache_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus exporter for Apache HTTP Server metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd apache_exporter-%{version}.linux-%{exporter_arch}

install -D -m 0755 apache_exporter %{buildroot}%{_bindir}/apache_exporter

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/apache_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/apache_exporter.conf << 'EOF'
u apache_exporter - "Prometheus Apache exporter"
EOF

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
%systemd_post apache_exporter.service

%preun
%systemd_preun apache_exporter.service

%postun
%systemd_postun_with_restart apache_exporter.service

%files
%{_bindir}/apache_exporter
%{_unitdir}/apache_exporter.service
%{_sysusersdir}/apache_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Tue Jan 13 2026 James Wilson <git@thesystem.dev> - 1.0.12-1
- Rebase to upstream version 1.0.12

* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 1.0.10-1
- Initial RPM package
