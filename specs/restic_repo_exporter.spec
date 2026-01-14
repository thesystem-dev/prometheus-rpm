%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           restic_repo_exporter
Version:        0.0.15
Release:        1%{?dist}
Summary:        Prometheus exporter for Restic repositories

License:        MIT
URL:            https://github.com/Worty/restic-repo-exporter

%ifarch aarch64
%global archive_arch arm64
%else
%global archive_arch amd64
%endif

Source0: https://github.com/Worty/restic-repo-exporter/releases/download/v%{version}/restic-repo-exporter_%{version}_linux_%{archive_arch}.tar.gz#/restic-repo-exporter-%{version}.linux-%{archive_arch}.tar.gz
Source1: restic_repo_exporter.service

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

Requires:       restic

%description
restic-repo-exporter collects health and usage metrics from one or more Restic
repositories and exposes them for Prometheus scraping.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 restic-repo-exporter %{buildroot}%{_bindir}/restic_repo_exporter
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

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/restic_repo_exporter.service
install -d -m 0750 %{buildroot}%{_sysconfdir}/restic_repo_exporter.d

install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/restic_repo_exporter.conf << 'EOF'
u restic_repo_exporter - "Restic Repository Exporter"
EOF

%post
%systemd_post restic_repo_exporter.service

%preun
%systemd_preun restic_repo_exporter.service

%postun
%systemd_postun_with_restart restic_repo_exporter.service

%files
%{_bindir}/restic_repo_exporter
%{_unitdir}/restic_repo_exporter.service
%dir %attr(0750,root,root) %{_sysconfdir}/restic_repo_exporter.d
%{_sysusersdir}/restic_repo_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Jan 14 2026 James Wilson <packages@thesystem.dev> - 0.0.15-1
- Initial RPM package
