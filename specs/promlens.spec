%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           promlens
Version:        0.4.0
Release:        1%{?dist}
Summary:        PromQL query analyzer UI

License:        Apache-2.0
URL:            https://github.com/prometheus/promlens

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 913764fef214dc3e13170dfcbabbf613e314c6d9e0e8287b6b38303bfb418676
%else
%global exporter_arch amd64
%global exporter_sha 1919dad57809ea5eab28522ed5cab1ac0adfeb0acb19c82e2ff4abfedc35b14c
%endif

Source0: https://github.com/prometheus/promlens/releases/download/v%{version}/promlens-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: promlens.service
Source2: promlens.tmpfiles.conf
Source3: promlens.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

%description
Promlens provides an interactive UI for inspecting and optimizing PromQL
queries.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd promlens-%{version}.linux-%{exporter_arch}
install -D -m 0755 promlens %{buildroot}%{_bindir}/promlens
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
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/promlens.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/promlens.conf

install -D -m 0644 %{SOURCE3} %{buildroot}%{_sysusersdir}/promlens.conf

install -d -m 0750 %{buildroot}/var/lib/promlens

%pre
%if 0%{?rhel} == 8
getent group promlens >/dev/null 2>&1 || groupadd -r promlens >/dev/null 2>&1 || :
getent passwd promlens >/dev/null 2>&1 || useradd -r -g promlens -d /var/lib/promlens -s /sbin/nologin -c "Promlens UI" promlens >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE3}
%endif

%post
%systemd_post promlens.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/promlens.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun promlens.service

%postun
%systemd_postun_with_restart promlens.service

%files
%{_bindir}/promlens
%{_unitdir}/promlens.service
%{_tmpfilesdir}/promlens.conf
%{_sysusersdir}/promlens.conf
%attr(0750,promlens,promlens) %dir /var/lib/promlens
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE

%changelog
* Wed Jul 15 2026 James Wilson <packages@thesystem.dev> - 0.4.0-1
- Rebase to upstream version 0.4.0

* Thu Feb 12 2026 James Wilson <packages@thesystem.dev> - 0.3.0-3
- Fix EL8 PREIN regression; create promlens account in %pre on EL8 and use sysusers compat on EL9-EL10

* Wed Feb 11 2026 James Wilson <packages@thesystem.dev> - 0.3.0-2
- Create promlens account in %pre via sysusers for correct file ownership on install

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.3.0-1
- Initial RPM package
