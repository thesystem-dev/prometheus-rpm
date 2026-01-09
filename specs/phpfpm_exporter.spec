%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           phpfpm_exporter
Version:        2.2.0
Release:        1%{?dist}
Summary:        Prometheus exporter for PHP-FPM

License:        MIT
URL:            https://github.com/hipages/php-fpm_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 75454955ecff4200aefc00dc26032c841ff7c1f24c0cb35813da4538d43879b4
%else
%global exporter_arch amd64
%global exporter_sha b1c207fcd89f9be20104fd90bc76b3c584987ea5a769c99d5759f79af8322449
%endif

Source0: https://github.com/hipages/php-fpm_exporter/releases/download/v%{version}/php-fpm_exporter_%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: phpfpm_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus exporter for PHP-FPM metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 php-fpm_exporter %{buildroot}%{_bindir}/php-fpm_exporter
ln -s php-fpm_exporter %{buildroot}%{_bindir}/phpfpm_exporter

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/phpfpm_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/phpfpm_exporter.conf << 'EOF'
u phpfpm_exporter - "Prometheus PHP-FPM exporter"
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
%systemd_post phpfpm_exporter.service

%preun
%systemd_preun phpfpm_exporter.service

%postun
%systemd_postun_with_restart phpfpm_exporter.service

%files
%{_bindir}/php-fpm_exporter
%{_bindir}/phpfpm_exporter
%{_unitdir}/phpfpm_exporter.service
%{_sysusersdir}/phpfpm_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 2.2.0-1
- Initial RPM package
