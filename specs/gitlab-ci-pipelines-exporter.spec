%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           gitlab-ci-pipelines-exporter
Version:        0.6.0
Release:        1%{?dist}
Summary:        Prometheus exporter for GitLab CI pipelines

License:        Apache-2.0
URL:            https://github.com/mvisonneau/gitlab-ci-pipelines-exporter

%ifarch aarch64
%global exporter_arch arm64
%global exporter_sha 0ac09c1733a1da1d99e7d32e99d358ac1ddd66512ade91684043f26ac41e0c18
%else
%global exporter_arch amd64
%global exporter_sha 6c83cc99278c02d675768b6dc8a59477aea0e82991d76cbfe0ff658321ead2c7
%endif

Source0: https://github.com/mvisonneau/gitlab-ci-pipelines-exporter/releases/download/v%{version}/gitlab-ci-pipelines-exporter_v%{version}_linux_%{exporter_arch}.tar.gz#/%{exporter_sha}
Source1: gitlab-ci-pipelines-exporter.service
Source2: gitlab-ci-pipelines-exporter.sysusers
Source3: gitlab-ci-pipelines-exporter.yml.example

BuildRequires:  systemd-rpm-macros
Requires:       ca-certificates

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

%description
gitlab-ci-pipelines-exporter collects pipeline, job and deployment metrics
from the GitLab API and exposes them for Prometheus scraping.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
install -D -m 0755 gitlab-ci-pipelines-exporter %{buildroot}%{_bindir}/gitlab-ci-pipelines-exporter
install -D -m 0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE
install -D -m 0644 README.md %{buildroot}%{_pkgdocdir}/README.md

install -D -m 0644 helpers/autocomplete/bash %{buildroot}%{_datadir}/bash-completion/completions/%{name}
install -D -m 0644 helpers/autocomplete/zsh %{buildroot}%{_datadir}/zsh/site-functions/_%{name}
install -D -m 0644 helpers/autocomplete/fish %{buildroot}%{_datadir}/fish/vendor_completions.d/%{name}.fish
install -D -m 0644 helpers/autocomplete/pwsh %{buildroot}%{_pkgdocdir}/completions/%{name}.ps1

install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/gitlab-ci-pipelines-exporter.service
install -d -m 0750 %{buildroot}%{_sysconfdir}/gitlab-ci-pipelines-exporter
install -D -m 0640 %{SOURCE3} %{buildroot}%{_sysconfdir}/gitlab-ci-pipelines-exporter/config.yml.example
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/gitlab-ci-pipelines-exporter.conf

%pre
%if 0%{?rhel} == 8
getent group gitlab-ci-pipelines-exporter >/dev/null 2>&1 || groupadd -r gitlab-ci-pipelines-exporter >/dev/null 2>&1 || :
getent passwd gitlab-ci-pipelines-exporter >/dev/null 2>&1 || useradd -r -g gitlab-ci-pipelines-exporter -M -s /sbin/nologin -c "GitLab CI Pipelines Exporter" gitlab-ci-pipelines-exporter >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE2}
%endif

%post
%systemd_post gitlab-ci-pipelines-exporter.service

%preun
%systemd_preun gitlab-ci-pipelines-exporter.service

%postun
%systemd_postun_with_restart gitlab-ci-pipelines-exporter.service

%files
%{_bindir}/gitlab-ci-pipelines-exporter
%{_unitdir}/gitlab-ci-pipelines-exporter.service
%dir %attr(0750,root,gitlab-ci-pipelines-exporter) %{_sysconfdir}/gitlab-ci-pipelines-exporter
%config(noreplace) %attr(0640,root,gitlab-ci-pipelines-exporter) %{_sysconfdir}/gitlab-ci-pipelines-exporter/config.yml.example
%{_sysusersdir}/gitlab-ci-pipelines-exporter.conf
%dir %{_datadir}/bash-completion
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/%{name}
%dir %{_datadir}/zsh
%dir %{_datadir}/zsh/site-functions
%{_datadir}/zsh/site-functions/_%{name}
%dir %{_datadir}/fish
%dir %{_datadir}/fish/vendor_completions.d
%{_datadir}/fish/vendor_completions.d/%{name}.fish
%license %{_licensedir}/%{name}/LICENSE
%doc %{_pkgdocdir}/README.md
%doc %{_pkgdocdir}/completions

%changelog
* Thu Sep 24 2026 James Wilson <packages@thesystem.dev> - 0.6.0-1
- Initial RPM package
