%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           frr_exporter
Version:        1.12.0
Release:        1%{?dist}
Summary:        Prometheus exporter for FRR metrics

License:        MIT
URL:            https://github.com/tynany/frr_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha aad52c19e759ce85d7f3bc490eba630a49d91e48dab23f9066cc665de11402c9
%else
%global exporter_arch amd64
%global exporter_sha 5279e275ec23e32902dd5c2cfac0c3ebf2f5673184bab367151dacf740888428
%endif

Source0: https://github.com/tynany/frr_exporter/releases/download/v%{version}/frr_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: frr_exporter_LICENSE
Source2: frr_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
frr_exporter connects to FRR daemon sockets and exposes routing metrics for
Prometheus scraping.

%prep
rm -rf %{name}-%{version}
mkdir -p %{name}-%{version}
tar -xf %{SOURCE0} -C %{name}-%{version} --strip-components=1
install -pm 0644 %{SOURCE1} %{name}-%{version}/LICENSE

%build
/bin/true

%install
cd %{name}-%{version}
install -D -m 0755 frr_exporter %{buildroot}%{_bindir}/frr_exporter
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
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/frr_exporter.service

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/frr_exporter.conf << 'EOF'
u frr_exporter - "Prometheus FRR Exporter"
EOF

%post
%systemd_post frr_exporter.service

%preun
%systemd_preun frr_exporter.service

%postun
%systemd_postun_with_restart frr_exporter.service

%files
%{_bindir}/frr_exporter
%{_unitdir}/frr_exporter.service
%{_sysusersdir}/frr_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Jul 29 2026 James Wilson <packages@thesystem.dev> - 1.12.0-1
- Rebase to upstream version 1.12.0

* Wed May 27 2026 James Wilson <packages@thesystem.dev> - 1.11.0-2
- Vendor upstream licence file

* Thu Apr 09 2026 James Wilson <packages@thesystem.dev> - 1.11.0-1
- Rebase to upstream version 1.11.0

* Fri Mar 27 2026 James Wilson <packages@thesystem.dev> - 1.10.1-1
- Initial RPM package
