# TODO
#  - lighttpd integration possible <http://wiki.lighttpd.net/33.html>.

# snapshot: DATE
%define _snap 2005-11-07

%if 0%{?_snap}
%define _source http://snaps.cowiki.org/%{name}-%{version}-interim-%{_snap}.tar.gz
%else
%define _source http://www.cowiki.org/download/%{name}-%{version}.tar.gz
%endif
%define _rel 0.1

Summary:	Web collaboration tool
Summary(pl):	Narz�dzie do wsp�pracy i wsp�tworzenia w sieci
Name:		cowiki
Version:	0.4.0
Release:	%{?_snap:0.%(echo %{_snap} | tr -d -).}%{_rel}
Epoch:		0
License:	GPL
Group:		Applications/WWW
Source0:	%{_source}
# Source0-md5:	aea66d8526e1633b942ad2f6d3aa1110
Patch0:		%{name}-FHS.patch
URL:		http://cowiki.org/
#BuildRequires:	rpmbuild(macros) >= 1.223
Requires:	php >= 4:5.0.2
Requires:	php-mysql
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
coWiki to wyszukane, ale �atwe w u�yciu narz�dzie do pracy zespo�owej
przez WWW pomagaj�ce wsp�pracownikom tworzy� i organizowa� dokumenty
WWW, weblogi, bazy wiedzy lub dowolne inne struktury dokument�w
bezpo�rednio w przegl�darce HTML. Mo�na rozwija� idee i otrzymywa�
towarzysz�c� dokumentacj� XML burzy m�zg�w bez potrzeby koncentrowania
si� na skomplikowanej sk�adni strukturalnej.

%prep
%setup -q %{?_snap:-n %{name}-%{version}-interim-%{_snap}}
%patch0 -p1

mv includes/cowiki/core.conf-dist .
rm {htdocs,includes/cowiki}/.cvsignore
mv htdocs/.htaccess .
rm htdocs/setup/LICENSE # GPL

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_appdir},%{_sysconfdir},/var/cache/%{name}}

cp -a htdocs includes $RPM_BUILD_ROOT%{_appdir}

sed -e '
    s,CHECK_INTERVAL = .*,CHECK_INTERVAL = "-1",
    s,RETURN_PATH = .*,RETURN_PATH = "postmaster@localhost",
    s,ABUSE_PATH = .*,ABUSE_PATH = "abuse@localhost",
    s,ROOT_PASSWD = .*,ROOT_PASSWD = "XXX",
    s,LOOKUP_DNS = .*,LOOKUP_DNS = off,
    s,TEMP = .*,TEMP = "/var/cache/%{name}/",

' core.conf-dist > $RPM_BUILD_ROOT%{_sysconfdir}/core.conf
echo -e '\n; vim: ft=dosini' >> $RPM_BUILD_ROOT%{_sysconfdir}/core.conf

# unfortunately cowiki works only as vhost root
cat <<EOF >> $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
<Directory /usr/share/cowiki/htdocs>
    Allow from all
</Directory>

<VirtualHost *:80>
	ServerName cowiki
	DocumentRoot /usr/share/cowiki/htdocs

EOF
sed -ne '/BEGIN/,/END/p' .htaccess >> $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
cat <<EOF >> $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
</VirtualHost>
EOF

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
%dir %{_sysconfdir}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/apache.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/core.conf
%{_appdir}
%dir %attr(770,root,http) /var/cache/%{name}
