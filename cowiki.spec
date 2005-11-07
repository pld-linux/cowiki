# TODO
#  - lighttpd integration possible <http://wiki.lighttpd.net/33.html>.

# snapshot: DATE
%define _snap 2005-11-07

%if 0%{?_snap}
%define _source http://snaps.cowiki.org/%{name}-%{version}-interim-%{_snap}.tar.gz
%else
%define _source http://www.cowiki.org/download/%{name}-%{version}.tar.gz
%endif
%define _rel 0.9

Summary:	Web collaboration tool
Summary(pl):	Narzêdzie do wspó³pracy i wspó³tworzenia w sieci
Name:		cowiki
Version:	0.4.0
Release:	%{?_snap:0.%(echo %{_snap} | tr -d -).}%{_rel}
Epoch:		0
License:	GPL
Group:		Applications/WWW
Source0:	%{_source}
# Source0-md5:	aea66d8526e1633b942ad2f6d3aa1110
Source1:	%{name}.conf
Patch0:		%{name}-FHS.patch
Patch1:		%{name}-config.patch
URL:		http://cowiki.org/
BuildRequires:	rpmbuild(macros) >= 1.221
Requires:	php >= 4:5.0.2
Requires:	php-mysql
Requires:	php-dom
Requires:	apache(mod_auth)
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_appdir %{_datadir}/%{name}
%define		_sysconfdir	/etc/%{name}

%description
coWiki is a sophisticated but easy to use web collaboration tool that
helps you and your co-workers to create and organize web documents,
weblogs and knowledgebases or any other document structures directly
in their HTML browser. You may evolve ideas and gain a concomitant XML
documentation of your brainstorming without having to concentrate on
complicated structural syntaxes.

%description -l pl
coWiki to wyszukane, ale ³atwe w u¿yciu narzêdzie do pracy zespo³owej
przez WWW pomagaj±ce wspó³pracownikom tworzyæ i organizowaæ dokumenty
WWW, weblogi, bazy wiedzy lub dowolne inne struktury dokumentów
bezpo¶rednio w przegl±darce HTML. Mo¿na rozwijaæ idee i otrzymywaæ
towarzysz±c± dokumentacjê XML burzy mózgów bez potrzeby koncentrowania
siê na skomplikowanej sk³adni strukturalnej.

%package setup
Summary:	coWiki setup package
Summary(pl):	Pakiet do wstêpnej konfiguracji coWiki
Group:		Applications/WWW
PreReq:		%{name} = %{epoch}:%{version}-%{release}

%description setup
Install this package to configure initial coWiki installation. You
should uninstall this package when you're done, as it considered
insecure to keep the setup files in place.

%description setup -l pl
Ten pakiet nale¿y zainstalowaæ w celu wstêpnej konfiguracji coWiki po
pierwszej instalacji. Potem nale¿y go odinstalowaæ, jako ¿e
pozostawienie plików instalacyjnych mog³oby byæ niebezpieczne.

%prep
%setup -q %{?_snap:-n %{name}-%{version}-interim-%{_snap}}
%patch0 -p1
%patch1 -p1

mv includes/cowiki/core.conf-dist .
rm {htdocs,includes/cowiki}/.cvsignore
mv htdocs/.htaccess .
rm htdocs/setup/LICENSE # GPL

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_appdir},%{_sysconfdir},/var/cache/%{name}}

cp -a htdocs includes misc $RPM_BUILD_ROOT%{_appdir}
install core.conf-dist $RPM_BUILD_ROOT%{_sysconfdir}/core.conf
install %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf

# for setup
install LICENSE $RPM_BUILD_ROOT%{_appdir}/htdocs/setup
install core.conf-dist $RPM_BUILD_ROOT%{_appdir}/includes/cowiki/core.conf-dist
touch $RPM_BUILD_ROOT%{_appdir}/htdocs/install.seal

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ "$1" = 1 ]; then
%banner %{name} -e <<EOF
Install the database using the appropriate "misc/database/*.sql" schema.
You must setup authorization and coWiki root password in:
- %{_sysconfdir}/core.conf

EOF
fi

%preun
if [ "$1" = "0" ]; then
	# nuke cache
	# FIXME could suffer too many arguments error
	rm -f /var/cache/%{name}/*
fi

%post setup
chgrp http %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
chmod g+w %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
rm -f %{_appdir}/htdocs/install.seal

%postun setup
if [ "$1" = "0" ]; then
	chgrp root %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
	chmod g-w %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
	touch %{_appdir}/htdocs/install.seal
fi

%triggerin -- apache1 >= 1.3.33-2
%apache_config_install -v 1 -c %{_sysconfdir}/apache.conf

%triggerun -- apache1 >= 1.3.33-2
%apache_config_uninstall -v 1

%triggerin -- apache >= 2.0.0
%apache_config_install -v 2 -c %{_sysconfdir}/apache.conf

%triggerun -- apache >= 2.0.0
%apache_config_uninstall -v 2

# cache dir moved
%triggerun -- %{name} < 0.4.0-0.20050618.3
# FIXME could suffer too many arguments error
rm -f /var/lib/%{name}/*

%files
%defattr(644,root,root,755)
%doc ChangeLog INSTALL* NEWS
%doc README.IDIOM README.PLUGIN SKEL.PLUGIN
%doc misc/database
%attr(751,root,root) %dir %{_sysconfdir}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/apache.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/core.conf

%dir %{_appdir}
%{_appdir}/misc
%dir %{_appdir}/includes
%dir %{_appdir}/includes/cowiki
%{_appdir}/includes/cowiki/class
%{_appdir}/includes/cowiki/locale
%{_appdir}/includes/cowiki/plugin
%{_appdir}/includes/cowiki/*.php
%dir %{_appdir}/htdocs
%{_appdir}/htdocs/img
%{_appdir}/htdocs/tpl
%{_appdir}/htdocs/*.txt
%{_appdir}/htdocs/*.php
%{_appdir}/htdocs/favicon.ico
%{_appdir}/htdocs/include.path

%dir %attr(770,root,http) /var/cache/%{name}

# setup seal
%config(noreplace,missingok) %verify(not md5 mtime size) %{_appdir}/htdocs/install.seal

%files setup
%defattr(644,root,root,755)
%{_appdir}/htdocs/setup
%{_appdir}/htdocs/install.pending
%{_appdir}/includes/cowiki/core.conf-dist
