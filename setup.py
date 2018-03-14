# -*- coding:utf-8 -*-
# created by Toons on 01/05/2017
try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup


with open("VERSION") as f1, open("readme.rst") as f2:
	VERSION = f1.read().strip()
	LONG_DESCRIPTION = f2.read()

kw = {
	"version": VERSION,
	"name": "Arky",
	"keywords": ["api", "dpos", "blockchain"],
	"author": "Toons",
	"author_email": "moustikitos@gmail.com",
	"maintainer": "Toons",
	"maintainer_email": "moustikitos@gmail.com",
	"url": "https://github.com/ArkEcosystem/arky",
	"download_url": "https://github.com/ArkEcosystem/arky/archive/aip11.zip",
	"include_package_data": True,
	"description": "Python API bridging DPOS blockchains",
	"long_description": LONG_DESCRIPTION,
	"packages": [
		"arky",
		"arky.ark",
		"arky.lisk",
		"arky.cli"
	],
	"install_requires": [
		"requests",
		"responses",
		"ecdsa",
		"pynacl",
		"pytz",
		"base58",
		"docopt",
		"ledgerblue",
	],
	"tests_require": [
		"responses",
	],
	"scripts": [
		"bin/arky-cli",
	],
	"license": "Copyright 2016-2017 Toons, Copyright 2017 ARK, MIT licence",
	"classifiers": [
		"Development Status :: 6 - Mature",
		"Environment :: Console",
		"Environment :: Web Environment",
		"Intended Audience :: Developers",
		"Intended Audience :: End Users/Desktop",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 3",
	],
}

setup(**kw)
