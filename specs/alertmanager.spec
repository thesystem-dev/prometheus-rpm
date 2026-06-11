%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           alertmanager
Version:        0.32.2
Release:        1%{?dist}
Summary:        Prometheus Alertmanager

License:        Apache-2.0
URL:            https://prometheus.io/

%ifarch aarch64
%global am_arch arm64
%global am_sha 1f223735c43bd60d4f6d5663169b8ecbb07282751431e19a64f6afa29616b66d
%else
%global am_arch amd64
%global am_sha 842f30671734e9920327aa8308e19aea7bb79c2b9905e941d83236267f87b13d
%endif

Source0: https://github.com/prometheus/alertmanager/releases/download/v%{version}/alertmanager-%{version}.linux-%{am_arch}.tar.gz#/%{am_sha}
Source1: alertmanager.service
Source2: alertmanager.yml
Source3: alertmanager.conf
Source4: alertmanager.tmpfiles.conf
Source5: alertmanager.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

%description
Alertmanager handles alerts sent by Prometheus servers.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd alertmanager-%{version}.linux-%{am_arch}

install -D -m 0755 alertmanager %{buildroot}%{_bindir}/alertmanager
install -D -m 0755 amtool       %{buildroot}%{_bindir}/amtool

install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/alertmanager/alertmanager.yml
install -D -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/alertmanager/alertmanager.conf

install -d -m 0750 %{buildroot}/var/lib/alertmanager

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/alertmanager.service
install -D -m 0644 %{SOURCE4} %{buildroot}%{_tmpfilesdir}/alertmanager.conf

install -D -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/alertmanager.conf

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


%pre
%if 0%{?rhel} == 8
getent group alertmanager >/dev/null 2>&1 || groupadd -r alertmanager >/dev/null 2>&1 || :
getent passwd alertmanager >/dev/null 2>&1 || useradd -r -g alertmanager -d /var/lib/alertmanager -s /sbin/nologin -c "Prometheus Alertmanager" alertmanager >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE5}
%endif

%post
%systemd_post alertmanager.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/alertmanager.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun alertmanager.service

%postun
%systemd_postun_with_restart alertmanager.service

%files
%{_bindir}/alertmanager
%{_bindir}/amtool
%config(noreplace) %{_sysconfdir}/alertmanager/alertmanager.yml
%config(noreplace) %{_sysconfdir}/alertmanager/alertmanager.conf
%{_unitdir}/alertmanager.service
%{_tmpfilesdir}/alertmanager.conf
%{_sysusersdir}/alertmanager.conf
%attr(0750,alertmanager,alertmanager) %dir /var/lib/alertmanager
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Thu Jun 11 2026 James Wilson <packages@thesystem.dev> - 0.32.2-1
- Rebase to upstream version 0.32.2

* Thu Apr 30 2026 James Wilson <packages@thesystem.dev> - 0.32.1-1
- Rebase to upstream version 0.32.1

* Thu Apr 09 2026 James Wilson <packages@thesystem.dev> - 0.32.0-1
- Rebase to upstream version 0.32.0

* Thu Feb 26 2026 James Wilson <packages@thesystem.dev> - 0.31.1-3
- Add ExecReload with SIGHUP support to alertmanager.service

* Mon Feb 16 2026 James Wilson <packages@thesystem.dev> - 0.31.1-2
- Add AF_NETLINK to systemd RestrictAddressFamilies to fix cluster advertise address detection

* Mon Feb 16 2026 James Wilson <packages@thesystem.dev> - 0.31.1-1
- Rebase to upstream version 0.31.1

* Thu Feb 12 2026 James Wilson <packages@thesystem.dev> - 0.30.1-4
- Fix EL8 PREIN regression; create alertmanager account in %pre on EL8 and use sysusers compat on EL9-EL10

* Wed Feb 11 2026 James Wilson <packages@thesystem.dev> - 0.30.1-2
- Create alertmanager account in %pre via sysusers for correct file ownership on install

* Tue Jan 13 2026 James Wilson <packages@thesystem.dev> - 0.30.1-1
- Rebase to upstream version 0.30.1

* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 0.30.0-1
- Initial RPM package
