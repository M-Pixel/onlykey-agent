# onlykey-agent

SSH agent for the OnlyKey.

The project started from a fork [trezor-agent](https://github.com/romanz/trezor-agent) (thanks!).

## Installation

**Not published on PyPI yet.**

```
$ apt-get install python-dev libusb-1.0-0-dev libudev-dev
$ pip install Cython
$ pip install git+git://github.com/trustcrypto/python-onlykey.git
$ pip install git+git://github.com/trustcrypto/onlykey-agent.git
```

## Getting started

### Public key generation

Run:

	/tmp $ only-agent ssh.hostname.com -v > hostname.pub
	2015-09-02 15:03:18,929 INFO         getting "ssh://ssh.hostname.com" public key from Trezor...
	2015-09-02 15:03:23,342 INFO         disconnected from Trezor
	/tmp $ cat hostname.pub
	ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBGSevcDwmT+QaZPUEWUUjTeZRBICChxMKuJ7dRpBSF8+qt+8S1GBK5Zj8Xicc8SHG/SE/EXKUL2UU3kcUzE7ADQ= ssh://ssh.hostname.com

Append `hostname.pub` contents to `~/.ssh/authorized_keys`
configuration file at `ssh.hostname.com`, so the remote server
would allow you to login using the corresponding private key signature.

### Usage

Run:

	/tmp $ onlykey-agent ssh.hostname.com -v -c
	2015-09-02 15:09:39,782 INFO         getting public key from the OnlyKey...
	2015-09-02 15:09:44,430 INFO         please confirm user "thomas" login to "ssh://ssh.hostname.com" by touching a button
	2015-09-02 15:09:46,152 INFO         signature status: OK
	Linux lmde 3.16.0-4-amd64 #1 SMP Debian 3.16.7-ckt11-1+deb8u3 (2015-08-04) x86_64

	The programs included with the Debian GNU/Linux system are free software;
	the exact distribution terms for each program are described in the
	individual files in /usr/share/doc/*/copyright.

	Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
	permitted by applicable law.
	Last login: Tue Sep  1 15:57:05 2015 from localhost
	~ $
