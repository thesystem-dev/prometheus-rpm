%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           restic_repo_exporter
Version:        0.0.17
Release:        1%{?dist}
Summary:        Prometheus exporter for Restic repositories

License:        MIT
URL:            https://github.com/Worty/restic-repo-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha c6d32a2c16f6472bf7593d3ad2e8d7909d002565fbdf09858e694316c8f29724
%else
%global exporter_arch amd64
%global exporter_sha 3a05810312dfd926b695cca73e6cf98f6dcb29e2e48c3ff4b07b380fb6fad58e
%endif

Source0: https://github.com/Worty/restic-repo-exporter/releases/download/v%{version}/restic-repo-exporter_%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: restic_repo_exporter.service
Source2: restic_repo_exporter.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

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

install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/restic_repo_exporter.conf

%pre
%if 0%{?rhel} == 8
getent group restic_repo_exporter >/dev/null 2>&1 || groupadd -r restic_repo_exporter >/dev/null 2>&1 || :
getent passwd restic_repo_exporter >/dev/null 2>&1 || useradd -r -g restic_repo_exporter -M -s /sbin/nologin -c "Restic Repository Exporter" restic_repo_exporter >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE2}
%endif

%post
%systemd_post restic_repo_exporter.service

%preun
%systemd_preun restic_repo_exporter.service

%postun
%systemd_postun_with_restart restic_repo_exporter.service

%files
%{_bindir}/restic_repo_exporter
%{_unitdir}/restic_repo_exporter.service
%dir %attr(0750,root,restic_repo_exporter) %{_sysconfdir}/restic_repo_exporter.d
%{_sysusersdir}/restic_repo_exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Sun Jul 05 2026 James Wilson <packages@thesystem.dev> - 0.0.17-1
- Rebase to upstream version 0.0.17

* Thu Jun 25 2026 James Wilson <packages@thesystem.dev> - 0.0.16-1
- Rebase to upstream version 0.0.16

* Wed May 27 2026 James Wilson <packages@thesystem.dev> - 0.0.15-4
- Pin upstream release asset checksums

* Mon May 25 2026 James Wilson <packages@thesystem.dev> - 0.0.15-3
- Allow restic_repo_exporter to read credential files under /etc/restic_repo_exporter.d

* Wed May 13 2026 James Wilson <packages@thesystem.dev> - 0.0.15-2
- Correct systemd unit environment variable handling

* Wed Jan 14 2026 James Wilson <packages@thesystem.dev> - 0.0.15-1
- Initial RPM package
