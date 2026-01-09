%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           nginx_exporter
Version:        1.5.1
Release:        1%{?dist}
Summary:        Prometheus exporter for NGINX

License:        Apache-2.0
URL:            https://github.com/nginxinc/nginx-prometheus-exporter

%ifarch aarch64
%global go_arch arm64
%global go_sha 8bea88fe912c63791de1fd35c8829f89c2e18b87fdb001c9b65fc371b2ebef3c
%else
%global go_arch amd64
%global go_sha 42ddc7ac31c70021d2a5c10414d473526490769632c1ef430b95d76dd1e3c187
%endif

Source0: https://github.com/nginxinc/nginx-prometheus-exporter/releases/download/v%{version}/nginx-prometheus-exporter_%{version}_linux_%{go_arch}.tar.gz#/%{go_sha}
Source1: nginx_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Prometheus exporter for NGINX metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 nginx-prometheus-exporter %{buildroot}%{_bindir}/nginx_exporter

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/nginx_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/nginx_exporter.conf << 'EOF'
u nginx_exporter - "Prometheus NGINX exporter"
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
%systemd_post nginx_exporter.service

%preun
%systemd_preun nginx_exporter.service

%postun
%systemd_postun_with_restart nginx_exporter.service

%files
%{_bindir}/nginx_exporter
%{_unitdir}/nginx_exporter.service
%{_sysusersdir}/nginx_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 1.5.1-1
- Initial RPM package
