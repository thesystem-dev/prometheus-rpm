%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           prometheus-paperless-exporter
Version:        0.0.9
Release:        1%{?dist}
Summary:        Prometheus exporter for Paperless-ngx

License:        BSD-3-Clause
URL:            https://github.com/hansmi/prometheus-paperless-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 596775fcb3d6e211838a64a2e6e5a219c155cb3403eb3fe4181c6e76035fac91
%else
%global exporter_arch amd64
%global exporter_sha 6f3335f821651a24b5e0599a1d8e304f542f9918b690e4c2eee2ed789b898276
%endif

Source0: https://github.com/hansmi/prometheus-paperless-exporter/releases/download/v%{version}/prometheus-paperless-exporter_%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: prometheus-paperless-exporter.service
Source2: prometheus-paperless-exporter.sysusers

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

%description
prometheus-paperless-exporter collects metrics from a Paperless-ngx instance
and exposes them for Prometheus scraping.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
cd prometheus-paperless-exporter_%{version}_linux_%{exporter_arch}

install -D -m 0755 prometheus-paperless-exporter %{buildroot}%{_bindir}/prometheus-paperless-exporter
install -D -m 0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE
install -D -m 0644 README.md %{buildroot}%{_pkgdocdir}/README.md

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/prometheus-paperless-exporter.service
install -d -m 0750 %{buildroot}%{_sysconfdir}/prometheus-paperless-exporter

install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/prometheus-paperless-exporter.conf

%pre
%if 0%{?rhel} == 8
getent group prometheus-paperless-exporter >/dev/null 2>&1 || groupadd -r prometheus-paperless-exporter >/dev/null 2>&1 || :
getent passwd prometheus-paperless-exporter >/dev/null 2>&1 || useradd -r -g prometheus-paperless-exporter -M -s /sbin/nologin -c "Prometheus Paperless Exporter" prometheus-paperless-exporter >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE2}
%endif

%post
%systemd_post prometheus-paperless-exporter.service

%preun
%systemd_preun prometheus-paperless-exporter.service

%postun
%systemd_postun_with_restart prometheus-paperless-exporter.service

%files
%{_bindir}/prometheus-paperless-exporter
%{_unitdir}/prometheus-paperless-exporter.service
%dir %attr(0750,root,prometheus-paperless-exporter) %{_sysconfdir}/prometheus-paperless-exporter
%{_sysusersdir}/prometheus-paperless-exporter.conf
%license %{_licensedir}/%{name}/LICENSE
%doc %{_pkgdocdir}/README.md

%changelog
* Thu Jul 16 2026 James Wilson <packages@thesystem.dev> - 0.0.9-1
- Initial RPM package
