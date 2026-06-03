%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0
%if 0%{?rhel}
%global el_major %{rhel}
%else
%global el_major 10
%endif

Name:           thesystem-release
Version:        %{el_major}
Release:        1%{?dist}
Summary:        Repository configuration for thesystem RPM packages

License:        MIT
URL:            https://github.com/thesystem-dev/prometheus-rpm
Source0:        prometheus-rpm.repo
Source1:        RPM-GPG-KEY-thesystem-dev
Source2:        thesystem-release_LICENSE

BuildArch:      noarch
Requires:       system-release

%description
Repository configuration and GPG key for thesystem RPM repositories.

%prep
/bin/true

%build
/bin/true

%install
install -D -m 0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/yum.repos.d/prometheus-rpm.repo
install -D -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-thesystem-dev
install -D -m 0644 %{SOURCE2} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%config(noreplace) %{_sysconfdir}/yum.repos.d/prometheus-rpm.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-thesystem-dev
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Wed Jun 03 2026 James Wilson <packages@thesystem.dev>
- Add repository bootstrap package
