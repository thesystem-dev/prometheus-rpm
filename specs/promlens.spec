%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           promlens
Version:        0.3.0
Release:        2%{?dist}
Summary:        PromQL query analyzer UI

License:        Apache-2.0
URL:            https://github.com/prometheus/promlens

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 7a23434c73b22fb2ca5a9564d3014795a57182c6880a79c9a666504e2a8a3c67
%else
%global exporter_arch amd64
%global exporter_sha 8fdcc621cf559b7e55c0e3cf334b8662ae8f53cf999cdf5d7d303d2841f62ef0
%endif

Source0: https://github.com/prometheus/promlens/releases/download/v%{version}/promlens-%{version}.linux-%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: promlens.service
Source2: promlens.tmpfiles.conf
Source3: promlens.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

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
%sysusers_create_compat %{SOURCE3}

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
* Wed Feb 11 2026 James Wilson <packages@thesystem.dev> - 0.3.0-2
- Create promlens account in %pre via sysusers for correct file ownership on install

* Sat Jan 03 2026 James Wilson <packages@thesystem.dev> - 0.3.0-1
- Initial RPM package
