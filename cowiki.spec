# TODO
#  - lighttpd integration possible <http://wiki.lighttpd.net/33.html>.
Summary:	Web collaboration tool
Name:		cowiki
Version:	0.3.3
Release:	0.14
Epoch:		0
License:	GPL
Group:		Applications/WWW
Source0:	http://cowiki.org/download/%{name}-%{version}.tar.gz
# Source0-md5:	91f995347ed5791f052285124223b87b
Patch0:		%{name}-FHS.patch
Patch1:		%{name}-class-case.patch
URL:		http://cowiki.org/
BuildRequires:	rpmbuild(macros) >= 1.177
Requires:	php >= 5.0.2
Requires:	php-mysql
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_appdir %{_datadir}/%{name}
%define		_sysconfdir	/etc/%{name}
%define		_apache1dir	/etc/apache
%define		_apache2dir	/etc/httpd

%description
coWiki is a sophisticated but easy to use web collaboration tool that
helps you and your co-workers to create and organize web documents,
weblogs and knowledgebases or any other document structures directly
in their HTML browser. You may evolve ideas and gain a concomitant XML
documentation of your brainstorming without having to concentrate on
complicated structural syntaxes.

%prep
%setup -q
%patch0 -p1
%patch1 -p1

mv includes/cowiki/core.conf-dist .
rm -f {htdocs,includes/cowiki}/.cvsignore
mv htdocs/.htaccess .

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_appdir},%{_sysconfdir}}

cp -a htdocs includes $RPM_BUILD_ROOT%{_appdir}

sed -e '
    s/CHECK_INTERVAL = .*/CHECK_INTERVAL = "-1"/
    s/RETURN_PATH = .*/RETURN_PATH = "your.bounce.email@localhost"/
    s/ABUSE_PATH = .*/ABUSE_PATH = "abuse@localhost"/
    s/ROOT_PASSWD = .*/ROOT_PASSWD = "XXX"/
    s/LOOKUP_DNS = .*/LOOKUP_DNS = off/
' core.conf-dist > $RPM_BUILD_ROOT%{_sysconfdir}/%{name}.ini

# unfortunately cowiki works only as vhost root
cat <<EOF >> $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
<Directory /usr/share/cowiki/htdocs>
    Allow from all
</Directory>

<VirtualHost *>
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
# apache1
if [ -d %{_apache1dir}/conf.d ]; then
	ln -sf %{_sysconfdir}/apache.conf %{_apache1dir}/conf.d/99_%{name}.conf
	if [ -f /var/lock/subsys/apache ]; then
		/etc/rc.d/init.d/apache restart 1>&2
	fi
fi
# apache2
if [ -d %{_apache2dir}/httpd.conf ]; then
	ln -sf %{_sysconfdir}/apache.conf %{_apache2dir}/httpd.conf/99_%{name}.conf
	if [ -f /var/lock/subsys/httpd ]; then
		/etc/rc.d/init.d/httpd restart 1>&2
	fi
fi

if [ "$1" = 1 ]; then
%banner %{name} -e <<EOF
Install the database using the appropriate "misc/database/*.sql" schema
Configure the coWiki in %{_sysconfdir}/%{name}.ini

EOF
fi

%preun
if [ "$1" = "0" ]; then
	# apache1
	if [ -f %{_apache1dir}/apache.conf ]; then
		rm -f %{_apache1dir}/conf.d/99_%{name}.conf
		if [ -f /var/lock/subsys/apache ]; then
			/etc/rc.d/init.d/apache restart 1>&2
		fi
	fi
	# apache2
	if [ -d %{_apache2dir}/httpd.conf ]; then
		rm -f %{_apache2dir}/httpd.conf/99_%{name}.conf
		if [ -f /var/lock/subsys/httpd ]; then
			/etc/rc.d/init.d/httpd restart 1>&2
		fi
	fi
fi

%files
%defattr(644,root,root,755)
%doc ChangeLog INSTALL NEWS 
%doc README.IDIOM README.PLUGIN SKEL.PLUGIN
%doc misc/database
%dir %{_sysconfdir}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/apache.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}.ini
%{_appdir}
