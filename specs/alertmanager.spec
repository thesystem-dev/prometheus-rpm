%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           alertmanager
Version:        0.30.1
Release:        2%{?dist}
Summary:        Prometheus Alertmanager

License:        Apache-2.0
URL:            https://prometheus.io/

%ifarch aarch64
%global am_arch arm64
%global am_sha 061a5ab3998fb8af75192980a559c7bfa3892da55098da839d7a79d94abe0b61
%else
%global am_arch amd64
%global am_sha 86fd95034e3e17094d6951118c54b396200be22a1c16af787e1f7129ebce8f1f
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
%{?sysusers_requires_compat}

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
%sysusers_create_compat %{SOURCE5}

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
* Wed Feb 11 2026 James Wilson <packages@thesystem.dev> - 0.30.1-2
- Create alertmanager account in %pre via sysusers for correct file ownership on install

* Tue Jan 13 2026 James Wilson <git@thesystem.dev> - 0.30.1-1
- Rebase to upstream version 0.30.1

* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 0.30.0-1
- Initial RPM package
