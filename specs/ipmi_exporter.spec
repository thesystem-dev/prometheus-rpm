%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           ipmi_exporter
Version:        1.10.1
Release:        1%{?dist}
Summary:        Prometheus exporter for IPMI metrics

License:        MIT
URL:            https://github.com/prometheus-community/ipmi_exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha fe7a5a699538c543cea7e6ab1d4e553647275c3e20ced1da42501a1aef1f7278
%else
%global exporter_arch amd64
%global exporter_sha 5a0fb507db69433c49d7c6beb2912854cc0996dd6fa66091bc4bc6b7ce8ffea0
%endif

Source0: https://github.com/prometheus-community/ipmi_exporter/releases/download/v%{version}/ipmi_exporter-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: ipmi_exporter.service
Source2: ipmi_exporter.yml
Source3: ipmi_exporter_sudoers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
IPMI exporter scrapes sensors locally or via RMCP using FreeIPMI tools.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd ipmi_exporter-%{version}.linux-%{exporter_arch}
install -D -m 0755 ipmi_exporter %{buildroot}%{_bindir}/ipmi_exporter
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/ipmi_exporter.service

install -d %{buildroot}/etc/ipmi_exporter
install -D -m 0644 %{SOURCE2} %{buildroot}/etc/ipmi_exporter/ipmi_local.yml

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/ipmi_exporter.conf << 'EOF'
u ipmi_exporter - "Prometheus IPMI Exporter"
EOF

install -D -m 0440 %{SOURCE3} %{buildroot}%{_sysconfdir}/sudo.d/ipmi_exporter

%post
%systemd_post ipmi_exporter.service

%preun
%systemd_preun ipmi_exporter.service

%postun
%systemd_postun_with_restart ipmi_exporter.service

%files
%{_bindir}/ipmi_exporter
%{_unitdir}/ipmi_exporter.service
%dir /etc/ipmi_exporter
/etc/ipmi_exporter/ipmi_local.yml
%{_sysconfdir}/sudo.d/ipmi_exporter
%{_sysusersdir}/ipmi_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.10.1-1
- Initial RPM package
