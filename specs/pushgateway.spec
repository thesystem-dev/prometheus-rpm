%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           pushgateway
Version:        1.11.3
Release:        1%{?dist}
Summary:        Prometheus push acceptor for batch and ephemeral jobs

License:        Apache-2.0
URL:            https://github.com/prometheus/pushgateway

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 727ff0098943657b44c21a029be9d9fcc4f249ec72dcb9f0a34aa66b2d5f1ecc
%else
%global exporter_arch amd64
%global exporter_sha bb0a44dee0953df9e8cd3c082981ff50327de56d965d83bdd9b0957d83921e38
%endif

Source0: https://github.com/prometheus/pushgateway/releases/download/v%{version}/pushgateway-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: pushgateway.service
Source2: pushgateway.tmpfiles.conf
Source3: pushgateway.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

%description
Prometheus Pushgateway allows ephemeral and batch jobs to push metrics,
which are then exposed for scraping by Prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd pushgateway-%{version}.linux-%{exporter_arch}
install -D -m 0755 pushgateway %{buildroot}%{_bindir}/pushgateway
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/pushgateway.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/pushgateway.conf

install -D -m 0644 %{SOURCE3} %{buildroot}%{_sysusersdir}/pushgateway.conf

install -d -m 0750 %{buildroot}/var/lib/pushgateway

%pre
%if 0%{?rhel} == 8
getent group pushgateway >/dev/null 2>&1 || groupadd -r pushgateway >/dev/null 2>&1 || :
getent passwd pushgateway >/dev/null 2>&1 || useradd -r -g pushgateway -d /var/lib/pushgateway -s /sbin/nologin -c "Prometheus Pushgateway" pushgateway >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE3}
%endif

%post
%systemd_post pushgateway.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/pushgateway.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun pushgateway.service

%postun
%systemd_postun_with_restart pushgateway.service

%files
%{_bindir}/pushgateway
%{_unitdir}/pushgateway.service
%{_tmpfilesdir}/pushgateway.conf
%{_sysusersdir}/pushgateway.conf
%attr(0750,pushgateway,pushgateway) %dir /var/lib/pushgateway
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Mon Jun 01 2026 James Wilson <packages@thesystem.dev> - 1.11.3-1
- Rebase to upstream version 1.11.3

* Thu Feb 12 2026 James Wilson <packages@thesystem.dev> - 1.11.2-3
- Fix EL8 PREIN regression; create pushgateway account in %pre on EL8 and use sysusers compat on EL9-EL10

* Wed Feb 11 2026 James Wilson <packages@thesystem.dev> - 1.11.2-2
- Create pushgateway account in %pre via sysusers for correct file ownership on install

* Tue Jan 13 2026 James Wilson <packages@thesystem.dev> - 1.11.2-1
- Rebase to upstream version 1.11.2

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 1.11.0-1
- Initial RPM package
