%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           node_exporter
Version:        1.12.1
Release:        1%{?dist}
Summary:        Prometheus Node Exporter

License:        Apache-2.0
URL:            https://github.com/prometheus/node_exporter

%ifarch aarch64
%global arch arm64
%global node_sha ad35b605f9954b9f1ffddf5ba054bdc5a98d790b9eae5291e1eeb83f1ecbd0e7
%else
%global arch amd64
%global node_sha b51d8a76aa2a9156a55d501aca6276fae09e262259a5e4e831d2c2222f084e63
%endif

Source0: https://github.com/prometheus/node_exporter/releases/download/v%{version}/node_exporter-%{version}.linux-%{arch}.tar.gz#/%{node_sha}
Source1: node_exporter.service
Source2: node_exporter.tmpfiles.conf
Source3: node_exporter.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

%description
Prometheus exporter for host metrics.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd node_exporter-%{version}.linux-%{arch}

install -D -m 0755 node_exporter %{buildroot}%{_bindir}/node_exporter

cd ..

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/node_exporter.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/node_exporter.conf
install -d -m 0750 %{buildroot}/var/lib/node_exporter

install -D -m 0644 %{SOURCE3} %{buildroot}%{_sysusersdir}/node_exporter.conf

cd node_exporter-%{version}.linux-%{arch}
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
getent group node_exporter >/dev/null 2>&1 || groupadd -r node_exporter >/dev/null 2>&1 || :
getent passwd node_exporter >/dev/null 2>&1 || useradd -r -g node_exporter -d /var/lib/node_exporter -s /sbin/nologin -c "Prometheus Node Exporter" node_exporter >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE3}
%endif

%post
%systemd_post node_exporter.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/node_exporter.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun node_exporter.service

%postun
%systemd_postun_with_restart node_exporter.service

%files
%{_bindir}/node_exporter
%{_unitdir}/node_exporter.service
%{_tmpfilesdir}/node_exporter.conf
%{_sysusersdir}/node_exporter.conf
%attr(0750,node_exporter,node_exporter) %dir /var/lib/node_exporter
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Jul 15 2026 James Wilson <packages@thesystem.dev> - 1.12.1-1
- Rebase to upstream version 1.12.1

* Thu Apr 09 2026 James Wilson <packages@thesystem.dev> - 1.11.1-1
- Rebase to upstream version 1.11.1

* Thu Feb 12 2026 James Wilson <packages@thesystem.dev> - 1.10.2-4
- Fix EL8 PREIN regression; create node_exporter account in %pre on EL8 and use sysusers compat on EL9-EL10

* Wed Feb 11 2026 James Wilson <packages@thesystem.dev> - 1.10.2-3
- Create node_exporter account in %pre via sysusers for correct file ownership on install

* Sun Feb 08 2026 James Wilson <packages@thesystem.dev> - 1.10.2-2
- Allow AF_NETLINK in systemd sandbox for arp/netdev collectors

* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 1.10.2-1
- Initial RPM package
