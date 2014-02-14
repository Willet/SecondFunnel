package { 
  'mysql-server': ensure => present;
  'libmysqlclient-dev': ensure => present;
  'git': ensure => present;
}

# Python
class python {
    package {
        "build-essential": ensure => latest;
        "python": ensure => installed;
        "python-dev": ensure => installed;
        "python-setuptools": ensure => installed;
	"libxml2-dev": ensure => installed;
        "libxslt-dev": ensure => installed;
        "libjpeg-dev": ensure => installed;
    }
    exec { "easy_install pip":
        path => "/usr/local/bin:/usr/bin:/bin",
        refreshonly => true,
        require => Package["python-setuptools"],
        subscribe => Package["python-setuptools"],
    }
     
    exec { "pip-install-req":
        command => "pip install -r /vagrant/requirements/dev.txt",
        path => "/usr/local/bin:/usr/bin:/bin",
        require => Package['git','mysql-server','libmysqlclient-dev', 'libxml2-dev', 'libxslt-dev'],
    }

    # in case we want to move pip dependencies in here
    #package {
    #    "django": ensure => "1.4.1",provider => pip;
    #    "ordereddict": ensure => "1.1",provider => pip;
    #    "fabric": ensure => "1.6.0",provider => pip;
    #}
}
class { "python": }

package { 'bundler':
    ensure   => 'installed',
    provider => 'gem',
}

exec { 'bundle install':
    command => 'bundle install',
    path => '/opt/vagrant_ruby/bin',
    cwd => '/vagrant',
    logoutput => true,
}

# Apache http://stackoverflow.com/questions/15263337/ubuntu-10-04-puppet-and-apache-apache-service-failing-to-start
package { 'apache2':
  ensure => present,	
}
service { 'apache2':
  ensure  => running,
  enable  => true,
  require => Package['apache2'],
}

# COMMON
exec { "apt-update":
    command => "/usr/bin/apt-get update"
}

Exec["apt-update"] -> Package <| |>

