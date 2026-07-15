%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           prometheus-lts
Version:        3.5.5
Release:        1%{?dist}
Summary:        Prometheus monitoring system and time series database (LTS)

License:        Apache-2.0
URL:            https://prometheus.io/

%ifarch aarch64
%global prom_arch arm64
%global prom_sha b4676dba3271deea2a92a3e85ac31cde67be707fdff54c5dbf48c9f2ecac5085
%else
%global prom_arch amd64
%global prom_sha 64d0beab873272b861a91df41668bc852c7e2e5b23f75c16059fb15b5630c577
%endif

%global prom_srcdir prometheus-%{version}.linux-%{prom_arch}

Source0: https://github.com/prometheus/prometheus/releases/download/v%{version}/prometheus-%{version}.linux-%{prom_arch}.tar.gz#/%{prom_sha}
Source1: prometheus-lts.service
Source2: prometheus-lts.tmpfiles.conf
Source3: prometheus-lts.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
Conflicts:      prometheus
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

%description
Prometheus is a systems and service monitoring system. It collects metrics
from configured targets at given intervals, evaluates rule expressions,
displays the results, and can trigger alerts if some condition is observed
to be true.

This package tracks the current Prometheus long-term support (LTS) release line and
installs the same runtime layout as the standard package. It cannot be
co-installed with prometheus.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd %{prom_srcdir}

install -D -m 0755 prometheus %{buildroot}%{_bindir}/prometheus
install -D -m 0755 promtool   %{buildroot}%{_bindir}/promtool

# Configuration (ship upstream example config)
install -D -m 0644 prometheus.yml %{buildroot}%{_sysconfdir}/prometheus/prometheus.yml

# Runtime data directory
install -d -m 0750 %{buildroot}/var/lib/prometheus

# systemd unit
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/prometheus.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/prometheus.conf

# sysusers (EL8+)
install -D -m 0644 %{SOURCE3} %{buildroot}%{_sysusersdir}/prometheus.conf

# License
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
getent group prometheus >/dev/null 2>&1 || groupadd -r prometheus >/dev/null 2>&1 || :
getent passwd prometheus >/dev/null 2>&1 || useradd -r -g prometheus -d /var/lib/prometheus -s /sbin/nologin -c "Prometheus monitoring system" prometheus >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE3}
%endif

%post
%systemd_post prometheus.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/prometheus.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun prometheus.service

%postun
%systemd_postun_with_restart prometheus.service

%files
%{_bindir}/prometheus
%{_bindir}/promtool
%config(noreplace) %{_sysconfdir}/prometheus/prometheus.yml
%{_unitdir}/prometheus.service
%{_tmpfilesdir}/prometheus.conf
%{_sysusersdir}/prometheus.conf
%attr(0750,prometheus,prometheus) %dir /var/lib/prometheus
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Jul 15 2026 James Wilson <packages@thesystem.dev> - 3.5.5-1
- Rebase to upstream version 3.5.5

* Sun Jun 21 2026 James Wilson <packages@thesystem.dev> - 3.5.4-1
- Rebase to upstream version 3.5.4

* Tue Apr 28 2026 James Wilson <packages@thesystem.dev> - 3.5.3-1
- Rebase to upstream version 3.5.3

* Thu Apr 16 2026 James Wilson <packages@thesystem.dev> - 3.5.2-1
- Rebase to upstream version 3.5.2

* Wed Mar 25 2026 James Wilson <packages@thesystem.dev> - 3.5.1-1
- Add Prometheus LTS package for the supported release line
